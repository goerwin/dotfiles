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
if command -v node &>/dev/null; then
  node "src/.config/karabiner/_template.ts" > "src/.config/karabiner/karabiner.json" || exit 1
  echo "Generated karabiner.json from template"
fi

homeDir=$(
  cd $homeDir
  pwd -P
) # absolute path

echo -e "\nCopying files..."

ignoredItems=("vscode-cursor")

for entry in $(ls -a ./src); do
  if [ $entry != "." ] && [ $entry != ".." ] && [ $entry != ".DS_Store" ] && [[ ! " ${ignoredItems[*]} " =~ " $entry " ]]; then
    cp -r ./src/$entry $homeDir
    echo "Copying $entry"
  fi
done

echo "\nFiles copied into $homeDir"

# Copy VSCode/Cursor settings
[ -d "./src/vscode-cursor" ] && {
  [ -d "$HOME/Library/Application Support/Code/User" ] && cp -r ./src/vscode-cursor/* "$HOME/Library/Application Support/Code/User/"
  [ -d "$HOME/Library/Application Support/Cursor/User" ] && cp -r ./src/vscode-cursor/* "$HOME/Library/Application Support/Cursor/User/"
  echo "VSCode/Cursor settings copied"
}

echo "Success! source $homeDir/.zshrc or restart your terminal to apply changes"
