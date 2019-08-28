FROM python:3.6-alpine
LABEL maintainer="Ocean Protocol <devops@oceanprotocol.com>"

ARG VERSION

RUN apk add --no-cache --update\
    bash \
    build-base \
    gcc \
    gettext\
    gmp \
    gmp-dev \
    libffi-dev \
    openssl-dev \
    py-pip \
    python3 \
    python3-dev \
  && pip install virtualenv

COPY . /ocean_events_handler
WORKDIR /ocean_events_handler

RUN pip install .

# config.ini configuration file variables
ENV KEEPER_URL='http://127.0.0.1:8545'
ENV PARITY_URL='http://127.0.0.1:8545'
ENV SECRET_STORE_URL='http://127.0.0.1:12001'
ENV PARITY_ADDRESS=''
ENV PARITY_PASSWORD=''
ENV PARITY_KEYFILE=''

ENTRYPOINT ["/ocean_events_handler/docker-entrypoint.sh"]
