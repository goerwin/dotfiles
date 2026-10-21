# Shared macOS install step for the daylier, mic-muter and key-remapper apps.
# The caller builds the app (each project has its own build specifics) and sets:
#   MAC_APP_NAME      process and display name, e.g. "Mic Muter"
#   MAC_SOURCE_APP    path of the freshly built "$MAC_APP_NAME.app"
# Optional:
#   MAC_INSTALL_DIR   default /Applications
#   MAC_QUIT_PATTERNS space-separated pgrep -f patterns that must be dead before
#                     replacing anything besides the app itself (e.g. daemon)
# Installs without keeping a backup: the new app is staged inside the install
# dir and verified, a running instance (if any) is quit, the old copy is removed
# and the new one takes its place. Relaunches only when the app (or one of the
# listed extra processes) was running before the install.

# Returns 0 when the app and all extra quit patterns are gone.
mac_processes_dead() {
  pgrep -xq "$MAC_APP_NAME" && return 1
  local pat
  for pat in ${=MAC_QUIT_PATTERNS:-}; do
    pgrep -f "$pat" >/dev/null 2>&1 && return 1
  done
  return 0
}

mac_install_app() {
  : "${MAC_APP_NAME:?MAC_APP_NAME must be set}"
  : "${MAC_SOURCE_APP:?MAC_SOURCE_APP must be set}"
  MAC_INSTALL_DIR="${MAC_INSTALL_DIR:-/Applications}"

  local target="$MAC_INSTALL_DIR/$MAC_APP_NAME.app"
  if [[ ! -d "$MAC_SOURCE_APP" ]]; then
    print -u2 -- "The build did not produce an app at: $MAC_SOURCE_APP"
    return 1
  fi

  local bundleId version installedId
  bundleId=$(/usr/libexec/PlistBuddy -c "Print :CFBundleIdentifier" "$MAC_SOURCE_APP/Contents/Info.plist" 2>/dev/null) || true
  version=$(/usr/libexec/PlistBuddy -c "Print :CFBundleShortVersionString" "$MAC_SOURCE_APP/Contents/Info.plist" 2>/dev/null) || true

  if [[ -e "$target" || -L "$target" ]]; then
    installedId=$(/usr/libexec/PlistBuddy -c "Print :CFBundleIdentifier" "$target/Contents/Info.plist" 2>/dev/null) || true
    if [[ -L "$target" || "$installedId" != "$bundleId" ]]; then
      print -u2 -- "Refusing to replace an unrelated app at: $target"
      return 1
    fi
  fi

  if [[ -n "$version" ]]; then
    print -- "Installing $MAC_APP_NAME $version to $target"
  else
    print -- "Installing $MAC_APP_NAME to $target"
  fi

  local -a sudoCommand=()
  if [[ ! -w "$MAC_INSTALL_DIR" || ( -e "$target" && ! -w "$target" ) ]]; then
    sudo -v
    sudoCommand=(sudo)
  fi

  local wasRunning=0
  pgrep -xq "$MAC_APP_NAME" && wasRunning=1
  local pat
  for pat in ${=MAC_QUIT_PATTERNS:-}; do
    pgrep -f "$pat" >/dev/null 2>&1 && wasRunning=1
  done

  # Stage the new app next to its destination, signatures verified before the
  # installed copy is touched.
  local stagingDir="$MAC_INSTALL_DIR/.${MAC_APP_NAME}-install.$$.app"
  discardStaging() { rm -rf "$stagingDir" 2>/dev/null || true; }
  if ! "${sudoCommand[@]}" ditto "$MAC_SOURCE_APP" "$stagingDir"; then
    discardStaging
    return 1
  fi
  if ! codesign --verify --deep --strict "$stagingDir"; then
    print -u2 -- "The staged app failed signature verification; installed copy untouched."
    discardStaging
    return 1
  fi

  if (( wasRunning )); then
    print -- "Quitting running $MAC_APP_NAME..."
    if [[ -n "$bundleId" ]]; then
      osascript -e "tell application id \"$bundleId\" to quit" >/dev/null 2>&1 || true
    fi
    local i
    for i in {1..25}; do
      mac_processes_dead && break
      sleep 0.2
    done
    if ! mac_processes_dead; then
      killall "$MAC_APP_NAME" >/dev/null 2>&1 || true
      for pat in ${=MAC_QUIT_PATTERNS:-}; do
        pkill -f "$pat" >/dev/null 2>&1 || true
      done
      sleep 0.2
      killall -9 "$MAC_APP_NAME" >/dev/null 2>&1 || true
      for pat in ${=MAC_QUIT_PATTERNS:-}; do
        pkill -9 -f "$pat" >/dev/null 2>&1 || true
      done
      sleep 0.2
      if ! mac_processes_dead; then
        print -u2 -- "$MAC_APP_NAME didn't quit; the installed copy was left untouched."
        discardStaging
        return 1
      fi
    fi
  fi

  if ! "${sudoCommand[@]}" rm -rf "$target"; then
    discardStaging
    return 1
  fi
  if ! "${sudoCommand[@]}" mv "$stagingDir" "$target"; then
    discardStaging
    return 1
  fi
  discardStaging

  if (( wasRunning )); then
    print -- "Re-launching $MAC_APP_NAME..."
    open "$target"
    print -- "Launched $MAC_APP_NAME."
  else
    print -- "$MAC_APP_NAME wasn't running before the install; left closed."
  fi
}
