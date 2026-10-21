BIOME := npm_config_registry=https://registry.npmjs.org npx @biomejs/biome@2.5.3

.PHONY: lint fix install install-apps brew-backup brew-restore

lint:
	$(BIOME) check .

fix:
	$(BIOME) check --write .

install:
	zsh bin/install.zsh

install-apps:
	@zsh bin/install-apps.zsh

brew-backup:
	brew bundle dump --file=Brewfile --formula --cask --tap --force

brew-restore:
	brew bundle install --file=Brewfile --no-upgrade
