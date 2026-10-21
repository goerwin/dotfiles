# Keep shared environment variables and secrets in .zshenv (read by all shells).
# export MACHINE_TYPE="godaddy"
# export GOCODE_BASE_URL="xxx"
# export GOCODE_API_KEY="xxx"
# export ANTHROPIC_BASE_URL="$GOCODE_BASE_URL"
# export ANTHROPIC_AUTH_TOKEN="$GOCODE_API_KEY"

# Include executables installed by tools such as Claude Code and Herdr.
export PATH="$HOME/.local/bin:$PATH"

ZSH_PATH="$HOME/.zsh"

# Settings
mkdir -p "$ZSH_PATH"
unsetopt beep # Disable zsh's error bell.

# Functions

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

function zshInstallPlugin() {
  local pluginDir="$ZSH_PATH/$1"
  if [[ ! -d "$pluginDir" ]]; then
    echo "Installing $1..."
    git clone "$2" "$pluginDir" || return
  fi
  source "$pluginDir/$3"
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
  if [ -z "$1" ]; then
    echo "❌ Error: Please specify a branch name (e.g., git update main)"
    return 1
  fi

  if ! git diff-index --quiet HEAD --; then
    echo "⚠️  Warning: You have uncommitted changes. Please stash or commit them first."
    return 1
  fi

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

# Aliases

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

# Others
alias sourcezsh="source ~/.zshrc"
alias rmrf="rm -rf"
alias cc="claude"
alias matrix="cmatrix"
alias cd.="cd ."
alias cdb="cd -" # go back to previous directory

# Main

# Bootstrap Homebrew; fnm and Starship are installed through the Brewfile.
if ! isCommand brew; then
  echo "Installing Homebrew..."
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi
isCommand starship && eval "$(starship init zsh)"
isCommand fnm && eval "$(fnm env --use-on-cd --shell zsh)"

# zsh-syntax-highlighting
zshInstallPlugin "zsh-syntax-highlighting" "https://github.com/zsh-users/zsh-syntax-highlighting.git" "zsh-syntax-highlighting.zsh"

# zsh-autosuggestions
[[ -r "$HOMEBREW_PREFIX/share/zsh-autosuggestions/zsh-autosuggestions.zsh" ]] &&
  source "$HOMEBREW_PREFIX/share/zsh-autosuggestions/zsh-autosuggestions.zsh"

# zsh-z
zshInstallPlugin "zsh-z" "https://github.com/agkozak/zsh-z.git" "zsh-z.plugin.zsh"

# Initialize zsh completion and Bash-compatible completion functions.
[[ -d "$HOMEBREW_PREFIX/share/zsh-completions" ]] &&
  fpath=("$HOMEBREW_PREFIX/share/zsh-completions" $fpath)
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

# Load cargo environment variables.
. "$HOME/.cargo/env"

# Godaddy

if [[ "$MACHINE_TYPE" == "godaddy" ]]; then
  # AWS setup godaddy
  # https://pep-docs.uxp.gdcorp.tools/docs/onboarding/machine-setup/aws/

  # NOTE: Maybe you need to uncomment this when needing to do AWS stuff
  # export USER=egaitan # user should be your godaddy email username
  alias okta='OKTA_DOMAIN=godaddy.okta.com; KEY=$(openssl rand -hex 18); eval $(aws-okta-processor authenticate -e -o $OKTA_DOMAIN -u $USER -k $KEY -d 7200)'
  alias kasm='. kasm-wrapper'
  export AWS_REGION=us-west-2 # (ar does not set the region properly, so doing it manually)

  # Load awsprofile's zsh completion setup.
  isCommand awsprofile && eval "$(awsprofile completion zsh)"

  # Before commands such as deploy-assets, select a profile (e.g. ap uxp_prod_ops).
  # AWS_REGION above sets the region; authenticate through SSO if prompted.
fi
