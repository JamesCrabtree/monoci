FROM jenkinsxio/builder-base:latest

COPY . /srv/service/monoci
WORKDIR /srv/service

RUN pip install --upgrade pip && \
    pip install -e monoci
