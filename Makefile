BIOME := npm_config_registry=https://registry.npmjs.org npx @biomejs/biome@2.5.3

.PHONY: lint fix install install-apps

lint:
	$(BIOME) check .

fix:
	$(BIOME) check --write .

install:
	zsh scripts/install.zsh

install-apps:
	@zsh scripts/install-apps.zsh
