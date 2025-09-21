#!/bin/zsh

extensions=(
  "anysphere.cpptools"
  "anysphere.cursorpyright"
  "anysphere.remote-containers"
  "anysphere.remote-wsl"
  "astro-build.astro-vscode"
  "biomejs.biome"
  "bradlc.vscode-tailwindcss"
  "cweijan.vscode-mysql-client2"
  "dbaeumer.vscode-eslint"
  "docker.docker"
  "dotjoshjohnson.xml"
  "dsznajder.es7-react-js-snippets"
  "eamodio.gitlens"
  "editorconfig.editorconfig"
  "esbenp.prettier-vscode"
  "foxundermoon.shell-format"
  "github.github-vscode-theme"
  "mikestead.dotenv"
  "mkhl.shfmt"
  "ms-azuretools.vscode-containers"
  "ms-azuretools.vscode-docker"
  "ms-python.debugpy"
  "ms-python.python"
  "ms-vscode.cmake-tools"
  "mylesmurphy.prettify-ts"
  "oderwat.indent-rainbow"
  "patbenatar.advanced-new-file"
  "qcz.text-power-tools"
  "redhat.vscode-yaml"
  "rvest.vs-code-prettier-eslint"
  "sleistner.vscode-fileutils"
  "unifiedjs.vscode-mdx"
  "usernamehw.errorlens"
  "wallabyjs.quokka-vscode"
  "xaver.clang-format"
  "yoavbls.pretty-ts-errors"
)

echo "Installing extensions..."

# Check which editors are available
cursor_available=false
vscode_available=false

if command -v cursor &> /dev/null; then
  cursor_available=true
  echo "📝 Cursor detected"
fi

if command -v code &> /dev/null; then
  vscode_available=true
  echo "📝 VS Code detected"
fi

if [ "$cursor_available" = false ] && [ "$vscode_available" = false ]; then
  echo "⚠️ Neither Cursor nor VS Code found!"
  exit 1
fi

# Install extensions in a single pass
for ext in "${extensions[@]}"; do
  echo "Installing $ext..."

  if [ "$cursor_available" = true ]; then
    cursor --install-extension "$ext" || echo "  ⚠️ Failed in Cursor"
  fi

  if [ "$vscode_available" = true ]; then
    code --install-extension "$ext" || echo "  ⚠️ Failed in VS Code"
  fi
done

echo "🎉 All extension installations finished!"
