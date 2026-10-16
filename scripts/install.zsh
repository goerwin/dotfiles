#!/bin/zsh
set -euo pipefail

cd "${0:A:h:h}" || exit 1

homeDir=${HOME}

echo "◆ Dotfiles Installer\n"

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

echo "\n🎉 Done!"
echo "👉 Run 'source ~/.zshrc' to apply the changes."


