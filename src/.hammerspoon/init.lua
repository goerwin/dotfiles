-- You need to install the hs ipc via:
-- https://github.com/Hammerspoon/hammerspoon/blob/master/extensions/ipc/ipc.lua#L303
-- ❯ sudo ln -s /Applications/Hammerspoon.app/Contents/Frameworks/hs/hs /usr/local/bin
-- ❯ sudo ln -s /Applications/Hammerspoon.app/Contents/Resources/man/hs.man /usr/local/share/man/man1/hs.1
require("hs.ipc")

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

function moveWindowToPreviousScreen()
  hs.window.focusedWindow():moveToScreen(
    hs.window.focusedWindow():screen():previous()
  )
end

function moveWindowToNextScreen()
  hs.window.focusedWindow():moveToScreen(
    hs.window.focusedWindow():screen():next()
  )
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

handleCustomSlotsForWindows()

hs.alert.show('Config loaded')
