BIOME := npm_config_registry=https://registry.npmjs.org npx @biomejs/biome@2.5.3
UPDATE_FLAG := $(if $(NO_UPDATE),--no-update)

.PHONY: lint fix test-skills install-skills install install-apps brew-backup install-brew install-brew-force

lint:
	$(BIOME) check .

fix:
	$(BIOME) check --write .

install:
	zsh bin/install.zsh $(UPDATE_FLAG)

install-apps:
	@zsh bin/install-apps.zsh $(UPDATE_FLAG) "$(APP)"

brew-backup:
	@./bin/brew-backup.zsh

install-brew:
	@./bin/install-brew.zsh

install-brew-force:
	@./bin/install-brew-force.zsh

test-skills:
	for tests in src/.agents/shared/tests src/.agents/skills/*/tests; do \
		PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s "$$tests" -v || exit 1; \
	done

install-skills:
	zsh bin/install-skills.zsh $(UPDATE_FLAG)
