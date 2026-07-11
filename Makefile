BIOME := npx @biomejs/biome@2.5.3

.PHONY: format check

lint:
	$(BIOME) check .

fix:
	$(BIOME) check --write .
