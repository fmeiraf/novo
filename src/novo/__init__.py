"""Novo — a terminal tool for managing experimental Python projects."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("novo")
except PackageNotFoundError:
    __version__ = "0.0.0+unknown"
