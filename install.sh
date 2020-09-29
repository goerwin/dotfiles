destDir=$1

if [[ $destDir == "" ]]; then
  echo "Specify directory DIR where to copy dotfiles"
  exit 1
fi

if ! [ -d $destDir ]; then
  echo "Dir $destDir does not exist"
  exit 1
fi

destDir=$(
  cd $destDir
  pwd -P
) # absolute path

echo -e "\nCopying files..."

for entry in $(ls -a ./src); do
  if [ $entry != "." ] && [ $entry != ".." ]; then
    cp -r ./src/$entry $destDir
    echo "Copying $entry"
  fi
done

echo "Files copied into $destDir"

destDir=$1
echo "Sourcing files: $destDir/.zshenv and $destDir/.zshrc"
source $destDir/.zshenv $destDir/.zshrc
echo "Success!"
