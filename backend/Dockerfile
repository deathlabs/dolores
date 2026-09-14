FROM alpine:3.24
LABEL image.authors="Victor Fernandez III, @cyberphor"
SHELL ["/bin/ash", "-o", "pipefail", "-c"]
WORKDIR /home/backend/
COPY checkpoints/ checkpoints/
COPY entrypoint.sh entrypoint.sh
COPY dolores/ dolores/
COPY memories/ memories/
COPY pyproject.toml pyproject.toml
COPY uv.lock uv.lock
COPY manage.py manage.py
ENV UV_PYTHON_INSTALL_DIR=/home/backend/.uv-python
RUN apk add --no-cache python3 uv && \
    apk upgrade --no-cache libcrypto3 libssl3 &&\
    uv sync --frozen --python /usr/bin/python3 && \
    uv run python -m pip uninstall pip -y || true &&\
    (apk del wget || true) &&\
    adduser -D dolores -h /home/backend/ &&\
    chmod u+x /home/backend/entrypoint.sh &&\
    chown -R dolores:dolores /home/backend/
ENV PATH="/home/backend/.venv/bin:$PATH"
USER dolores
EXPOSE 8000
CMD [ "./entrypoint.sh" ]
