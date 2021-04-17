homeDir=$1

if [[ $homeDir == "" ]]; then
  echo "Specify directory DIR where to copy dotfiles"
  exit 1
fi

if ! [ -d $homeDir ]; then
  echo "Dir $homeDir does not exist"
  exit 1
fi

homeDir=$(
  cd $homeDir
  pwd -P
) # absolute path

echo -e "\nCopying files..."

for entry in $(ls -a ./src); do
  if [ $entry != "." ] && [ $entry != ".." ]; then
    cp -r ./src/$entry $homeDir
    echo "Copying $entry"
  fi
done

echo "Files copied into $homeDir"
echo "Success! You can source $homeDir/.zshrc or restart your terminal"
