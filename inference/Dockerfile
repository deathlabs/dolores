FROM alpine:3.23
LABEL image.authors="Victor Fernandez III, @cyberphor"
WORKDIR /home/dolores/
COPY requirements.txt requirements.txt
RUN apk add --no-cache --update python3 py3-pip &&\
    pip install --break-system-packages -r requirements.txt &&\
    addgroup -g 1000 dolores &&\
    adduser -D -G dolores -u 1000 dolores -h /home/dolores/ &&\
    mkdir /home/dolores/downloads &&\
    chown dolores:dolores /home/dolores/downloads &&\
    chmod ug+rwx,o+rx,g+s /home/dolores/downloads
COPY dolores/ dolores/
RUN chown -R dolores:dolores /home/dolores/
USER dolores
CMD [ "python", "-m", "dolores.main" ]
