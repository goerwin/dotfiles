#!/bin/zsh
# alfred-title: Install dotfiles

set -euo pipefail

cd "${0:A:h:h}" || exit 1

# Homebrew installation
if ! command -v brew &>/dev/null; then
  brewExecutable="/opt/homebrew/bin/brew"
  [[ "$(/usr/bin/uname -m)" == arm64 ]] || brewExecutable="/usr/local/bin/brew"
  if [[ ! -x "$brewExecutable" ]]; then
    echo "Installing Homebrew..."
    brewInstaller=$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)
    /bin/bash -c "$brewInstaller"
  fi
  eval "$("$brewExecutable" shellenv)"
fi

print -r -- "Updating dotfiles..."
git pull --ff-only

homeDir=${HOME}

echo "◆ Dotfiles Installer\n"

# zsh-z has no Homebrew formula; install it here instead of at shell startup.
if [[ ! -d "$homeDir/.zsh/zsh-z" ]]; then
  mkdir -p "$homeDir/.zsh"
  git clone https://github.com/agkozak/zsh-z.git "$homeDir/.zsh/zsh-z"
fi

# Generate karabiner.json from template
if command -v node &>/dev/null; then
  generatedKarabinerDestination=".config/karabiner/karabiner.json"
  node "src/.config/karabiner/_template.ts" >"src/$generatedKarabinerDestination" || exit 1
  echo "⚙️  $generatedKarabinerDestination generated"

  generatedLocalPwDestination="keyRemapperMac/rules/_localPw.json"
  node "src/keyRemapperMac/rules/_localPw.ts" >"src/$generatedLocalPwDestination" || exit 1
  echo "⚙️  $generatedLocalPwDestination generated"
fi

# Copy src files into homeDir
homeDir=$(cd "$homeDir" && pwd -P)
echo "\n📂 Copying dotfiles → $homeDir"

# Remove keyRemapper folders first so renamed/deleted files don't linger
for folder in keyRemapperMac keyRemapperWin; do
  if [ -d "$homeDir/$folder" ]; then
    rm -rf "$homeDir/$folder"
    echo "  🗑️  removed $folder"
  fi
done

setopt GLOB_DOTS
ignoredItems=("vscode-cursor" ".DS_Store")

# Top-level src folders whose installed files are listed individually.
recursiveListingFolders=(".local")

installEntry() {
  local entry="$1"
  local destination="$2"
  local file

  rsync -a --exclude='.DS_Store' "$entry" "$destination/" || return 1
  [[ "${entry:t}" == ".DS_Store" ]] && return 0

  local topLevelFolder="${entry#./src/}"
  topLevelFolder="${topLevelFolder%%/*}"
  if (( ${recursiveListingFolders[(Ie)$topLevelFolder]} == 0 )); then
    print -r -- "  ✅ $destination/${entry:t}"
    return 0
  fi

  for file in "$entry"/**/*(ND^/) "$entry"(N^/); do
    [[ "${file:t}" == ".DS_Store" ]] && continue
    print -r -- "  ✅ $destination/${entry:t}${file#"$entry"}"
  done
}

for entry in ./src/*; do
  entryName=$(basename "$entry")
  case " ${ignoredItems[@]} " in
  *" $entryName "*) echo "  ➖ $entryName" ;;
  *) installEntry "$entry" "$homeDir" || exit 1 ;;
  esac
done

# Copy VSCode/Cursor settings
[ -d "./src/vscode-cursor" ] && {
  echo "\n🖥️  Syncing editor settings"
  for editor in Code Cursor; do
    editorDir="$homeDir/Library/Application Support/$editor/User"
    if [ -d "$editorDir" ]; then
      for entry in ./src/vscode-cursor/*; do
        installEntry "$entry" "$editorDir" || exit 1
      done
    fi
  done
}

# Persistent macOS preferences only need to be applied during setup.
# Restore spacing: defaults -currentHost delete -globalDomain NSStatusItemSpacing
defaults -currentHost write -globalDomain NSStatusItemSpacing -int 12
defaults write NSGlobalDomain AppleKeyboardUIMode -int 3

# hidutil settings reset after restarts; the LaunchAgent reapplies this at login.
capsLockAgent="$homeDir/Library/LaunchAgents/local.dotfiles.caps-lock-delay.plist"
if launchctl print "gui/$UID" &>/dev/null; then
  launchctl bootout "gui/$UID" "$capsLockAgent" 2>/dev/null || true
  launchctl bootstrap "gui/$UID" "$capsLockAgent"
else
  echo "Caps Lock delay setting will apply at the next graphical login."
fi

echo "\n🎉 Done!"
echo "👉 Run 'source ~/.zshrc' to apply the changes."
