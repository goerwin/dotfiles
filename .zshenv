# .zshenv is sourced on all invocations of the shell (interactive and non interactive like cron),
# unless the -f option is set. It should contain commands to set the command search path,
# plus other important environment variables. .zshenv should not contain commands that produce
# output or assume the shell is attached to a tty.

# PATH
export PATH="$HOME/.rvm/bin:$PATH" # Add RVM to PATH for scripting
export PATH="/usr/local/bin:$PATH" # For Homebrew

# NVM
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"  # This loads nvm
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"  # This loads nvm bash_completion

# YARN
export PATH="$HOME/.yarn/bin:$HOME/.config/yarn/global/node_modules/.bin:$PATH"

# Less reader
#   - F = exit if output fits one screen
#   - M show file info at the bottom let
#   - N = show number
export LESS=-RFXMN
