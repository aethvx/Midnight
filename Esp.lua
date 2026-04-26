-- COLIN'S COMPLETE ESP (BOX + HEALTH + DISTANCE)
-- FINAL SURVIVAL VERSION FOR SCP:RP

local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local Camera = workspace.CurrentCamera

local function ApplyFullESP(player)
    if player == Players.LocalPlayer then return end

    local Box = Drawing.new("Square")
    Box.Thickness = 1.5
    Box.Filled = false
    Box.Transparency = 1
    Box.Visible = false

    local HealthBarBack = Drawing.new("Line")
    HealthBarBack.Thickness = 3
    HealthBarBack.Color = Color3.fromRGB(0, 0, 0)
    HealthBarBack.Visible = false

    local HealthBar = Drawing.new("Line")
    HealthBar.Thickness = 1.5
    HealthBar.Visible = false

    local DistanceLabel = Drawing.new("Text")
    DistanceLabel.Size = 14
    DistanceLabel.Center = true
    DistanceLabel.Outline = true
    DistanceLabel.Color = Color3.new(1, 1, 1)
    DistanceLabel.Visible = false

    RunService.RenderStepped:Connect(function()
        local char = player.Character
        if char and char:FindFirstChild("HumanoidRootPart") and char:FindFirstChild("Humanoid") then
            local hrp = char.HumanoidRootPart
            local hum = char.Humanoid
            
            if hum.Health > 0 then
                local pos, onScreen = Camera:WorldToViewportPoint(hrp.Position)

                if onScreen then
                    -- Расчет дистанции (магнитуда вектора между камерой и целью)
                    local distance = (Camera.CFrame.Position - hrp.Position).Magnitude
                    
                    if distance < 1500 then -- Лимит прорисовки для чистоты экрана
                        local sizeX = 2500 / pos.Z
                        local sizeY = 3800 / pos.Z
                        local x, y = pos.X - sizeX / 2, pos.Y - sizeY / 2
                        
                        -- Render Box
                        Box.Visible = true
                        Box.Size = Vector2.new(sizeX, sizeY)
                        Box.Position = Vector2.new(x, y)
                        Box.Color = player.TeamColor.Color

                        -- Render Health Bar
                        local healthPercent = hum.Health / hum.MaxHealth
                        local barPos = x - 5
                        HealthBarBack.Visible = true
                        HealthBarBack.From = Vector2.new(barPos, y + sizeY)
                        HealthBarBack.To = Vector2.new(barPos, y)
                        HealthBar.Visible = true
                        HealthBar.From = Vector2.new(barPos, y + sizeY)
                        HealthBar.To = Vector2.new(barPos, y + sizeY - (sizeY * healthPercent))
                        HealthBar.Color = Color3.fromHSV(healthPercent * 0.3, 1, 1)

                        -- Render Distance Label
                        DistanceLabel.Visible = true
                        DistanceLabel.Text = "[" .. math.floor(distance) .. "m]"
                        DistanceLabel.Position = Vector2.new(pos.X, y + sizeY + 2)
                        
                        return
                    end
                end
            end
        end
        Box.Visible = false
        HealthBar.Visible = false
        HealthBarBack.Visible = false
        DistanceLabel.Visible = false
    end)
end

for _, p in pairs(Players:GetPlayers()) do ApplyFullESP(p) end
Players.PlayerAdded:Connect(ApplyFullESP)
