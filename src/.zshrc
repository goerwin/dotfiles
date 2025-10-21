# .zshrc is sourced in interactive shells. It should contain commands to set up
# aliases, functions, options, key bindings, etc.

ZSH_PATH=$HOME/.zsh
TEXT_EDITOR="cursor"

#//////////////////////////
# # Settings
#//////////////////////////

# Create .zsh folder for plugins
mkdir -p $ZSH_PATH

# Disable beep sound
unsetopt beep

# Enable menu navigation with double tab
# NOTE: This seems to not be doing anything
# zstyle ':completion:*' menu select

# Case insensitive tab completion
# NOTE: This seems to not be doing anything
# zstyle ':completion:*' matcher-list 'm:{a-zA-Z}={A-Za-z}'

#//////////////////////////
# # Functions
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

# Better way to find
function f() {
  find . -iname "$1" ${@:2}
}
function ff() {
  find . -type f -iname "$1" ${@:2}
}
function fd() {
  find . -type d -iname "$1" ${@:2}
}

function open() {
  if [[ $(grep -s Microsoft /proc/version) ]]; then # WSL
    explorer.exe $(wslpath -w "${@:-.}")
  elif [[ $(grep -s WSL2 /proc/version) ]]; then # WSL2
    explorer.exe $@
  elif command -v open &>/dev/null; then # Mac
    command open $@
  else
    echo "Open not found"
  fi
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

#//////////////////////////
# Aliases
#//////////////////////////

# Git
alias g="git"
alias gc="git commit"
alias gcm="git commit -m"
alias gcamend="git commit --amend -C HEAD"
alias gcz="git cz"
alias gs="git status"
alias ga="git add"
alias ga.="git add ."
alias gp="git push"
alias gpf="git push --force"
alias gpo="git push origin"
alias gpom="git push origin main"
alias gpomf="git push origin main --force"
alias greset="git reset"
alias gcheckout="git checkout"
alias gch="git checkout"
alias gch.="git checkout ."
alias gd="git diff"
alias gd.="git diff ."
alias gdc="git diff --cached"
alias gds="git diff --staged"
alias gclean="git clean . -f"
alias go="git open"
alias gstash="git stash --include-untracked"
alias gstashpop="git stash pop"
alias gstashlist="git stash list"
alias gstashclear="git stash clear"
alias gstashdrop="git stash drop"
alias gstashapply="git stash apply"
alias gstashbranch="git stash branch"
alias gstashcheckout="git stash checkout"

# Editor
alias code.="$TEXT_EDITOR ."
alias codezsh="$TEXT_EDITOR ~/.zshrc"

# NPM
alias npmlsg="npm ls -g --depth=0"
alias npmls="npm ls --depth=0"
alias npmr="npm run"
alias npmrd="npm run dev"
alias npmrp="npm run prod"
alias npmrs="npm run start"
alias npmrsd="npm run start-dev"
alias npmrt="npm run test"
alias npmrb="npm run build"
alias npmrbd="npm run build-dev"
alias npmcu="npx npm-check-updates"
alias npmcuDev="npmcu --dep dev"
alias npmcuDevUpgrade="npmcuDev -u"
alias npmcuProd="npmcu --dep prod"
alias npmcuProdUpgrade="npmcuProd -u"
alias npmi="npm install"
alias npmig="npm install -g"
alias npmis="npm install --save"
alias npmisd="npm install --save-dev"
alias npmu="npm uninstall"
alias npmusd="npm uninstall --save-dev"
alias npmus="npm uninstall --save"
alias npmug="npm uninstall -g"
alias npmupdateg="npm update -g"
# backup npm global
alias npmbackup="npmlsg > ~/Dropbox/MacOS/backups/npmpackages.txt"
alias npmopenbackup="$TEXT_EDITOR ~/Dropbox/MacOS/backups/npmpackages.txt"

# Open
alias open.="open ."

# CD
alias cd.="cd ."
alias cdp="cd ~/projects"
alias cdprojects="cd ~/projects"
alias cdb="cd -"

# Others
alias killcam="sudo pkill "VDCAssistant""
alias sourcezsh="source ~/.zshrc"
alias rmf="rm -rf"
alias airport="sudo /System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport"
alias airportlswifi="airport -s"
alias cls=clear
alias dc="docker-compose"
alias dcb="dc build"
alias dcu="dc up"
alias dcd="dc down"
alias matrix=cmatrix

#//////////////////////////
# Main
#//////////////////////////

# Create a .zshenv file in your home directory to load environment variables specific to your machine
# For example: `export MACHINE_TYPE="work"`
# Load environment variables from .zshenv file
isFile ~/.zshenv && source ~/.zshenv

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
zshInstallPlugin "zsh-syntax-highlighting" "https://github.com/zsh-users/zsh-autosuggestions.git" "zsh-syntax-highlighting.zsh"

# zsh-autosuggestions
zshInstallPlugin "zsh-autosuggestions" "https://github.com/zsh-users/zsh-autosuggestions.git" "zsh-autosuggestions.zsh"

# zsh-z
zshInstallPlugin "zsh-z" "https://github.com/agkozak/zsh-z.git" "zsh-z.plugin.zsh"

# enable auto completions for commands/files
autoload -U compinit bashcompinit && compinit && bashcompinit

# keyboard navigation to autocompletions
zstyle ':completion:*' menu select

# Make Ctrl-U (cmd+backspace) act as "delete to beginning of line" (backward-kill-line)
bindkey "^U" backward-kill-line

# disable caps lock delay only if not already set
hidutil property --set '{"CapsLockDelayOverride":0}' >/dev/null 2>&1

#//////////////////////////
# Godaddy
#//////////////////////////

if [[ "$MACHINE_TYPE" == "godaddy" ]]; then
  # AWS setup godaddy
  # https://pep-docs.uxp.gdcorp.tools/docs/onboarding/machine-setup/aws/

  export USER=egaitan # user should be your godaddy email username
  alias okta='OKTA_DOMAIN=godaddy.okta.com; KEY=$(openssl rand -hex 18); eval $(aws-okta-processor authenticate -e -o $OKTA_DOMAIN -u $USER -k $KEY -d 7200)'
  alias kasm='. kasm-wrapper'
  export AWS_REGION=us-west-2 # (ar does not set the region properly, so doing it manually)

  # Pipx
  if ! isCommand "pipx"; then
    brew install pipx
    pipx ensurepath
    sudo pipx ensurepath --global
  fi

  # Initialize python environment
  ! isCommand "pyenv" && brew install pyenv
  export PYENV_ROOT="$HOME/.pyenv"
  [[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"
  eval "$(pyenv init - zsh)"

  # Enable AWS Profile auto completions (ap, ar)
  eval "$(awsprofile completion zsh)"

  # To use eg. deploy-assets you need to set a profile first, eg. `ap uxp_prod_ops`
  # and also a region (already done above in AWS_REGION).
  # Then, it should ask you for SSO login.
fi
