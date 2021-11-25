function handleCustomSlotForWorkVideos()
    local focusedWin = hs.window.focusedWindow()
    local screen = focusedWin:screen()
    local screenFrame = screen:frame()

    function getAspectRatioHeight(width)
        return width * 9 / 16
    end

    local desiredVideoWidth = 850
    local macOSTitleBarHeight = 28
    local videoheight = getAspectRatioHeight(desiredVideoWidth) + macOSTitleBarHeight;

    local slots = {{
        x = 0,
        y = screenFrame.y,
        w = screenFrame.w - desiredVideoWidth,
        h = screenFrame.h
    }, {
        x = screenFrame.w - desiredVideoWidth,
        y = screenFrame.y,
        w = desiredVideoWidth,
        h = screenFrame.h
    }, {
        x = screenFrame.w - desiredVideoWidth,
        y = screenFrame.y,
        w = desiredVideoWidth,
        h = videoheight
    }, {
        x = screenFrame.w - desiredVideoWidth,
        y = screenFrame.y + videoheight,
        w = desiredVideoWidth,
        h = screenFrame.h - videoheight
    }, {
        x = 0,
        y = screenFrame.y,
        w = screenFrame.w - desiredVideoWidth,
        h = videoheight
    }, {
        x = 0,
        y = screenFrame.y + videoheight,
        w = screenFrame.w - desiredVideoWidth,
        h = screenFrame.h - videoheight
    }}

    local windowManagement = hs.hotkey.modal.new('cmd-alt', 'p')
    local windowManagementAlert = nil
    local idx = 1

    function windowManagement:entered()
        windowManagementAlert = hs.alert('Custom mode (Press 1/2/3/4/5/6, left/right arrows or HL to accomodate)',
            'infinite')
    end

    function windowManagement:exited()
        hs.alert.closeSpecific(windowManagementAlert)
    end

    windowManagement:bind('', 'left', function()
        idx = idx > 1 and idx - 1 or #slots
        hs.window.focusedWindow():setFrame(slots[idx])
    end)

    windowManagement:bind('', 'h', function()
        idx = idx > 1 and idx - 1 or #slots
        hs.window.focusedWindow():setFrame(slots[idx])
    end)

    windowManagement:bind('', 'right', function()
        idx = idx < #slots and idx + 1 or 1
        hs.window.focusedWindow():setFrame(slots[idx])
    end)

    windowManagement:bind('', 'l', function()
        idx = idx < #slots and idx + 1 or 1
        hs.window.focusedWindow():setFrame(slots[idx])
    end)

    windowManagement:bind('', '1', function()
        hs.window.focusedWindow():setFrame(slots[1])
    end)

    windowManagement:bind('', '2', function()
        hs.window.focusedWindow():setFrame(slots[2])
    end)

    windowManagement:bind('', '3', function()
        hs.window.focusedWindow():setFrame(slots[3])
    end)

    windowManagement:bind('', '4', function()
        hs.window.focusedWindow():setFrame(slots[4])
    end)

    windowManagement:bind('', '5', function()
        hs.window.focusedWindow():setFrame(slots[5])
    end)

    windowManagement:bind('', '6', function()
        hs.window.focusedWindow():setFrame(slots[6])
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
handleCustomSlotForWorkVideos()
hs.alert.show('Config loaded')
