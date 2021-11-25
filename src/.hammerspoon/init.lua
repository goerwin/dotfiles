function handleCustomSlotForWorkVideos()
    local focusedWin = hs.window.focusedWindow()
    local screen = focusedWin:screen()
    local screenFrame = screen:frame()

    function getAspectRatioHeight(width)
        return width * 9 / 16
    end

    local macOSTitleBarHeight = 28
    local desiredVideoWidth = 850
    local videoheight = getAspectRatioHeight(desiredVideoWidth) + macOSTitleBarHeight;

    -- _________________
    -- |       | - - - -
    -- |       |   2
    -- |   1   | - - - -
    -- |       |   3
    -- |       | - - - -
    -- |       |
    -- _________________
    local slot1 = {
        x = 0,
        y = screenFrame.y,
        w = screenFrame.w - desiredVideoWidth,
        h = screenFrame.h
    };

    local slot2 = {
        x = screenFrame.w - desiredVideoWidth,
        y = screenFrame.y,
        w = desiredVideoWidth,
        h = videoheight
    };

    local slot3 = {
        x = screenFrame.w - desiredVideoWidth,
        y = screenFrame.y + videoheight,
        w = desiredVideoWidth,
        h = videoheight
    };

    local windowManagement = hs.hotkey.modal.new('cmd-alt', 'p')
    local windowManagementAlert = nil

    function windowManagement:entered()
        windowManagementAlert = hs.alert('Custom mode (Press 1/2/3 to accomodate)', 'infinite')
    end

    function windowManagement:exited()
        hs.alert.closeSpecific(windowManagementAlert)
    end

    windowManagement:bind('', '1', function()
        hs.window.focusedWindow():setFrame(slot1)
    end)

    windowManagement:bind('', '2', function()
        hs.window.focusedWindow():setFrame(slot2)
    end)

    windowManagement:bind('', '3', function()
        hs.window.focusedWindow():setFrame(slot3)
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
