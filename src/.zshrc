# .zshrc configures interactive shells: aliases, functions, options, and key bindings.
# .zshenv is read by default for all shells, including noninteractive shells.
# Keep essential environment variables in .zshenv.

# Include executables installed by tools such as Claude Code and Herdr.
export PATH="$HOME/.local/bin:$PATH"

ZSH_PATH=$HOME/.zsh
TEXT_EDITOR="cursor"

#//////////////////////////
# Settings
#//////////////////////////

# Create the plugin directory.
mkdir -p $ZSH_PATH

# Disable zsh's own error bell.
unsetopt beep

#//////////////////////////
# Functions
#//////////////////////////

function isDir() {
  [ -d "$1" ]
}

function isFile() {
  [ -e "$1" ]
}

function isCommand() {
  command -v "$1" &>/dev/null
}

# Run a command once per key, recording only successful runs.
runOnce() {
  local _RUN_ONCE_DIR="$HOME/.cache/.run-once"
  local key="$1"
  shift

  local flag="$_RUN_ONCE_DIR/.$key"
  [[ -f "$flag" ]] && return 0
  mkdir -p "$_RUN_ONCE_DIR" || return 1
  "$@" && touch "$flag"
}

function zshCloneGitRepoToZshDir() {
  local gitRepoUrl="$1"
  local baseName="$2"

  pushd "$ZSH_PATH" # temporarily "cd" into this path until popd
  git clone "$gitRepoUrl" "$baseName"
  popd
}

function zshInstallPlugin() {
  local pluginName="$1"
  local gitUrl="$2"
  local relativeSourceFilePath="$3"
  local pluginDir="$ZSH_PATH/$pluginName"

  if isDir "$pluginDir"; then
    source "$pluginDir/$relativeSourceFilePath"
  else
    echo "Installing $pluginName..."
    zshCloneGitRepoToZshDir "$gitUrl" "$pluginName"
  fi
}

function zshRemovePlugins() {
  rm -rf "$ZSH_PATH" && source "$HOME/.zshrc"
}

# Commit without running the pre-commit and commit-msg hooks.
function gitCommitNoVerify() {
  git commit -m "$*" --no-verify
}

# Update a local branch from origin without switching branches.
function gitUpdateBranch() {
  # 1. Check if a branch name was provided
  if [ -z "$1" ]; then
    echo "❌ Error: Please specify a branch name (e.g., git update main)"
    return 1
  fi

  # 2. Refuse updates when tracked files have uncommitted changes.
  if ! git diff-index --quiet HEAD --; then
    echo "⚠️  Warning: You have uncommitted changes. Please stash or commit them first."
    return 1
  fi

  # 3. Attempt the update
  echo "🔄 Updating '$1' from remote origin..."
  if git fetch origin "$1":"$1"; then
    echo "✅ Success: Local branch '$1' is now up to date with origin/$1!"
  else
    echo "❌ Error: Update failed (see git error above)."
    return 1
  fi
}

# Clear the screen and scrollback at a zsh prompt, preserving the current command.
function clearScreenAndScrollback() {
  # Flush the redraw before clearing scrollback to avoid saving blank lines.
  zle .clear-screen
  zle -R
  printf '\033[3J'
}

#//////////////////////////
# Aliases
#//////////////////////////

# Git
alias g="git"
alias gc="git commit"
alias gcm="git commit -m"
alias gcmnv="gitCommitNoVerify"
alias gcamend="git commit --amend -C HEAD"
alias gs="git status"
alias ga="git add"
alias ga.="git add ."
alias gp="git push"
alias gpf="git push --force"
alias gpl="git pull"
alias gplr="git pull --rebase"
alias gch="git checkout"
alias gch.="git checkout ."
alias gd="git diff"
alias gd.="git diff ."
alias gds="git diff --staged"
alias gdsummary="git diff --compact-summary"
alias gupdate="gitUpdateBranch"
alias gclean="git clean"
alias gcleanf="git clean . -f"
alias gopen='gh browse'
alias gop=gopen
alias gopenpr='gh pr view "${$(git rev-parse --abbrev-ref "@{u}" 2>/dev/null)#*/}" --web'
alias gopr=gopenpr

