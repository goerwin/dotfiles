# .zshrc is sourced in interactive shells. It should contain commands to set up
# aliases, functions, options, key bindings, etc.

ZSH_PATH=$HOME/.zsh
TEXT_EDITOR="code"

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
  gitRepoUrl=$1
  baseName=$2

  pushd $ZSH_PATH # temporarily "cd" into this path until popd
  git clone $gitRepoUrl $baseName
  popd
}

function ZshUpdatePlugins() {
  rm -rf $ZSH_PATH
  source $HOME/.zshrc
}

function isDir() {
  if [ -d $1 ]; then
    true
  else
    false
  fi
}

function isFile() {
  if [ -e $1 ]; then
    true
  else
    false
  fi
}

function isCommand() {
  if command -v $1 &>/dev/null; then
    true
  else
    false
  fi
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
# Commands/Plugins
#//////////////////////////

# Homebrew

if isCommand "brew"; then
  :
else
  echo "Installing Homebrew..."
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

# Starship

if isCommand "starship"; then # WSL
  eval "$(starship init zsh)"
else
  echo "Installing Starship..."
  curl -sS https://starship.rs/install.sh | sh
fi

# NVM

NVM_DIR="$([ -z "${XDG_CONFIG_HOME-}" ] && printf %s "${HOME}/.nvm" || printf %s "${XDG_CONFIG_HOME}/nvm")"

if isFile "$NVM_DIR/nvm.sh"; then
  [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh" # This loads nvm
else
  echo "Installing NVM..."
  PROFILE=/dev/null bash -c 'curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash'
  [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh" # This loads nvm
fi

# zsh-syntax-highlighting

if isDir $ZSH_PATH/zsh-syntax-highlighting; then
  source "$ZSH_PATH/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh"
else
  echo "Installing ZSH syntax highlighting..."
  zshCloneGitRepoToZshDir "https://github.com/zsh-users/zsh-syntax-highlighting.git" "zsh-syntax-highlighting"
fi

# enable auto completions for commands/files
autoload -Uz compinit bashcompinit
compinit
bashcompinit

# keyboard navigation to autocompletions
zstyle ':completion:*' menu select

# zsh-autosuggestions
source $(brew --prefix)/share/zsh-autosuggestions/zsh-autosuggestions.zsh

# Initialize python environment
eval "$(pyenv init - zsh)"

# JOB - WORK - GODADDY SETUP
# https://pep-docs.uxp.gdcorp.tools/docs/onboarding/machine-setup/aws/

# user should be your godaddy email username
export USER=egaitan
alias okta='OKTA_DOMAIN=godaddy.okta.com; KEY=$(openssl rand -hex 18); eval $(aws-okta-processor authenticate -e -o $OKTA_DOMAIN -u $USER -k $KEY -d 7200)'
alias kasm='. kasm-wrapper'

# Created by `pipx` on 2025-01-21 01:09:18
export PATH="$PATH:/Users/goerwin/.local/bin"
export PATH="$PATH:/Users/goerwin/.local/bin"
export PYENV_ROOT="$HOME/.pyenv"
[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"

# Enable AWS Profile auto completions (ap, ar)
eval "$(awsprofile completion zsh)"

# (ar does not set the region properly, so doing it manually)
export AWS_REGION=us-west-2
