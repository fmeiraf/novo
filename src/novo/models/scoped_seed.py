"""ScopedSeed: a seed paired with the scope it was discovered in."""

from typing import Literal

from pydantic import BaseModel

from novo.models.seed import Seed

Scope = Literal["local", "user", "remote", "builtin"]

VALID_SCOPES: tuple[Scope, ...] = ("local", "user", "remote", "builtin")


class ScopedSeed(BaseModel):
    """A seed plus the scope it was discovered in.

    `scope` is one of: local (workspace `.novo/seeds/`), user
    (`~/.local/share/novo/seeds/`), remote (`~/.local/share/novo/remotes/<n>/<seed>/`),
    or builtin (bundled with the package). For `remote`, `remote` carries the
    remote name; for all other scopes it is None.
    """

    seed: Seed
    scope: Scope
    remote: str | None = None

    @property
    def identifier(self) -> str:
        """Canonical scoped identifier (e.g. `user:default`, `remote:team/etl`)."""
        if self.scope == "remote":
            return f"remote:{self.remote}/{self.seed.name}"
        return f"{self.scope}:{self.seed.name}"


def parse_seed_identifier(raw: str) -> tuple[Scope | None, str | None, str]:
    """Parse a seed identifier string.

    Forms accepted:
        "foo"              -> (None, None, "foo")           # implicit, needs resolution
        "local:foo"        -> ("local", None, "foo")
        "user:foo"         -> ("user", None, "foo")
        "builtin:foo"      -> ("builtin", None, "foo")
        "remote:team/foo"  -> ("remote", "team", "foo")

    Raises ValueError for malformed inputs (empty, bad scope, bad remote shape).
    """
    if not raw or raw.strip() != raw:
        raise ValueError(f"invalid seed identifier: {raw!r}")

    if ":" not in raw:
        return None, None, raw

    scope_part, _, rest = raw.partition(":")
    if scope_part not in VALID_SCOPES:
        raise ValueError(
            f"unknown seed scope {scope_part!r} in {raw!r}; "
            f"expected one of {', '.join(VALID_SCOPES)}"
        )
    if not rest:
        raise ValueError(f"missing seed name after scope in {raw!r}")

    if scope_part == "remote":
        if "/" not in rest:
            raise ValueError(
                f"remote seed identifier must be 'remote:<name>/<seed>', got {raw!r}"
            )
        remote_name, _, seed_name = rest.partition("/")
        if not remote_name or not seed_name:
            raise ValueError(f"invalid remote seed identifier: {raw!r}")
        return "remote", remote_name, seed_name

    return scope_part, None, rest  # type: ignore[return-value]
