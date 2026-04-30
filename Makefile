.PHONY: help publish-test watch build clean

help:
	@echo "make build         build wheel + sdist locally into dist/"
	@echo "make publish-test  push current branch and trigger TestPyPI workflow"
	@echo "make watch         tail the latest workflow run"
	@echo "make clean         remove dist/"

build:
	rm -rf dist
	uv build

publish-test:
	git push
	gh workflow run workflow.yml --ref main
	@echo "Triggered — 'make watch' to follow."

watch:
	@RUN_ID=$$(gh run list --workflow=workflow.yml --limit 1 --json databaseId --jq '.[0].databaseId'); \
	gh run watch $$RUN_ID

clean:
	rm -rf dist
