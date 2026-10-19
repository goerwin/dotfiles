# Shared build and install flow for the personal-team iOS apps
# (financer, noter, daylier) and for the preflight in dotfiles' install-apps.zsh.
#
# Consumers set, before calling ios_install_app:
#   APP_NAME        app name (also the .xcodeproj name), e.g. Financer
#   PROJECT_ROOT    directory that contains "$APP_NAME.xcodeproj"
# Optional overrides:
#   SCHEME            default "$APP_NAME Release"
#   CONFIGURATION     default Release
#   DERIVED_DATA_DIR  default "$PROJECT_ROOT/.build/DerivedData"
#   IOS_SET_PROFILE_EXPIRATION=1
#                     additionally passes BUILD_TIMESTAMP and
#                     PROVISIONING_PROFILE_EXPIRATION_DATE as build settings
#                     (for apps that show the profile expiry inside the app)
# The device UDID must come from IOS_DEVICE_UDID in the environment; installs
# are always tied to the explicitly chosen device.
#
# The location of this repo is overridable via DOTFILES_DIR; consumers default
# to "$HOME/Projects/dotfiles".

# Requires IOS_DEVICE_UDID; installs never run against an implicit device.
ios_resolve_device() {
  if [[ -n "${IOS_DEVICE_UDID:-}" ]]; then
    return 0
  fi
  print -ru2 -- "IOS_DEVICE_UDID is not set."
  print -ru2 -- "Export it, pass it along (e.g. make install IOS_DEVICE_UDID=<device-udid>),"
  print -ru2 -- "or set it in dotfiles' .env as IOS_DEVICE_UDID=\"<device-udid>\"."
  return 1
}

