# syntax=docker/dockerfile:1.7@sha256:a57df69d0ea827fb7266491f2813635de6f17269be881f696fbfdf2d83dda33e
ARG PYTHON_IMAGE=python:3.11-slim@sha256:db3ff2e1800a8581e2c48a27c3995339d47bdf046da21c7627accd3d51053a93

FROM ${PYTHON_IMAGE} AS data-builder
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /build
RUN apt-get update \
    && apt-get install -y --no-install-recommends default-jre-headless qpdf \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --uid 65532 --gid 0 --no-create-home --shell /usr/sbin/nologin builder
COPY requirements.txt requirements-build.txt ./
RUN pip install --no-cache-dir --disable-pip-version-check -r requirements-build.txt
COPY --chown=65532:0 lib ./lib
COPY --chown=65532:0 src/__init__.py ./src/__init__.py
COPY --chown=65532:0 src/history ./src/history
COPY --chown=65532:0 scripts/audit_pdfs.py ./scripts/audit_pdfs.py
USER 65532:0
RUN --network=none python scripts/audit_pdfs.py
RUN --network=none python -m src.history.build \
    && rm -rf \
        src/history/coursereg_history/data/raw \
        src/history/coursereg_history/data/cleaned \
        src/history/vacancy_history/data/raw \
        src/history/vacancy_history/data/cleaned
COPY --chown=65532:0 src/web ./src/web
COPY --chown=65532:0 tests ./tests
RUN --network=none python -m unittest

FROM ${PYTHON_IMAGE} AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir --disable-pip-version-check -r requirements.txt \
    && useradd --uid 65532 --gid 0 --no-create-home --shell /usr/sbin/nologin app
COPY --from=data-builder --chown=65532:0 /build/lib /app/lib
COPY --from=data-builder --chown=65532:0 /build/src/__init__.py /app/src/__init__.py
COPY --from=data-builder --chown=65532:0 /build/src/history /app/src/history
COPY --from=data-builder --chown=65532:0 /build/src/web /app/src/web
USER 65532:0
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD ["python", "-c", "import socket; s=socket.socket(socket.AF_UNIX); s.settimeout(3); s.connect('/run/courserekt/http.sock'); s.sendall(b'GET /healthz HTTP/1.0\\r\\nHost: localhost\\r\\n\\r\\n'); assert b'200 OK' in s.recv(256)"]
CMD ["gunicorn", "--bind", "unix:/run/courserekt/http.sock", "--umask", "007", "--workers", "2", "--threads", "4", "--timeout", "60", "--worker-tmp-dir", "/tmp", "--access-logfile", "-", "--error-logfile", "-", "src.web.app:app"]
