FROM docker.io/library/python:3.12-slim

ADD . /app

WORKDIR /app

RUN pip install -r /app/requirements.txt --no-cache-dir

CMD ["/bin/bash", "entrypoint.sh"]