FROM alpine:3.23
LABEL image.authors="Victor Fernandez III, @cyberphor"
WORKDIR /home/tools/
COPY requirements.txt requirements.txt
COPY dolores/ dolores/
RUN apk add --no-cache --update python3 py3-pip &&\
    pip install --break-system-packages -r requirements.txt &&\
    adduser -D dolores -h /home/tools/ &&\
    chown -R dolores:dolores /home/tools/
USER dolores
EXPOSE 8002
CMD [ "python", "-m", "dolores.main" ]
