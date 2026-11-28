# Signing for the app installs. Mac apps sign with one self-signed certificate:
# it never expires, Apple can't revoke it, and the privacy permissions granted
# to an app survive rebuilds. Apps that need an Apple provisioning profile (all
# iOS apps, and Financer and Daylier on the Mac for keychain sharing) sign with
# the personal team's Apple Development certificate instead.

LOCAL_SIGNING_IDENTITY="Goerwin Local Code Signing"
# The login keychain asks for its password before codesign can use a new key,
# which would hang unattended installs, so the certificate has its own keychain.
# Its password is empty: the key is protected by your account's file access.
LOCAL_SIGNING_KEYCHAIN="$HOME/Library/Keychains/goerwin-signing.keychain-db"
LOCAL_SIGNING_HASH=

# Creates the certificate on first use, then keeps its keychain searchable and
# unlocked, and sets LOCAL_SIGNING_HASH for codesign.
local_signing_prepare() {
  local keychain=$LOCAL_SIGNING_KEYCHAIN identities line
  if [[ ! -f "$keychain" ]]; then
    local_signing_create || return 1
  fi
  local -a searchList=("${(@f)$(security list-keychains -d user | sed -e 's/^ *"//' -e 's/"$//')}")
  if (( ! ${searchList[(Ie)$keychain]} )); then
    security list-keychains -d user -s "${searchList[@]}" "$keychain" || return 1
  fi
  security unlock-keychain -p "" "$keychain" || return 1

  identities=$(security find-identity -p codesigning "$keychain") || return 1
  for line in "${(@f)identities}"; do
    if [[ "$line" == *"\"$LOCAL_SIGNING_IDENTITY\""* ]]; then
      LOCAL_SIGNING_HASH=${${=line}[2]}
      print -r -- "Signing identity: $LOCAL_SIGNING_IDENTITY ($LOCAL_SIGNING_HASH)"
      return 0
    fi
  done
  print -ru2 -- "\"$LOCAL_SIGNING_IDENTITY\" is missing from $keychain."
  print -ru2 -- "Delete that keychain file to have it recreated, then run again."
  return 1
}

local_signing_create() {
  local keychain=$LOCAL_SIGNING_KEYCHAIN workDir password
  workDir=$(mktemp -d "${TMPDIR:-/tmp}/signing-certificate.XXXXXX") || return 1
  password=$(/usr/bin/openssl rand -hex 16)
  {
    # The system openssl writes a PKCS#12 file that `security import` accepts.
    /usr/bin/openssl req -x509 -newkey rsa:2048 -nodes -days 3650 \
      -subj "/CN=$LOCAL_SIGNING_IDENTITY" \
      -addext "basicConstraints=critical,CA:false" \
      -addext "keyUsage=critical,digitalSignature" \
      -addext "extendedKeyUsage=critical,codeSigning" \
      -keyout "$workDir/key.pem" -out "$workDir/certificate.pem" 2>/dev/null \
    && /usr/bin/openssl pkcs12 -export -name "$LOCAL_SIGNING_IDENTITY" \
      -inkey "$workDir/key.pem" -in "$workDir/certificate.pem" \
      -out "$workDir/identity.p12" -passout "pass:$password" \
    && security create-keychain -p "" "$keychain" \
    && security set-keychain-settings "$keychain" \
    && security unlock-keychain -p "" "$keychain" \
    && security import "$workDir/identity.p12" -k "$keychain" -P "$password" \
      -T /usr/bin/codesign \
    && security set-key-partition-list -S apple-tool:,apple:,codesign: -s \
      -k "" "$keychain" >/dev/null \
    && print -r -- "Created \"$LOCAL_SIGNING_IDENTITY\", valid for 10 years."
  } always {
    rm -rf "$workDir"
  }
}

# Re-signs an app and all the code inside it with the local certificate,
# keeping each part's identifier and entitlements. The hardened runtime is
# dropped: it only loads libraries from the same team, and a self-signed
# certificate has none, so apps with embedded frameworks would crash at launch.
local_signing_sign() {
  local app=$1
  local_signing_prepare || return 1
  codesign --force --deep --sign "$LOCAL_SIGNING_HASH" \
    --preserve-metadata=identifier,entitlements "$app"
}

# Xcode must have provisioning teams and the keychain at least one Apple
# Development identity whose certificate Apple still trusts.
check_signing() {
  local teams identities hash certificates usable
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

  # find-identity -v flags revoked identities with CSSMERR_ codes, but only
  # once the keychain has learned of the revocation, so each is checked online.
  identities=$(security find-identity -v -p codesigning 2>/dev/null \
    | grep -F '"Apple Development:' | grep -v CSSMERR_) || true
  certificates=$(mktemp -d "${TMPDIR:-/tmp}/signing.XXXXXX")
  security find-certificate -a -Z -p -c "Apple Development" >"$certificates/all" 2>/dev/null || true
  for hash in ${(f)"$(print -r -- "$identities" | awk '{print $2}')"}; do
    awk -v hash="$hash" '/^SHA-1 hash:/ { keep = ($3 == hash) }
      keep && /BEGIN CERTIFICATE/, keep && /END CERTIFICATE/' \
      "$certificates/all" >"$certificates/$hash.pem"
    if security verify-cert -q -p codeSign -R ocsp -c "$certificates/$hash.pem" >/dev/null 2>&1; then
      usable=$(print -r -- "$identities" | grep -F -- "$hash")
      break
    fi
  done
  rm -rf "$certificates"

  if [[ -z "$usable" ]]; then
    print -ru2 -- "No usable Apple Development identity in the keychain."
    print -ru2 -- "Your Apple Development certificate may be revoked or expired."
    print -ru2 -- "Open Xcode > Settings > Accounts, sign in again, and refresh certificates, then run again."
    return 1
  fi
  usable=${usable#*\"}
  print -r -- "Signing identity: ${usable%\"*}"
}
