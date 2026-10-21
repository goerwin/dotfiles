BIOME := npm_config_registry=https://registry.npmjs.org npx @biomejs/biome@2.5.3

.PHONY: lint fix install install-apps brew-backup install-brew install-brew-force

lint:
	$(BIOME) check .

fix:
	$(BIOME) check --write .

install:
	zsh bin/install.zsh

install-apps:
	@zsh bin/install-apps.zsh

brew-backup:
	brew bundle dump --file=src/.Brewfile --formula --cask --tap --uv --force
	install -m 644 src/.Brewfile "$(HOME)/.Brewfile"

install-brew:
	brew bundle install --file=src/.Brewfile --no-upgrade
	install -m 644 src/.Brewfile "$(HOME)/.Brewfile"

install-brew-force: install-brew
	brew bundle cleanup --file=src/.Brewfile --formula --cask --tap --uv --force
