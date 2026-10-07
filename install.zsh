#!/bin/zsh

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
homeDir=$(cd $homeDir; pwd -P)
echo "\n📂 Copying dotfiles → $homeDir"

# Remove keyRemapper folders first so renamed/deleted files don't linger
for folder in keyRemapperMac keyRemapperWin; do
  if [ -d "$homeDir/$folder" ]; then
    rm -rf "$homeDir/$folder" && echo "  🗑️  removed $folder"
  fi
done

setopt GLOB_DOTS
ignoredItems=("vscode-cursor" ".DS_Store")

for entry in ./src/*; do
  entryName=$(basename "$entry")
  case " ${ignoredItems[@]} " in
  *" $entryName "*) echo "  ➖ $entryName" ;;
  *) cp -r "$entry" "$homeDir" && echo "  ✅ $entryName" ;;
  esac
done

# Copy VSCode/Cursor settings
[ -d "./src/vscode-cursor" ] && {
  echo "\n🖥️  Syncing editor settings"
  [ -d "$HOME/Library/Application Support/Code/User" ]   && cp -r ./src/vscode-cursor/* "$HOME/Library/Application Support/Code/User/"   && echo "  ✅ VSCode"
  [ -d "$HOME/Library/Application Support/Cursor/User" ] && cp -r ./src/vscode-cursor/* "$HOME/Library/Application Support/Cursor/User/" && echo "  ✅ Cursor"
}

echo "\n🎉 Done!"
echo "👉 Run 'source ~/.zshrc' to apply the changes."


