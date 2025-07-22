FROM docker.io/library/python:3.12-slim

ADD . /app

WORKDIR /app

RUN pip install --upgrade pip -i https://mirrors.aliyun.com/pypi/simple/ && \
    pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/

CMD ["/bin/bash", "entrypoint.sh"]