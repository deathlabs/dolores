FROM alpine:3.23
LABEL image.authors="Victor Fernandez III, @cyberphor"
WORKDIR /home/inference/
COPY dolores/ dolores/
COPY requirements.txt requirements.txt
RUN apk add --no-cache --update python3 py3-pip &&\
    pip install --break-system-packages -r requirements.txt &&\
    adduser -D dolores -h /home/inference/ &&\
    chown -R dolores:dolores /home/inference/
USER dolores
CMD [ "python", "-m", "dolores.main" ]
