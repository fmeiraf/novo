.PHONY: help publish-test build clean

VERSION := $(shell grep '^version = ' pyproject.toml | head -1 | cut -d'"' -f2)

help:
	@echo "make build         build wheel + sdist locally into dist/"
	@echo "make publish-test  push branch + tag v\$$(VERSION) to fire TestPyPI workflow"
	@echo "make clean         remove dist/"

build:
	rm -rf dist
	uv build

publish-test:
	@echo "Publishing v$(VERSION)"
	git push
	git tag v$(VERSION)
	git push origin v$(VERSION)
	@echo ""
	@echo "Tag pushed — workflow firing."
	@echo "Watch: https://github.com/fmeiraf/novo/actions"

clean:
	rm -rf dist
