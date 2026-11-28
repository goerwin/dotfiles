BIOME := npm_config_registry=https://registry.npmjs.org npx @biomejs/biome@2.5.3
UPDATE_FLAG := $(if $(NO_UPDATE),--no-update)

.PHONY: lint fix build-skills install-skills install install-apps save-brew install-brew install-brew-force

lint:
	$(BIOME) check .

build-skills:
	node lib/build-skills.mjs

fix:
	$(BIOME) check --write .

install:
	zsh bin/install.zsh $(UPDATE_FLAG)

install-apps:
	@zsh bin/install-apps.zsh $(UPDATE_FLAG) "$(APP)" "$(PLATFORM)"

save-brew:
	@./bin/save-brew.zsh

install-brew:
	@./bin/install-brew.zsh

install-brew-force:
	@./bin/install-brew-force.zsh

install-skills:
	zsh bin/install-skills.zsh $(UPDATE_FLAG)
