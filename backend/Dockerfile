FROM alpine:3.23
LABEL image.authors="Victor Fernandez III, @cyberphor"
WORKDIR /home/backend/
COPY entrypoint.sh entrypoint.sh
COPY dolores/ dolores/
COPY memories/ memories/
COPY requirements.txt requirements.txt
COPY manage.py manage.py
RUN apk add --no-cache --update python3 py3-pip uvicorn &&\
    pip install --break-system-packages -r requirements.txt &&\
    adduser -D dolores -h /home/backend/ &&\
    chmod u+x /home/backend/entrypoint.sh &&\
    chown -R dolores:dolores /home/backend/
USER dolores
EXPOSE 8000
CMD [ "./entrypoint.sh" ]
