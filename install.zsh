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
ignoredItems=("vscode-cursor" "ai" ".DS_Store")

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

# Copy AGENTS.md and link for Claude/Codex/OpenCode
[ -f "./src/ai/AGENTS.md" ] && {
  echo "\n🤖 Syncing agent settings"
  cp "./src/ai/AGENTS.md" "$homeDir/AGENTS.md" && echo "  ✅ AGENTS.md"
  mkdir -p "$homeDir/.claude" "$homeDir/.codex" "$homeDir/.config/opencode"
  ln -sf "$homeDir/AGENTS.md" "$homeDir/.claude/CLAUDE.md" && echo "  ✅ ~/.claude/CLAUDE.md → AGENTS.md"
  ln -sf "$homeDir/AGENTS.md" "$homeDir/.codex/AGENTS.md" && echo "  ✅ ~/.codex/AGENTS.md → AGENTS.md"
  ln -sf "$homeDir/AGENTS.md" "$homeDir/.config/opencode/AGENTS.md" && echo "  ✅ ~/.config/opencode/AGENTS.md → AGENTS.md"
}

echo "\n🎉 Done!"
echo "👉 Run 'source ~/.zshrc' to apply the changes."


