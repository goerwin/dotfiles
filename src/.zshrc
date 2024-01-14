# .zshrc is sourced in interactive shells. It should contain commands to set up
# aliases, functions, options, key bindings, etc.

# Using FNM INSTEAD OF NVM for faster init
eval "$(fnm env --use-on-cd)"
alias nvm="fnm"

# YARN
export PATH="$HOME/.yarn/bin:$HOME/.config/yarn/global/node_modules/.bin:$PATH"

ZSH_PATH=$HOME/.zsh
TEXT_EDITOR="code"
HOME_DIRS=(
  $HOME
  "/mnt/c/Users/erwin.gaitan"
  "/mnt/c/Users/goerwin"
)

GOOGLE_DRIVE_POSSIBLE_PATHS=(
  "/mnt/g/Mi unidad"
  "G:/Mi unidad"
  "Google Drive"
)

#//////////////////////////
# # Settings
#//////////////////////////

# Create .zsh folder
mkdir -p $ZSH_PATH

# Disable beep sound
unsetopt beep

# Enable menu navigation with double tab
zstyle ':completion:*' menu select

# Case insensitive tab completion
zstyle ':completion:*' matcher-list 'm:{a-zA-Z}={A-Za-z}'

#//////////////////////////
# # Key Bindings
#//////////////////////////

# Text manipulation
# bindkey -L to list all bindings
# showkey -a to see keycodes
bindkey '^[[1;5D' backward-word      # Ctrl+leftArrow
bindkey '^[[1;5C' forward-word       # Ctrl+rightArrow
bindkey "^[[1;2H" backward-kill-line # (windows: Shift+Home)
bindkey "^H" backward-kill-word      # (windows: Ctrl+Shift+H or Ctrl+Backspace)
bindkey \^U backward-kill-line       # (mac/unix)

zle -N customClearScreen
bindkey "^O" customClearScreen

# make search up and down work, so partially type and hit up/down to find relevant stuff
# start typing + [Up-Arrow] - fuzzy find history forward
if [[ "${terminfo[kcuu1]}" != "" ]]; then
  autoload -U up-line-or-beginning-search
  zle -N up-line-or-beginning-search
  bindkey "${terminfo[kcuu1]}" up-line-or-beginning-search
fi
# start typing + [Down-Arrow] - fuzzy find history backward
if [[ "${terminfo[kcud1]}" != "" ]]; then
  autoload -U down-line-or-beginning-search
  zle -N down-line-or-beginning-search
  bindkey "${terminfo[kcud1]}" down-line-or-beginning-search
fi

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

# Make dir and cd into it
function md() {
  mkdir -p "$@" && cd "$@"
}

function move() {
  mkdir -p "$2"
  mv "$1" "$2"
}

function copy() {
  mkdir -p "$2"
  cp "$1" "$2"
}

function customClearScreen() {
  echo "\ec\e[3J"
  zle reset-prompt # For TMUX
  zle redisplay    # For ZSH Shell
}

