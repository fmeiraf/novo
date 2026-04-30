.PHONY: help publish-test publish build clean

VERSION := $(shell grep '^version = ' pyproject.toml | head -1 | cut -d'"' -f2)

help:
	@echo "make build         build wheel + sdist locally into dist/"
	@echo "make publish-test  push tag testpypi-v\$$(VERSION) to fire TestPyPI workflow"
	@echo "make publish       push tag v\$$(VERSION) to fire PyPI workflow (gated on approval)"
	@echo "make clean         remove dist/"

build:
	rm -rf dist
	uv build

publish-test:
	@echo "Publishing v$(VERSION) to TestPyPI"
	git push
	git tag testpypi-v$(VERSION)
	git push origin testpypi-v$(VERSION)
	@echo ""
	@echo "Tag pushed — workflow firing."
	@echo "Watch: https://github.com/fmeiraf/novo/actions"

publish:
	@echo "Publishing v$(VERSION) to PyPI"
	@echo "(workflow will pause for environment approval)"
	git push
	git tag v$(VERSION)
	git push origin v$(VERSION)
	@echo ""
	@echo "Tag pushed — approve the run at:"
	@echo "https://github.com/fmeiraf/novo/actions"

clean:
	rm -rf dist
