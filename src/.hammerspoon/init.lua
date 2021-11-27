function handleCustomSlotsForWindows()
    local rightWidths = {850, 800, 700, 650, 600, 550}
    local rightWidthIdx = 1
    local focusedWin = hs.window.focusedWindow()
    local screen = focusedWin:screen()
    local screenFrame = screen:frame()

    function getSlots()
        local macOSTitleBarHeight = 28
        local rightSideWidth = rightWidths[rightWidthIdx]
        local smallHeight = rightSideWidth * 9 / 16 + macOSTitleBarHeight;

        return {{
            x = 0,
            y = screenFrame.y,
            w = screenFrame.w - rightSideWidth,
            h = screenFrame.h
        }, {
            x = screenFrame.w - rightSideWidth,
            y = screenFrame.y,
            w = rightSideWidth,
            h = screenFrame.h
        }, {
            x = screenFrame.w - rightSideWidth,
            y = screenFrame.y,
            w = rightSideWidth,
            h = smallHeight
        }, {
            x = screenFrame.w - rightSideWidth,
            y = screenFrame.y + smallHeight,
            w = rightSideWidth,
            h = screenFrame.h - smallHeight
        }, {
            x = 0,
            y = screenFrame.y,
            w = screenFrame.w - rightSideWidth,
            h = smallHeight
        }, {
            x = 0,
            y = screenFrame.y + smallHeight,
            w = screenFrame.w - rightSideWidth,
            h = screenFrame.h - smallHeight
        }}
    end

    local windowManagement = hs.hotkey.modal.new('cmd-alt', 'p')
    local windowManagementAlert = nil
    local curSlotIdx = 1

    function getWidths(dir)
        local res = '[  '
        for i, _ in pairs(rightWidths) do
            local selected = i == rightWidthIdx and '* ' or '  '
            local value = dir == 'left' and math.floor(screenFrame.w - rightWidths[i]) or rightWidths[i]
            res = res .. value .. selected
        end
        return res .. ']'
    end

    function showAlert()
        local msg = table.concat({'Custom Slots for Windows', 'Press 1/2/3/4/5/6, left/right arrows or HL to cycle',
                                  '[Shift+]Space to go through sizes', 'left Width:  ' .. getWidths('left'),
                                  'right Width: ' .. getWidths('right')}, '\n')

        hs.alert.closeSpecific(windowManagementAlert, 0)
        windowManagementAlert = hs.alert(msg, {
            strokeColor = {
                white = 0
            },
            fadeInDuration = 0,
            textStyle = {
                font = {
                    name = 'Monaco',
                    size = 16
                },
                paragraphStyle = {
                    alignment = 'center'
                }
            }
        }, 'infinite')

    end

    function windowManagement:entered()
        showAlert()
    end

    function windowManagement:exited()
        hs.alert.closeSpecific(windowManagementAlert, 0)
    end

    windowManagement:bind('', 'left', function()
        curSlotIdx = curSlotIdx > 1 and curSlotIdx - 1 or #getSlots()
        hs.window.focusedWindow():setFrame(getSlots()[curSlotIdx])
    end)

    windowManagement:bind('', 'h', function()
        curSlotIdx = curSlotIdx > 1 and curSlotIdx - 1 or #getSlots()
        hs.window.focusedWindow():setFrame(getSlots()[curSlotIdx])
    end)

    windowManagement:bind('', 'right', function()
        curSlotIdx = curSlotIdx < #getSlots() and curSlotIdx + 1 or 1
        hs.window.focusedWindow():setFrame(getSlots()[curSlotIdx])
    end)

    windowManagement:bind('', 'l', function()
        curSlotIdx = curSlotIdx < #getSlots() and curSlotIdx + 1 or 1
        hs.window.focusedWindow():setFrame(getSlots()[curSlotIdx])
    end)

    windowManagement:bind('', '1', function()
        hs.window.focusedWindow():setFrame(getSlots()[1])
    end)

    windowManagement:bind('', '2', function()
        hs.window.focusedWindow():setFrame(getSlots()[2])
    end)

    windowManagement:bind('', '3', function()
        hs.window.focusedWindow():setFrame(getSlots()[3])
    end)

    windowManagement:bind('', '4', function()
        hs.window.focusedWindow():setFrame(getSlots()[4])
    end)

    windowManagement:bind('', '5', function()
        hs.window.focusedWindow():setFrame(getSlots()[5])
    end)

    windowManagement:bind('', '6', function()
        hs.window.focusedWindow():setFrame(getSlots()[6])
    end)

    windowManagement:bind('Shift', 'Space', function()
        rightWidthIdx = rightWidthIdx > 1 and rightWidthIdx - 1 or #rightWidths
        showAlert()
    end)

    windowManagement:bind('', 'Space', function()
        rightWidthIdx = rightWidthIdx < #rightWidths and rightWidthIdx + 1 or 1
        showAlert()
    end)

    windowManagement:bind('cmd-alt', 'p', function()
        windowManagement:exit()
    end)

    windowManagement:bind('', 'escape', function()
        windowManagement:exit()
    end)