function notes() {
  for homeDir in $HOME_DIRS; do
    for googleDrivePossiblePath in $GOOGLE_DRIVE_POSSIBLE_PATHS; do
      notesFullPath="$homeDir/$googleDrivePossiblePath/Documents/notes"
      notesFullPath2="$googleDrivePossiblePath/Documents/notes"

      if isDir $notesFullPath; then
        $TEXT_EDITOR $notesFullPath
        break 2
        break
      elif isDir $notesFullPath2; then
        $TEXT_EDITOR $notesFullPath2
        break 2
        break
      fi
    done
  done
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

function cloneGitRepo() {
  gitRepoUrl=$1
  baseName=$2

  pushd $ZSH_PATH # cd temporately to this path until popd
  git clone $gitRepoUrl $baseName
  popd
}

function updatePlugins() {
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

# Youtube download youtube-dl
alias youtube="youtube-dl"
alias youtubebestaudio="youtube-dl -f bestaudio"
alias youtubebestvideo="youtube-dl -f bestvideo"
alias youtubemp3="youtube-dl -x --audio-format mp3 --audio-quality 0"
alias youtubem4a="youtube-dl -f m4a"
alias youtubemp4="youtube-dl -f mp4"
alias youtubea=youtubem4a
alias youtubev=youtubebestvideo

#//////////////////////////
# Plugins
#//////////////////////////

if isCommand "starship"; then # WSL
  eval "$(starship init zsh)"
else
  curl -fsSL https://starship.rs/install.sh | bash
fi

# zsh-syntax-highlighting
if isDir $ZSH_PATH/zsh-syntax-highlighting; then
  source "$ZSH_PATH/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh"
else
  cloneGitRepo "https://github.com/zsh-users/zsh-syntax-highlighting.git" "zsh-syntax-highlighting"
fi

# zsh-autosuggestions
if isDir $ZSH_PATH/zsh-autosuggestions; then
  source "$ZSH_PATH/zsh-autosuggestions/zsh-autosuggestions.zsh"
else
  cloneGitRepo "https://github.com/zsh-users/zsh-autosuggestions" "zsh-autosuggestions"
fi

# zsh-z
if isDir $ZSH_PATH/zsh-z; then
  source "$ZSH_PATH/zsh-z/zsh-z.plugin.zsh"
  autoload -U compinit && compinit # Tab completions
else
  cloneGitRepo "https://github.com/agkozak/zsh-z.git" "zsh-z"
fi

# TODO: LS_COLORS

##############################
# D1$N€Y
##############################

aws-account-list() {
  echo "886979687859 : ETech Shared Services DevTools"
  echo "125225864736 : Build & Delivery Engineering (Platform Systems Engineering-4736)"
  echo "841052471418 : ETech Shared Services Atlassian (sedevsvc)"
  echo "120533669058 : ETech Shared Services NonProd"
  echo "286174615158 : ETech Shared Services Prod"
  echo "431617356611 : Tcoe Tools - Parks"
  echo "245425841826 : Tcoe Tools - EntTech (corp)"
  echo "409768580306 : ETech Shared Services Atlassian Prod"
}

aws-sts-get-id() {
  aws-account-list | grep $(aws sts get-caller-identity | jq --raw-output '.Account')
}

# if your SAML_ROLE is different by account just add to the functions below.

# how to store password in Mac Keystore

reset_asap_password() {
  echo "run the following:"
  echo "security delete-generic-password -a $AWS_HUBID -s hubid"
  echo "security add-generic-password -a $AWS_HUBID -s hubid -w $1"
}

asap_shared_nonprod() {
  export AWS_SAML_ACCOUNT=120533669058
  unset AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN AWS_ACCESS_KEY_ID AWS_ACCESS_KEY AWS_PROFILE
  eval $(aws-saml-auth -u $AWS_HUBID -p "$(security find-generic-password -a $AWS_HUBID -s hubid -w)")
}

asap_shared_prod() {
  export AWS_SAML_ACCOUNT=286174615158
  unset AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN AWS_ACCESS_KEY_ID AWS_ACCESS_KEY AWS_PROFILE
  eval $(aws-saml-auth -u $AWS_HUBID -p "$(security find-generic-password -a $AWS_HUBID -s hubid -w)")
}

aws-account-list() {
  echo "886979687859 : ETech Shared Services DevTools"
  echo "125225864736 : Build & Delivery Engineering (Platform Systems Engineering-4736)"
  echo "841052471418 : ETech Shared Services Atlassian (sedevsvc)"
  echo "120533669058 : ETech Shared Services NonProd"
  echo "286174615158 : ETech Shared Services Prod"
  echo "431617356611 : Tcoe Tools - Parks"
  echo "245425841826 : Tcoe Tools - EntTech (corp)"
  echo "409768580306 : ETech Shared Services Atlassian Prod"
}

aws-sts-get-id() {
  aws-account-list | grep $(aws sts get-caller-identity | jq --raw-output '.Account')
}

# if your SAML_ROLE is different by account just add to the functions below.

# how to store password in Mac Keystore

reset_asap_password() {
  echo "run the following:"
  echo "security delete-generic-password -a $AWS_HUBID -s hubid"
  echo "security add-generic-password -a $AWS_HUBID -s hubid -w $1"
}

asap_shared_nonprod() {
  export AWS_SAML_ACCOUNT=120533669058
  unset AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN AWS_ACCESS_KEY_ID AWS_ACCESS_KEY AWS_PROFILE
  eval $(aws-saml-auth -u $AWS_HUBID -p "$(security find-generic-password -a $AWS_HUBID -s hubid -w)")
}

asap_shared_prod() {
  export AWS_SAML_ACCOUNT=286174615158
  unset AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN AWS_ACCESS_KEY_ID AWS_ACCESS_KEY AWS_PROFILE
  eval $(aws-saml-auth -u $AWS_HUBID -p "$(security find-generic-password -a $AWS_HUBID -s hubid -w)")
}

# To check Java Virtual Machines/JDK installed:
# /usr/libexec/java_home -V

# To switch to a specific JDK
# export JAVA_HOME=`/usr/libexec/java_home -v 1.8`
export JAVA_HOME=$(/usr/libexec/java_home -v 11)

# export SAUCE_USERNAME=xxx
# export SAUCE_ACCESS_KEY=xxx

# export decrypter_property=xxx
# export AWS_REGION=xxx

# export AWS_HUBID=xxx
# export AWS_DEFAULT_REGION=xxx
# export AWS_SAML_USER=xxx
# export AWS_SAML_ROLE=xxx

# export SERVER_SSL_KEY_STORE=xxx

# For React-Native Development with Android
export ANDROID_HOME=$HOME/Library/Android/sdk
export PATH=$PATH:$ANDROID_HOME/emulator
export PATH=$PATH:$ANDROID_HOME/tools
export PATH=$PATH:$ANDROID_HOME/tools/bin
export PATH=$PATH:$ANDROID_HOME/platform-tools

# Bun
export BUN_INSTALL="$HOME/.bun"
export PATH="$BUN_INSTALL/bin:$PATH"
