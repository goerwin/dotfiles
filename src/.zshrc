# .zshrc is sourced in interactive shells. It should contain commands to set up
# aliases, functions, options, key bindings, etc.

# Path to your oh-my-zsh installation.
ZSH=$HOME/.oh-my-zsh

TEXT_EDITOR="code"
HOME_DIRS=(
  $HOME
  "/mnt/c/Users/erwin.gaitan/"
  "/mnt/c/Users/goerwin/"
)

# Set name of the theme to load.
# Look in ~/.oh-my-zsh/themes/
# Optionally, if you set this to "random", it"ll load a random theme each
# time that oh-my-zsh is loaded.
# ZSH_THEME="gallois"
# ZSH_THEME="simple"
# ZSH_THEME="avit"
# ZSH_THEME="af-magic"

# Uncomment the following line to use case-sensitive completion.
# CASE_SENSITIVE="true"

# Uncomment the following line to use hyphen-insensitive completion. Case
# sensitive completion must be off. _ and - will be interchangeable.
# HYPHEN_INSENSITIVE="true"

# Uncomment the following line to disable bi-weekly auto-update checks.
# DISABLE_AUTO_UPDATE="true"

# Uncomment the following line to change how often to auto-update (in days).
# export UPDATE_ZSH_DAYS=13

# Uncomment the following line to disable colors in ls.
# DISABLE_LS_COLORS="true"

# Uncomment the following line to disable auto-setting terminal title.
# DISABLE_AUTO_TITLE="true"

# Uncomment the following line to enable command auto-correction.
# ENABLE_CORRECTION="true"

# Uncomment the following line to display red dots whilst waiting for completion.
# COMPLETION_WAITING_DOTS="true"

# Uncomment the following line if you want to disable marking untracked files
# under VCS as dirty. This makes repository status check for large repositories
# much, much faster.
# DISABLE_UNTRACKED_FILES_DIRTY="true"

# Uncomment the following line if you want to change the command execution time
# stamp shown in the history command output.
# The optional three formats: "mm/dd/yyyy"|"dd.mm.yyyy"|"yyyy-mm-dd"
# HIST_STAMPS="mm/dd/yyyy"

# Would you like to use another custom folder than $ZSH/custom?
# ZSH_CUSTOM=/path/to/new-custom-folder

# Which plugins would you like to load? (plugins can be found in ~/.oh-my-zsh/plugins/*)
# Custom plugins may be added to ~/.oh-my-zsh/custom/plugins/
# Example format: plugins=(rails git textmate ruby lighthouse)
# Add wisely, as too many plugins slow down shell startup.
plugins=(
  git
  z
  jsontools
)

source $ZSH/oh-my-zsh.sh

# Starship
eval "$(starship init zsh)"

#//////////////////////////
# # KEY BINDINGS
#//////////////////////////

bindkey -e
bindkey "^[[1;9C" forward-word  # Ctrl + right
bindkey "^[[1;9D" backward-word # Ctrl + left
bindkey "^U" backward-kill-line # Ctrl + U
bindkey "^H" backward-kill-word # Ctrl + Backspace

zle -N customClearScreen
bindkey "^O" customClearScreen

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
unalias md
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
  echoti clear
  precmd
  zle redisplay # For ZSH Shell
}

function notes() {
  notesPath="Google Drive/Documents/notes"

  for homeDir in $HOME_DIRS; do
    [ -d "$homeDir/$notesPath" ] && $TEXT_EDITOR "$homeDir/$notesPath"
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

#//////////////////////////
# Aliases
#//////////////////////////

# Github
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
alias codezsh="$TEXT_EDITOR ~/.zshenv && $TEXT_EDITOR ~/.zshrc"

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
alias cdp="cd ~/Projects"
alias cdprojects="cd ~/Projects"
alias cdb="cd -"

# Others
alias killcam="sudo pkill "VDCAssistant""
alias sourcezsh="source ~/.zshenv && source ~/.zshrc"
alias rmf="rm -rf"
alias airport="sudo /System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport"
alias airportlswifi="airport -s"
alias cls=clear

# Youtube download youtube-dl
alias youtube="youtube-dl"
alias youtubebestaudio="youtube-dl -f bestaudio"
alias youtubebestvideo="youtube-dl -f bestvideo"
alias youtubemp3="youtube-dl -x --audio-format mp3 --audio-quality 0"
alias youtubem4a="youtube-dl -f m4a"
alias youtubemp4="youtube-dl -f mp4"
alias youtubea=youtubem4a
alias youtubev=youtubebestvideo
