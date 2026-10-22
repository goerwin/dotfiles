BIOME := npm_config_registry=https://registry.npmjs.org npx @biomejs/biome@2.5.3

.PHONY: lint fix install install-apps brew-backup install-brew install-brew-force

lint:
	$(BIOME) check .

fix:
	$(BIOME) check --write .

install:
	zsh bin/install.zsh

install-apps:
	@zsh bin/install-apps.zsh "$(APP)"

brew-backup:
	@./bin/brew-backup.zsh

install-brew:
	@./bin/install-brew.zsh

install-brew-force:
	@./bin/install-brew-force.zsh
