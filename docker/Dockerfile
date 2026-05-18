# Clean test environment for novo: git + uv on a slim Python base.
# The novo source tree is bind-mounted at /novo at run time and installed
# as an editable uv tool by entrypoint.sh, so edits flow through immediately.

FROM python:3.13-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PATH="/root/.local/bin:${PATH}" \
    TERM=xterm-256color

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
        git \
        ca-certificates \
        curl \
        less \
 && rm -rf /var/lib/apt/lists/* \
 && curl -LsSf https://astral.sh/uv/install.sh | sh

# Sensible git defaults so `seed link` and detached-mode commits work without prompts.
RUN git config --global user.email "novo-test@example.com" \
 && git config --global user.name  "novo-test" \
 && git config --global init.defaultBranch main

COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# A writable scratch dir for ad-hoc detached experiments / workspaces.
WORKDIR /workspace

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["bash"]
