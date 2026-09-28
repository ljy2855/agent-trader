FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    MULTICA_BIN=/usr/local/bin/multica

# Pin the multica CLI version. Bump in lockstep with the release the operator's
# scheduled tasks run on macOS so mock/live behaviour stays consistent across
# hosts. Override at build time via `--build-arg MULTICA_VERSION=...`.
ARG MULTICA_VERSION=0.4.9

WORKDIR /app

# multica CLI Linux binary (Go binary — no glibc surprises). We install
# ca-certificates + curl just for the download, then drop curl to keep the
# runtime image lean. The watcher uses MULTICA_BIN to locate this binary.
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl \
    && curl -fsSL \
        "https://github.com/multica-ai/multica/releases/download/v${MULTICA_VERSION}/multica_linux_amd64.tar.gz" \
        -o /tmp/multica.tar.gz \
    && tar -xzf /tmp/multica.tar.gz -C /tmp multica \
    && install -m 0755 /tmp/multica /usr/local/bin/multica \
    && rm -f /tmp/multica.tar.gz /tmp/multica \
    && apt-get purge -y curl \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

# Dependencies come from uv.lock — the same versions the test suite runs on.
# Until 2026-09-27 this was a bare `pip install .` against open ranges, so each
# build took whatever PyPI had that day: tests ran fastmcp 2.12.4 while the
# image ran 4.x, and a 2.x-only call crashed the MCP pod on deploy. Layered
# before the source so a code-only change reuses the dependency layer.
ARG UV_VERSION=0.6.3
COPY pyproject.toml uv.lock README.md ./
RUN pip install --upgrade pip "uv==${UV_VERSION}" \
    && uv export --frozen --no-dev --no-emit-project --format requirements-txt -o /tmp/requirements.txt \
    && pip install -r /tmp/requirements.txt \
    && pip uninstall -y uv \
    && rm -f /tmp/requirements.txt

COPY main.py main_http.py main_dashboard.py main_watcher.py ./
COPY src ./src
COPY automation ./automation

# The project itself only; every dependency is already pinned above.
RUN pip install --no-deps .

EXPOSE 8000

CMD ["python", "main_http.py"]
