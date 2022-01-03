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
  node "src/.config/karabiner/_template.js" >"src/.config/karabiner/karabiner.json"
fi

homeDir=$(
  cd $homeDir
  pwd -P
) # absolute path

echo -e "\nCopying files..."

for entry in $(ls -a ./src); do
  if [ $entry != "." ] && [ $entry != ".." ] && [ $entry != ".DS_Store" ]; then
    cp -r ./src/$entry $homeDir
    echo "Copying $entry"
  fi
done

echo "Files copied into $homeDir"
echo "Success! source $homeDir/.zshrc or restart your terminal to apply changes"
