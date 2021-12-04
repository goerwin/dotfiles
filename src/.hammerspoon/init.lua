-- if t2 contains t1 (regardless of extra keys) then it is considered equal
function deepCompare(t1, t2)
    local ty1 = type(t1)
    local ty2 = type(t2)

    if ty1 ~= ty2 then
        return false
    end

    -- non-table types can be directly compared
    if ty1 ~= 'table' and ty2 ~= 'table' then
        return t1 == t2
    end

    if ty1 ~= 'table' or ty2 ~= 'table' then
        return false
    end

    for k1, v1 in pairs(t1) do
        local v2 = t2[k1]
        if v2 == nil or not deepCompare(v1, v2) then
            return false
        end
    end

    return true
end

function findIndex(table, valueToSearch)
    for i, v in pairs(table) do
        if deepCompare(v, valueToSearch) then
            return i
        end
    end

    return nil
end

function getWindowFrames(screenFrame)
    local halfWidthLeft = math.floor(screenFrame.w / 2)
    local halfWidthRight = halfWidthLeft + screenFrame.w % 2
    local halfHeightTop = math.floor(screenFrame.h / 2)
    local halfHeightBottom = halfHeightTop + screenFrame.h % 2

    return {
        maximized = {
            x = screenFrame.x,
            y = screenFrame.y,
            w = screenFrame.w,
            h = screenFrame.h
        },
        halfLeft = {
            x = screenFrame.x,
            y = screenFrame.y,
            w = halfWidthLeft,
            h = screenFrame.h
        },
        topHalfLeft = {
            x = screenFrame.x,
            y = screenFrame.y,
            w = halfWidthLeft,
            h = halfHeightTop
        },
        bottomHalfLeft = {
            x = screenFrame.x,
            y = screenFrame.y + halfHeightTop,
            w = halfWidthLeft,
            h = halfHeightBottom
        },
        halfRight = {
            x = screenFrame.x + halfWidthLeft,
            y = screenFrame.y,
            w = halfWidthRight,
            h = screenFrame.h
        },
        topHalfRight = {
            x = screenFrame.x + halfWidthLeft,
            y = screenFrame.y,
            w = halfWidthRight,
            h = halfHeightTop
        },
        bottomHalfRight = {
            x = screenFrame.x + halfWidthLeft,
            y = screenFrame.y + halfHeightTop,
            w = halfWidthRight,
            h = halfHeightBottom
        }
    }
end

function getCurrentWindowInfo()
    local window = hs.window.focusedWindow()
    if not window then
        return false
    end

    local screen = window:screen()
    local screenFrame = screen:frame()
    local windowFrame = window:frame()

    return {
        windowFrame = windowFrame,
        screenFrame = screenFrame,
        window = window
    }
end

function setNewWindowFrame(newWinIdx, direction, newWinIdxMaps)
    local currentWindowInfo = getCurrentWindowInfo()

    if not currentWindowInfo then
        return
    end

    local window = currentWindowInfo.window
    local windowFrame = currentWindowInfo.windowFrame
    local screenFrame = currentWindowInfo.screenFrame

    local windowFrames = getWindowFrames(screenFrame)

    if not newWinIdxMaps then
        newWinIdxMaps = {
            maximized = 'halfLeft',
            halfLeft = 'halfRight',
            halfRight = 'topHalfLeft',
            topHalfLeft = 'bottomHalfLeft',
            bottomHalfLeft = 'topHalfRight',
            topHalfRight = 'bottomHalfRight',
            bottomHalfRight = 'maximized'
        }
    end

    if (direction) then
        local winIdx = findIndex(windowFrames, windowFrame)
        newWinIdx = winIdx and direction == 'next' and newWinIdxMaps[winIdx] or findIndex(newWinIdxMaps, winIdx) or
                        newWinIdx
    end

    hs.window.animationDuration = 0
    return window:setFrame(windowFrames[newWinIdx])
end

