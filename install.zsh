#!/bin/zsh

homeDir=${HOME}

echo "◆ Dotfiles Installer\n"

# Generate karabiner.json from template
if command -v node &>/dev/null; then
  generatedKarabinerDestination=".config/karabiner/karabiner.json"
  node "src/.config/karabiner/_template.ts" >"src/$generatedKarabinerDestination" || exit 1
  echo "⚙️  $generatedKarabinerDestination generated"
fi

# Copy src files into homeDir
homeDir=$(cd $homeDir; pwd -P)
echo "\n📂 Copying dotfiles → $homeDir"

setopt GLOB_DOTS
ignoredItems=("vscode-cursor" "ai" ".DS_Store" "biome.template.json")

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

echo "\n🔄 Sourcing $homeDir/.zshrc"
echo "\n🎉 Done!"