# NPM
alias npmr="npm run"
alias npmrd="npm run dev"
alias npmrs="npm run start"
alias npmrt="npm run test"
alias npmrb="npm run build"
alias npmi="npm install"
alias npmis="npm install --save"
alias npmisd="npm install --save-dev"
alias npmu="npm uninstall"
alias npmus="npm uninstall --save"
alias npmusd="npm uninstall --save-dev"
alias npmig="npm install -g"
alias npmug="npm uninstall -g"

# CD
alias cd.="cd ."
alias cdb="cd -" # go back to previous directory

# Others
alias sourcezsh="source ~/.zshrc"
alias rmrf="rm -rf"
alias cc="claude"

#//////////////////////////
# Main
#//////////////////////////

# Homebrew
if ! isCommand "brew"; then
  echo "Installing Homebrew..."
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

# Starship
if isCommand "starship"; then
  eval "$(starship init zsh)"
else
  echo "Installing Starship..."
  curl -sS https://starship.rs/install.sh | sh
fi

# FNM
if isCommand "fnm"; then
  eval "$(fnm env --use-on-cd --shell zsh)"
else
  echo "Installing FNM..."
  curl -fsSL https://fnm.vercel.app/install | bash
fi

# zsh-syntax-highlighting
zshInstallPlugin "zsh-syntax-highlighting" "https://github.com/zsh-users/zsh-syntax-highlighting.git" "zsh-syntax-highlighting.zsh"

# zsh-autosuggestions
zshInstallPlugin "zsh-autosuggestions" "https://github.com/zsh-users/zsh-autosuggestions.git" "zsh-autosuggestions.zsh"

# zsh-z
zshInstallPlugin "zsh-z" "https://github.com/agkozak/zsh-z.git" "zsh-z.plugin.zsh"

# Initialize zsh completion and Bash-compatible completion functions.
autoload -U compinit bashcompinit && compinit && bashcompinit

# Enable keyboard selection in completion menus.
zstyle ':completion:*' menu select

# Use Emacs-style editing keys in zsh.
bindkey -e

# Ctrl + O → clear screen and scrollback
zle -N clear-screen-and-scrollback clearScreenAndScrollback
bindkey '^O' clear-screen-and-scrollback

# Ctrl + U → delete from cursor to beginning of line
bindkey "^U" backward-kill-line

# Handle common terminal sequences for Option + Left/Right word navigation.
bindkey '^[^[[D' backward-word
bindkey '^[^[[C' forward-word
bindkey '^[[1;3D' backward-word
bindkey '^[[1;3C' forward-word

# Let lowercase completion input match uppercase characters.
zstyle ':completion:*' matcher-list 'm:{a-z}={A-Z}'

# Request no Caps Lock activation delay.
hidutil property --set '{"CapsLockDelayOverride":0}' >/dev/null 2>&1

# Set menu bar item spacing to 12 once, using a runOnce flag.
# Restore the default: defaults -currentHost delete -globalDomain NSStatusItemSpacing
runOnce menu_bar_item_spacing \
  defaults -currentHost write -globalDomain NSStatusItemSpacing -int 12

# Enable Tab navigation through all macOS controls.
defaults write NSGlobalDomain AppleKeyboardUIMode -int 3

#//////////////////////////
# Godaddy
#//////////////////////////

if [[ "$MACHINE_TYPE" == "godaddy" ]]; then
  # AWS setup godaddy
  # https://pep-docs.uxp.gdcorp.tools/docs/onboarding/machine-setup/aws/

  # NOTE: Maybe you need to uncomment this when needing to do AWS stuff
  # export USER=egaitan # user should be your godaddy email username
  alias okta='OKTA_DOMAIN=godaddy.okta.com; KEY=$(openssl rand -hex 18); eval $(aws-okta-processor authenticate -e -o $OKTA_DOMAIN -u $USER -k $KEY -d 7200)'
  alias kasm='. kasm-wrapper'
  export AWS_REGION=us-west-2 # (ar does not set the region properly, so doing it manually)

  # Pipx
  if ! isCommand "pipx"; then
    brew install pipx
    pipx ensurepath
    sudo pipx ensurepath --global
  fi

  # Initialize pyenv for Python version selection.
  ! isCommand "pyenv" && brew install pyenv
  export PYENV_ROOT="$HOME/.pyenv"
  [[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"
  eval "$(pyenv init - zsh)"

  # Load awsprofile's zsh completion setup.
  eval "$(awsprofile completion zsh)"

  # Before commands such as deploy-assets, select a profile (e.g. ap uxp_prod_ops).
  # AWS_REGION above sets the region; authenticate through SSO if prompted.
fi
