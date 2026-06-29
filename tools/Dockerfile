FROM alpine:3.23
LABEL image.authors="Victor Fernandez III, @cyberphor"
WORKDIR /home/dolores/
COPY requirements.txt requirements.txt
COPY dolores/ dolores/
RUN apk add --no-cache --update python3 py3-pip git &&\
    pip install --break-system-packages -r requirements.txt &&\
    addgroup -g 1000 dolores &&\
    adduser -D -G dolores -u 1000 dolores -h /home/dolores/ &&\
    mkdir -p /home/dolores/downloads &&\
    chown -R dolores:dolores /home/dolores/ &&\
    chmod ug+rwx,o+rx,g+s /home/dolores/downloads
USER dolores
EXPOSE 8002
CMD [ "python", "-m", "dolores.main" ]
