from pathlib import Path
import os
import tkinter as tk
from tkinter import messagebox, ttk

from dotenv import load_dotenv

from phone_bot.database import Database, REGULAR, REPLACEMENT


class QueueManager:
    def __init__(self, root: tk.Tk, database: Database) -> None:
        self.root = root
        self.database = database
        root.title("Очереди номеров")
        root.geometry("820x620")
        root.minsize(700, 500)

        self.stats = ttk.Label(root, font=("Segoe UI", 11, "bold"))
        self.stats.pack(anchor="w", padx=12, pady=(12, 6))

        ttk.Label(root, text="Вставь номера — каждый с новой строки:").pack(
            anchor="w", padx=12
        )
        self.input = tk.Text(root, height=7, font=("Consolas", 11))
        self.input.pack(fill="x", padx=12, pady=6)

        add_buttons = ttk.Frame(root)
        add_buttons.pack(fill="x", padx=12, pady=(0, 10))
        ttk.Button(
            add_buttons,
            text="Добавить обычные",
            command=lambda: self.add(REGULAR),
        ).pack(side="left", padx=(0, 8))
        ttk.Button(
            add_buttons,
            text="Добавить на перестановку",
            command=lambda: self.add(REPLACEMENT),
        ).pack(side="left")
        ttk.Button(add_buttons, text="Обновить", command=self.refresh).pack(
            side="right"
        )

        queues = ttk.Frame(root)
        queues.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        queues.columnconfigure(0, weight=1)
        queues.columnconfigure(1, weight=1)
        queues.rowconfigure(0, weight=1)

        self.regular_tree = self.create_queue(queues, "Обычные", REGULAR, column=0)
        self.replacement_tree = self.create_queue(
            queues, "На перестановку — выдаются первыми", REPLACEMENT, column=1
        )
        self.refresh()

    def create_queue(
        self,
        parent: ttk.Frame,
        title: str,
        queue_type: str,
        column: int,
    ) -> ttk.Treeview:
        frame = ttk.LabelFrame(parent, text=title, padding=8)
        frame.grid(
            row=0,
            column=column,
            sticky="nsew",
            padx=(0, 6) if column == 0 else (6, 0),
        )
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

        tree = ttk.Treeview(frame, columns=("phone",), show="headings")
        tree.heading("phone", text="Номер")
        tree.column("phone", anchor="w")
        tree.grid(row=0, column=0, columnspan=2, sticky="nsew")

        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        scrollbar.grid(row=0, column=2, sticky="ns")
        tree.configure(yscrollcommand=scrollbar.set)

        ttk.Button(
            frame,
            text="Удалить",
            command=lambda: self.remove_selected(tree),
        ).grid(row=1, column=0, sticky="ew", pady=(8, 0), padx=(0, 4))
        target = REPLACEMENT if queue_type == REGULAR else REGULAR
        move_text = "→ Перестановка" if target == REPLACEMENT else "→ Обычные"
        ttk.Button(
            frame,
            text=move_text,
            command=lambda: self.move_selected(tree, target),
        ).grid(row=1, column=1, sticky="ew", pady=(8, 0), padx=(4, 0))
        return tree

    def add(self, queue_type: str) -> None:
        lines = self.input.get("1.0", "end").splitlines()
        result = self.database.add_phones(lines, queue_type)
        if not any(line.strip() for line in lines):
            messagebox.showwarning("Нет номеров", "Сначала вставь номера в поле.")
            return

        details = [f"Добавлено: {result.added}"]
        if result.duplicates:
            details.append(f"Дубликаты: {result.duplicates}")
        if result.invalid:
            details.append("Не распознаны: " + ", ".join(result.invalid[:5]))
        messagebox.showinfo("Готово", "\n".join(details))
        self.input.delete("1.0", "end")
        self.refresh()

    def selected_id(self, tree: ttk.Treeview) -> int | None:
        selected = tree.selection()
        return int(selected[0]) if selected else None

    def remove_selected(self, tree: ttk.Treeview) -> None:
        phone_id = self.selected_id(tree)
        if phone_id is None:
            messagebox.showwarning("Не выбран номер", "Выбери номер в таблице.")
            return
        if messagebox.askyesno("Удаление", "Удалить выбранный номер из очереди?"):
            self.database.remove_phone(phone_id)
            self.refresh()

    def move_selected(self, tree: ttk.Treeview, target: str) -> None:
        phone_id = self.selected_id(tree)
        if phone_id is None:
            messagebox.showwarning("Не выбран номер", "Выбери номер в таблице.")
            return
        self.database.move_phone(phone_id, target)
        self.refresh()

    def refresh(self) -> None:
        counts = self.database.counts()
        self.stats.configure(
            text=(
                f"Обычные: {counts[REGULAR]}    "
                f"На перестановку: {counts[REPLACEMENT]}    "
                f"Выдано: {self.database.total_issued()}"
            )
        )
        for tree, queue_type in (
            (self.regular_tree, REGULAR),
            (self.replacement_tree, REPLACEMENT),
        ):
            tree.delete(*tree.get_children())
            for item in self.database.list_queue(queue_type):
                tree.insert("", "end", iid=str(item.id), values=(item.phone,))


def main() -> None:
    project_dir = Path(__file__).resolve().parent
    load_dotenv(project_dir / ".env")
    database = Database(project_dir / os.getenv("DATABASE_PATH", "data/phones.db"))
    database.initialize()
    root = tk.Tk()
    QueueManager(root, database)
    root.mainloop()


if __name__ == "__main__":
    main()