# Preflight: device must be visible to devicectl and not offline.
ios_check_device() {
  ios_resolve_device || return 1
  local deviceId="$IOS_DEVICE_UDID" listing row state
  if ! listing=$(xcrun devicectl list devices 2>&1); then
    print -ru2 -- "xcrun devicectl list devices failed:"
    print -ru2 -- "$listing"
    return 1
  fi
  row=$(print -r -- "$listing" | grep -F -- "$deviceId" | head -n 1) || true
  if [[ -z "$row" ]]; then
    print -ru2 -- "iPhone $deviceId is not visible to Xcode."
    print -ru2 -- "Connect it once by cable, unlock it, trust this Mac, and enable"
    print -ru2 -- "Developer Mode (Settings > Privacy & Security > Developer Mode)."
    print -ru2 -- "Wi-Fi debugging can be enabled afterwards in Xcode > Devices and Simulators."
    return 1
  fi
  if [[ "$row" == *" (UDID)"* ]]; then
    state=${row#*" (UDID)"}
  elif [[ "$row" == *" (ECID)"* ]]; then
    state=${row#*" (ECID)"}
  elif [[ "$row" == *" (CoreDevice)"* ]]; then
    state=${row#*" (CoreDevice)"}
  else
    print -ru2 -- "iPhone $deviceId check: unexpected devicectl output:"
    print -ru2 -- "$row"
    return 1
  fi
  state=${${=state}[1]}
  if [[ "$state" != connected && "$state" != available ]]; then
    print -ru2 -- "iPhone $deviceId is paired but currently '$state'."
    print -ru2 -- "Unlock it and connect it (cable or Wi-Fi debugging), then run again."
    return 1
  fi
  print -r -- "iPhone $deviceId ready ($state)"
}

# Preflight: Xcode account must have provisioning teams and the keychain must
# contain at least one valid codesigning identity.
ios_check_signing() {
  local count identities teams
  teams=$(defaults read com.apple.dt.Xcode IDEProvisioningTeams 2>/dev/null) || true
  if [[ -n "$teams" ]] && ! grep -q teamID <<< "$teams"; then
    teams=$(defaults read com.apple.dt.Xcode IDEProvisioningTeamByKeychainAccounts 2>/dev/null) || true
  fi
  if [[ -z "$teams" ]]; then
    print -ru2 -- "No provisioning teams registered in Xcode."
    print -ru2 -- "Open Xcode > Settings > Accounts, sign in with the Apple ID used by these projects,"
    print -ru2 -- "and let Xcode download the team details, then run again."
    return 1
  fi
  identities=$(security find-identity -v -p codesigning 2>/dev/null | tail -n 1)
  count=$(print -r -- "$identities" | grep -oE "[0-9]+ valid identities" | grep -oE "[0-9]+") || true
  if [[ -z "$count" || "$count" == 0 ]]; then
    print -ru2 -- "No valid codesigning identities in the keychain ($identities)."
    print -ru2 -- "Your Apple Development certificate may be revoked or expired."
    print -ru2 -- "Open Xcode > Settings > Accounts, sign in again, and refresh certificates, then run again."
    return 1
  fi
}

# Device-side signature probe: installing the previous build in seconds tells us
# whether the device still accepts the signing identity. Only an identity the
# device no longer trusts is fatal (rebuilding can never fix that); any other
# probe failure (e.g. an expired profile) falls through to the fresh build,
# which re-signs and re-provisions anyway.
ios_signature_probe() {
  [[ -d "$IOS_APP_PATH" ]] || return 0
  echo "\n🧪 Probing device code-signing trust..."
  local probe
  probe=$(xcrun devicectl device install app --device "$IOS_DEVICE_UDID" "$IOS_APP_PATH" 2>&1) || true
  if grep -Eq "0xe8008018|identity used to sign" <<<"$probe"; then
    echo "$probe" >&2
    echo "\n❌ The device rejects the signing identity; rebuilding won't fix it." >&2
    echo "Delete dead certificates from Keychain, check the phone's date/time" >&2
    echo "(automatic), reboot the phone, then run again." >&2
    return 1
  fi
}

ios_install_app() {
  : "${APP_NAME:?APP_NAME must be set}"
  : "${PROJECT_ROOT:?PROJECT_ROOT must be set}"
  SCHEME="${SCHEME:-$APP_NAME Release}"
  CONFIGURATION="${CONFIGURATION:-Release}"
  DERIVED_DATA_DIR="${DERIVED_DATA_DIR:-$PROJECT_ROOT/.build/DerivedData}"
  IOS_PROJ_PATH="$PROJECT_ROOT/$APP_NAME.xcodeproj"
  IOS_APP_PATH="$DERIVED_DATA_DIR/Build/Products/$CONFIGURATION-iphoneos/$APP_NAME.app"

  ios_resolve_device || return 1
  ios_signature_probe || return 1

  echo "\n🔐 Resolving provisioning profile..."
  xcodebuild \
    -project "$IOS_PROJ_PATH" \
    -scheme "$SCHEME" \
    -configuration "$CONFIGURATION" \
    -destination "platform=iOS,id=$IOS_DEVICE_UDID" \
    -derivedDataPath "$DERIVED_DATA_DIR" \
    -allowProvisioningUpdates \
    -allowProvisioningDeviceRegistration

  local -a buildSettings=()
  local timestamp expiration profilePath
  if [[ -n "${IOS_SET_PROFILE_EXPIRATION:-}" ]]; then
    profilePath=$(find "$DERIVED_DATA_DIR" \
      -path "*/Build/Products/$CONFIGURATION-iphoneos/$APP_NAME.app/embedded.mobileprovision" \
      -print0 | xargs -0 ls -t | head -n 1)
    expiration=$(
      security cms -D -i "$profilePath" \
      | plutil -extract ExpirationDate xml1 -o - - \
      | xmllint --xpath "string(//date)" - \
      | sed 's/Z$/.000Z/'
    )
    timestamp="$(date -u '+%Y-%m-%dT%H:%M:%S.000Z')"
    buildSettings+=(BUILD_TIMESTAMP="$timestamp" PROVISIONING_PROFILE_EXPIRATION_DATE="$expiration")
  fi
  if [[ -n "${DEVELOPMENT_TEAM:-}" ]]; then
    buildSettings+=(DEVELOPMENT_TEAM="$DEVELOPMENT_TEAM")
  fi

  echo "\n🔧 Building $APP_NAME for device $IOS_DEVICE_UDID..."
  xcodebuild \
    -project "$IOS_PROJ_PATH" \
    -scheme "$SCHEME" \
    -configuration "$CONFIGURATION" \
    -destination "platform=iOS,id=$IOS_DEVICE_UDID" \
    -derivedDataPath "$DERIVED_DATA_DIR" \
    -allowProvisioningUpdates \
    "${buildSettings[@]}" \
    build

  if [[ ! -d "$IOS_APP_PATH" ]]; then
    echo "❌ Expected app not found at: $IOS_APP_PATH" >&2
    return 1
  fi

  echo "\n📦 Installing app..."
  xcrun devicectl device install app \
    --device "$IOS_DEVICE_UDID" \
    "$IOS_APP_PATH"

  if [[ -n "${timestamp:-}" ]]; then
    echo "\n🕒 Timestamp: $timestamp"
    echo "📅 Expiration date: $expiration"
  fi
  echo "✅ $APP_NAME.app installed successfully on device $IOS_DEVICE_UDID"
}
