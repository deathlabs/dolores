FROM alpine:3.23
LABEL image.authors="Victor Fernandez III, @cyberphor"
WORKDIR /home/dolores/
COPY requirements.txt requirements.txt
RUN apk add --no-cache --update python3=3.12.13-r0 py3-pip=25.1.1-r1 git=2.52.0-r0 &&\
    pip install --no-cache-dir --break-system-packages -r requirements.txt &&\
    addgroup -g 1000 dolores &&\
    adduser -D -G dolores -u 1000 dolores -h /home/dolores/ &&\
    mkdir -p /home/dolores/downloads
COPY dolores/ dolores/
RUN chown -R dolores:dolores /home/dolores/ &&\
    chmod ug+rwx,o+rx,g+s /home/dolores/downloads
USER dolores
EXPOSE 8002
CMD [ "python", "-m", "dolores.main" ]
