# .zshrc is sourced in interactive shells. It should contain commands to set up
# aliases, functions, options, key bindings, etc.

# NVM
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"                   # This loads nvm
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion" # This loads nvm bash_completion

# YARN
export PATH="$HOME/.yarn/bin:$HOME/.config/yarn/global/node_modules/.bin:$PATH"

ZSH_PATH=$HOME/.zsh
TEXT_EDITOR="code"
HOME_DIRS=(
  $HOME
  "/mnt/c/Users/erwin.gaitan/"
  "/mnt/c/Users/goerwin/"
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

# Tab completions
autoload -U compinit && compinit

#//////////////////////////
# # Key Bindings
#//////////////////////////

bindkey -e
bindkey "^[[1;9C" forward-word  # Ctrl + right
bindkey "^[[1;9D" backward-word # Ctrl + left
bindkey "^U" backward-kill-line # Ctrl + U
bindkey "^H" backward-kill-word # Ctrl + Backspace

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
  notesPath="Google Drive/Documents/notes"

  for homeDir in $HOME_DIRS; do
    isDir "$homeDir/$notesPath" && $TEXT_EDITOR "$homeDir/$notesPath"
  done
}

function open() {
  if [[ $(grep Microsoft /proc/version) ]]; then # WSL
    explorer.exe $(wslpath -w "${@:-.}")
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
alias gpom="git push origin master"
alias gpomf="git push origin master --force"
alias greset="git reset"
alias gcheckout="git checkout"
alias gch="git checkout"
alias gch.="git checkout ."
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
alias ls='ls --color=auto'
alias ll='ls -alF'

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
else
  cloneGitRepo "https://github.com/agkozak/zsh-z.git" "zsh-z"
fi
