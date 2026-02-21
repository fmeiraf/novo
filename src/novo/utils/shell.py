"""Shell function generator for `novo open`."""

SHELL_FUNCTION = r"""
# novo shell integration
novo() {
    if [ "$1" = "open" ] && [ -n "$2" ]; then
        local target
        target="$(command novo _open-path "$2" 2>/dev/null)"
        if [ -n "$target" ] && [ -d "$target" ]; then
            cd "$target" || return 1
        else
            command novo "$@"
        fi
    else
        command novo "$@"
    fi
}
""".strip()


def get_shell_init() -> str:
    """Return the shell function for `novo open` integration."""
    return SHELL_FUNCTION
