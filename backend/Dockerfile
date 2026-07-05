FROM alpine:3.23
LABEL image.authors="Victor Fernandez III, @cyberphor"
WORKDIR /home/dolores/
COPY checkpoints/ checkpoints/
COPY dolores/ dolores/
COPY entrypoint.sh entrypoint.sh
COPY memories/ memories/
COPY requirements.txt requirements.txt
COPY manage.py manage.py
RUN apk add --no-cache --update python3 py3-pip uvicorn=0.38.0-r0 &&\
    pip install --no-cache-dir --break-system-packages -r requirements.txt &&\
    adduser -D dolores -h /home/dolores/ &&\
    chmod u+x /home/dolores/entrypoint.sh &&\
    chown -R dolores:dolores /home/dolores/
USER dolores
EXPOSE 8000
CMD [ "./entrypoint.sh" ]