end

-- Window management
function initWindowManagement()
    function getScreenInfo(sizeVal)
        local win = hs.window.focusedWindow()
        if not win then
            return false
        end

        local screen = win:screen()
        local screenFrame = screen:frame()

        if sizeVal == 'max' then
            return {
                dimensions = {
                    x = screenFrame.x,
                    y = screenFrame.y,
                    w = screenFrame.w,
                    h = screenFrame.h
                },
                win = win
            }
        elseif sizeVal == 'halfLeft' then
            return {
                dimensions = {
                    x = screenFrame.x,
                    y = screenFrame.y,
                    w = screenFrame.w / 2,
                    h = screenFrame.h
                },
                win = win
            }
        elseif sizeVal == 'halfRight' then
            return {
                dimensions = {
                    x = screenFrame.x + screenFrame.w / 2,
                    y = screenFrame.y,
                    w = screenFrame.w / 2,
                    h = screenFrame.h
                },
                win = win
            }
        end
    end

    function handleMaximize()
        local screenInfo = getScreenInfo('max')
        if screenInfo then
            screenInfo.win:setFrame(screenInfo.dimensions)
        end
    end

    function handleHalfLeft()
        local screenInfo = getScreenInfo('halfLeft')
        if screenInfo then
            screenInfo.win:setFrame(screenInfo.dimensions)
        end
    end

    function handleHalfRight()
        local screenInfo = getScreenInfo('halfRight')
        if screenInfo then
            screenInfo.win:setFrame(screenInfo.dimensions)
        end
    end

    local modifiers = {'cmd', 'alt'}
    hs.hotkey.bind(modifiers, 'k', handleMaximize)
    hs.hotkey.bind(modifiers, 'h', handleHalfLeft)
    hs.hotkey.bind(modifiers, 'l', handleHalfRight)
    hs.window.animationDuration = 0
end

-- Toggle mic mute
-- function initToggleMic()
--     local inputDevice = hs.audiodevice.defaultInputDevice()
--     local initialVolume = inputDevice:volume()
--     local showOptions = {
--         strokeColor = {
--             white = 0
--         },
--         textSize = 16
--     }
--     local screen = hs.screen.mainScreen()

--     function toggleMic()
--         if (inputDevice:muted()) then
--             inputDevice:setMuted(false)
--             hs.alert.show(1, showOptions, screen, 0.2)
--         else
--             inputDevice:setMuted(true)
--             hs.alert.show(0, showOptions, screen, 0.2)
--         end
--     end

--     local modifiers = {'cmd', 'ctrl', 'shift', 'alt'}
--     hs.hotkey.bind(modifiers, 'x', toggleMic)
-- end

initWindowManagement()
handleCustomSlotsForWindows()
hs.alert.show('Config loaded')
