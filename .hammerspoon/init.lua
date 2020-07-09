-- Helper
function stringifyTable(t, name, indent)

   local cart     -- a container
   local autoref  -- for self references

   --[[ counts the number of elements in a table
   local function tablecount(t)
      local n = 0
      for _, _ in pairs(t) do n = n+1 end
      return n
   end
   ]]
   -- (RiciLake) returns true if the table is empty
   local function isemptytable(t) return next(t) == nil end

   local function basicSerialize (o)
      local so = tostring(o)
      if type(o) == "function" then
         local info = debug.getinfo(o, "S")
         -- info.name is nil because o is not a calling level
         if info.what == "C" then
            return string.format("%q", so .. ", C function")
         else
            -- the information is defined through lines
            return string.format("%q", so .. ", defined in (" ..
                info.linedefined .. "-" .. info.lastlinedefined ..
                ")" .. info.source)
         end
      elseif type(o) == "number" or type(o) == "boolean" then
         return so
      else
         return string.format("%q", so)
      end
   end

   local function addtocart (value, name, indent, saved, field)
      indent = indent or ""
      saved = saved or {}
      field = field or name

      cart = cart .. indent .. field

      if type(value) ~= "table" then
         cart = cart .. " = " .. basicSerialize(value) .. ";\n"
      else
         if saved[value] then
            cart = cart .. " = {}; -- " .. saved[value]
                        .. " (self reference)\n"
            autoref = autoref ..  name .. " = " .. saved[value] .. ";\n"
         else
            saved[value] = name
            --if tablecount(value) == 0 then
            if isemptytable(value) then
               cart = cart .. " = {};\n"
            else
               cart = cart .. " = {\n"
               for k, v in pairs(value) do
                  k = basicSerialize(k)
                  local fname = string.format("%s[%s]", name, k)
                  field = string.format("[%s]", k)
                  -- three spaces between levels
                  addtocart(v, fname, indent .. "   ", saved, field)
               end
               cart = cart .. indent .. "};\n"
            end
         end
      end
   end

   name = name or "__unnamed__"
   if type(t) ~= "table" then
      return name .. " = " .. basicSerialize(t)
   end
   cart, autoref = "", ""
   addtocart(t, name, indent)
   return cart .. autoref
end

-- WINDOW MANAGEMENT
function initWindowManagement()
  local windowManagement = hs.hotkey.modal.new('cmd-ctrl-shift-alt', 'w')
  local windowManagementAlert = nil

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
    else hs.alert.show('No active window')
    end
  end

  function handleHalfLeft()
    local screenInfo = getScreenInfo('halfLeft')
    if screenInfo then screenInfo.win:setFrame(screenInfo.dimensions)
    else hs.alert.show('No active window')
    end
  end

  function handleHalfRight()
    local screenInfo = getScreenInfo('halfRight')
    if screenInfo then screenInfo.win:setFrame(screenInfo.dimensions)
    else hs.alert.show('No active window')
    end
  end

  function handleMovePrevNextScreen(isNextScreen)
    local win = hs.window.focusedWindow()
    if not win then return false end

    local toScreen
    if isNextScreen then toScreen = win:screen():next()
    else toScreen = win:screen():previous()
    end

    local fr = toScreen:frame()
    win:setFrame({ x = fr.x, y = fr.y, w = fr.w, h = fr.h })
  end

  function windowManagement:entered()
    windowManagementAlert = hs.alert('Window mode', 'infinite')
  end

  function windowManagement:exited()
    hs.alert.closeSpecific(windowManagementAlert)
  end

  windowManagement:bind('', 'm', handleMaximize)
  windowManagement:bind('', 'q', handleHalfLeft)
  windowManagement:bind('', 'w', handleHalfRight)
  windowManagement:bind('', 'j', function() handleMovePrevNextScreen(true) end)
  windowManagement:bind('', 'k', handleMovePrevNextScreen)
  windowManagement:bind('', 'escape', function() windowManagement:exit() end)

  hs.window.animationDuration = 0
end

-- OPEN APPS
function initOpenApps()
  local hyper = {'cmd', 'ctrl'}

  function factoryLaunchApp(name)
    return function() hs.application.launchOrFocus(name) end
  end

  hs.hotkey.bind(hyper, 'e', factoryLaunchApp('/Applications/Sublime Text.app'))
  hs.hotkey.bind(hyper, 'w', factoryLaunchApp('Google Chrome'))
  hs.hotkey.bind(hyper, 'c', factoryLaunchApp('iTerm'))
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

  local hyper = {'cmd', 'ctrl', 'shift', 'alt'}
  hs.hotkey.bind(hyper, 'x', toggleMic)
end

initWindowManagement()
initToggleMic()
hs.alert.show('Config loaded')
