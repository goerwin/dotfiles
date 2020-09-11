
if [[ $1 == "" ]]; then
  echo "Specify directory DIR where to copy dotfiles"
  exit 1
fi

tmpDir=$(mktemp -d)
git clone http://github.com/goerwin/dotfiles tmpDir
echo "$tmpDir"
