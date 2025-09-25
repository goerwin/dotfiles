homeDir=$1

if [[ $homeDir == "" ]]; then
  echo "Specify directory DIR where to copy dotfiles"
  exit 1
fi

if ! [ -d $homeDir ]; then
  echo "Dir $homeDir does not exist"
  exit 1
fi

# Generate karabiner.json from template automatically
{
  if command -v node &>/dev/null; then
    node "src/.config/karabiner/_template.ts" >"src/.config/karabiner/karabiner.json" || exit 1
    echo "Generated karabiner.json from template"
  fi
}

# Copy src files into homeDir
{
  homeDir=$(
    cd $homeDir
    pwd -P
  ) # absolute path

  echo -e "\nCopying files..."

  setopt GLOB_DOTS # include dotfiles in globs
  ignoredItems=("vscode-cursor" "ai" ".DS_Store" "biome.template.json")

  for entry in ./src/*; do
    entryName=$(basename "$entry")

    case " ${ignoredItems[@]} " in
    *" $entryName "*)
      # skip
      ;;
    *)
      cp -r "$entry" "$homeDir"
      echo "Copying $entryName"
      ;;
    esac
  done

  cp -r ./src/biome.template.json "$homeDir/biome.json"
  echo "Copying biome.json from biome.template.json"
  echo "\nFiles copied into $homeDir"
}

# Copy VSCode/Cursor settings
{
  [ -d "./src/vscode-cursor" ] && {
    [ -d "$HOME/Library/Application Support/Code/User" ] && cp -r ./src/vscode-cursor/* "$HOME/Library/Application Support/Code/User/"
    [ -d "$HOME/Library/Application Support/Cursor/User" ] && cp -r ./src/vscode-cursor/* "$HOME/Library/Application Support/Cursor/User/"
    echo "VSCode/Cursor settings copied"
  }
}

echo "Success! source $homeDir/.zshrc or restart your terminal to apply changes"
