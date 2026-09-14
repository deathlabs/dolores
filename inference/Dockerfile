FROM alpine:3.24
LABEL image.authors="Victor Fernandez III, @cyberphor"
SHELL ["/bin/ash", "-o", "pipefail", "-c"]
WORKDIR /home/dolores/
COPY dolores/ dolores/
COPY pyproject.toml pyproject.toml
COPY uv.lock uv.lock
ENV UV_PYTHON_INSTALL_DIR=/home/dolores/.uv-python
RUN apk add --no-cache python3 uv && \
    apk upgrade --no-cache libcrypto3 libssl3 &&\
    uv sync --frozen --python /usr/bin/python3 && \
    uv run python -m pip uninstall pip -y || true &&\
    addgroup -g 1000 dolores &&\
    adduser -D -G dolores -u 1000 dolores -h /home/dolores/ &&\
    mkdir -p /home/dolores/downloads &&\
    chmod ug+rwx,o+rx,g+s /home/dolores/downloads &&\
    chown -R dolores:dolores /home/dolores/
ENV PATH="/home/dolores/.venv/bin:$PATH"
USER dolores
CMD [ "python", "-m", "dolores.main" ]
