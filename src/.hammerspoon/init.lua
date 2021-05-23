-- Window management
function initWindowManagement()
  function getScreenInfo(sizeVal)
    local win = hs.window.focusedWindow()
    if not win then return false end

    local screen = win:screen()
    local fr = screen:frame()

    if sizeVal == 'max' then
      return { dimensions = { x = fr.x, y = fr.y, w = fr.w, h = fr.h }, win = win }
    elseif sizeVal == 'halfLeft' then
      return { dimensions = { x = fr.x, y = fr.y, w = fr.w/2, h = fr.h }, win = win }
    elseif sizeVal == 'halfRight' then
      return { dimensions = { x = fr.x + fr.w/2, y = fr.y, w = fr.w/2, h = fr.h }, win = win }
    end
  end

  function handleMaximize()
    local screenInfo = getScreenInfo('max')
    if screenInfo then screenInfo.win:setFrame(screenInfo.dimensions)
    end
  end

  function handleHalfLeft()
    local screenInfo = getScreenInfo('halfLeft')
    if screenInfo then screenInfo.win:setFrame(screenInfo.dimensions)
    end
  end

  function handleHalfRight()
    local screenInfo = getScreenInfo('halfRight')
    if screenInfo then screenInfo.win:setFrame(screenInfo.dimensions)
    end
  end

  local modifiers = {'cmd', 'alt'}
  hs.hotkey.bind(modifiers, 'k', handleMaximize)
  hs.hotkey.bind(modifiers, 'h', handleHalfLeft)
  hs.hotkey.bind(modifiers, 'l', handleHalfRight)
  hs.window.animationDuration = 0
end

-- Toggle mic mute
function initToggleMic()
  local inputDevice = hs.audiodevice.defaultInputDevice()
  local initialVolume = inputDevice:volume()
  local showOptions = { strokeColor = { white = 0 }, textSize = 16 }
  local screen = hs.screen.mainScreen()

  function toggleMic()
    if (inputDevice:muted()) then
      inputDevice:setMuted(false)
      hs.alert.show(1, showOptions, screen, 0.2)
    else
      inputDevice:setMuted(true)
      hs.alert.show(0, showOptions, screen, 0.2)
    end
  end

  local modifiers = {'cmd', 'ctrl', 'shift', 'alt'}
  hs.hotkey.bind(modifiers, 'x', toggleMic)
end

initWindowManagement()
hs.alert.show('Config loaded')
