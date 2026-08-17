from getpass import getpass
from pathlib import Path
import os
import shutil

from dotenv import load_dotenv, set_key


def main() -> None:
    project_dir = Path(__file__).resolve().parent
    env_path = project_dir / ".env"
    if not env_path.exists():
        shutil.copyfile(project_dir / ".env.example", env_path)

    load_dotenv(env_path)
    current_api_id = os.getenv("API_ID", "").strip()
    if current_api_id == "12345678":
        current_api_id = ""
    current_api_hash = os.getenv("API_HASH", "").strip()

    api_id = (
        input(f"API_ID{' [already set]' if current_api_id else ''}: ").strip()
        or current_api_id
    )
    api_hash = (
        getpass(
            f"API_HASH{' [already set; Enter keeps it]' if current_api_hash and 'replace_with' not in current_api_hash else ''}: "
        ).strip()
        or current_api_hash
    )

    try:
        int(api_id)
    except ValueError as error:
        raise ValueError("API_ID должен состоять только из цифр") from error
    if not api_hash or "replace_with" in api_hash:
        raise ValueError("API_HASH не заполнен")

    set_key(env_path, "API_ID", api_id, quote_mode="never")
    set_key(env_path, "API_HASH", api_hash, quote_mode="never")
    print(f"\nНастройки сохранены в {env_path}")
    print("API_HASH не был показан на экране. Теперь запусти discover_ids.bat.")


if __name__ == "__main__":
    main()