function handleCustomSlotsForWindows()
    local rightWidths = {850, 800, 700, 650, 600, 550}
    local rightWidthIdx = 1

    function getSlots()
        local focusedWin = hs.window.focusedWindow()
        local screen = focusedWin:screen()
        local screenFrame = screen:frame()
        local macOSTitleBarHeight = 28
        local rightSideWidth = rightWidths[rightWidthIdx]
        local smallHeight = math.floor(rightSideWidth * 9 / 16 + macOSTitleBarHeight);

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
        local focusedWin = hs.window.focusedWindow()
        local screen = focusedWin:screen()
        local screenFrame = screen:frame()
        local res = '[  '
        for i, _ in pairs(rightWidths) do
            local selected = i == rightWidthIdx and '* ' or '  '
            local value = dir == 'left' and math.floor(screenFrame.w - rightWidths[i]) or rightWidths[i]
            res = res .. value .. selected
        end
        return res .. ']'
    end

    function showAlert()
        local msg = table.concat({'Press 1/2/3/4/5/6, left/right arrows or HL to cycle through custom sizes',
                                  'Press [Shift+]Enter to cycle through predefined sizes',
                                  '[Shift+]Space to set custom sizes', 'left Width:  ' .. getWidths('left'),
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

    windowManagement:bind('Shift', 'Return', function()
        setNewWindowFrame('maximized', 'prev')
    end)

    windowManagement:bind('', 'Return', function()
        setNewWindowFrame('maximized', 'next')
    end)

    windowManagement:bind('cmd-alt', 'p', function()
        windowManagement:exit()
    end)

    windowManagement:bind('', 'escape', function()
        windowManagement:exit()
    end)
end

function handleBecausekarabinerisdead()
    local types = hs.eventtap.event.types
    hs.hotkey.bind({'alt'}, 'c', function()
        local mousePos = hs.mouse.absolutePosition()
        hs.eventtap.event.newMouseEvent(types.leftMouseDown, mousePos):post()
    end, function()
        local mousePos = hs.mouse.absolutePosition()
        hs.eventtap.event.newMouseEvent(types.leftMouseUp, mousePos):post()
    end)

    hs.hotkey.bind({'cmd'}, 'j', function()
        hs.eventtap.keyStroke({}, 'pageDown')
    end, nil, function()
        hs.eventtap.keyStroke({}, 'pageDown')
    end)

    hs.hotkey.bind({'cmd'}, 'k', function()
        hs.eventtap.keyStroke({}, 'pageUp')
    end, nil, function()
        hs.eventtap.keyStroke({}, 'pageUp')
    end)

    -- Why do I need to do this
    local chromeCmdAltF
    chromeCmdAltF = hs.hotkey.bind({'cmd+alt'}, 'f', function()
        chromeCmdAltF:disable()
        hs.eventtap.keyStroke({'cmd+ctrl'}, 'f')
        chromeCmdAltF:enable()
    end)

    local cmdShiftJ = hs.hotkey.bind({'cmd+shift'}, 'j', function()
        hs.eventtap.keyStroke({'shift'}, 'pageDown')
    end)

    local cmdShiftK = hs.hotkey.bind({'cmd+shift'}, 'k', function()
        hs.eventtap.keyStroke({'shift'}, 'pageUp')
    end)

    local chromeCmdH = hs.hotkey.new({'cmd'}, 'h', function()
        hs.eventtap.keyStroke({'cmd'}, '5')
    end)

    local chromeCmdL = hs.hotkey.new({'cmd'}, 'l', function()
        hs.eventtap.keyStroke({'cmd'}, '6')
    end)

    local cmdSemicolon = hs.hotkey.new({'cmd'}, ';', function()
        chromeCmdL:disable()
        hs.eventtap.keyStroke({'cmd'}, 'l')
        chromeCmdL:enable()
    end)

    local chromeLeft = hs.hotkey.new({}, 'left', function()
        hs.eventtap.keyStroke({'cmd'}, '5')
    end)

    local chromeRight = hs.hotkey.new({}, 'right', function()
        hs.eventtap.keyStroke({'cmd'}, '6')
    end)

    local chromeUp = hs.hotkey.new({}, 'up', function()
        hs.eventtap.keyStroke({'alt'}, 's')
    end)

    local chromeDown = hs.hotkey.new({}, 'down', function()
        hs.eventtap.keyStroke({'alt'}, 't')
    end)

    local chromeCmdShiftI
    chromeCmdShiftI = hs.hotkey.new({'cmd+shift'}, 'i', function()
        chromeCmdShiftI:disable()
        hs.eventtap.keyStroke({'cmd+alt'}, 'i', 1000)
        chromeCmdShiftI:enable()
    end)

    local wf = hs.window.filter
    local googleChromeWindow = wf.new("Google Chrome")
    googleChromeWindow:subscribe(wf.windowFocused, function()
        chromeCmdH:enable()
        chromeCmdL:enable()
        chromeLeft:enable()
        chromeRight:enable()
        chromeUp:enable()
        chromeDown:enable()
        cmdSemicolon:enable()
        chromeCmdShiftI:enable()

    end):subscribe(wf.windowUnfocused, function()
        chromeCmdH:disable()
        chromeCmdL:disable()
        chromeLeft:disable()
        chromeRight:disable()
        chromeUp:disable()
        chromeDown:disable()
        cmdSemicolon:disable()
        chromeCmdShiftI:disable()
    end)

    hs.hotkey.bind({'alt'}, '1', function()
        hs.alert.show('mode 1')
        chromeLeft:disable()
        chromeRight:disable()
        chromeUp:disable()
        chromeDown:disable()
    end)

    hs.hotkey.bind({'alt'}, '2', function()
        hs.alert.show('mode 2')
        chromeLeft:enable()
        chromeRight:enable()
        chromeUp:enable()
        chromeDown:enable()
    end)

    -- Mute mic
    hs.hotkey.bind({'alt'}, 'm', function()
        hs.eventtap.keyStroke({'cmd+alt'}, 'm')
    end)
end

-- Window management
function initWindowManagement()
    hs.hotkey.bind({'cmd', 'alt'}, 'k', function()
        setNewWindowFrame('maximized')
    end)

    hs.hotkey.bind({'cmd', 'alt'}, 'h', function()
        setNewWindowFrame('halfLeft', 'next', {
            halfLeft = 'topHalfLeft',
            topHalfLeft = 'bottomHalfLeft',
            bottomHalfLeft = 'halfLeft'
        })

    end)

    hs.hotkey.bind({'cmd', 'alt'}, 'l', function()
        setNewWindowFrame('halfRight', 'next', {
            halfRight = 'topHalfRight',
            topHalfRight = 'bottomHalfRight',
            bottomHalfRight = 'halfRight'
        })
    end)
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
handleBecausekarabinerisdead()

hs.alert.show('Config loaded')
