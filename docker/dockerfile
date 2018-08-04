FROM python:3.7-alpine

ENV PYTHONUNBUFFERED 1
ENV PIP_NO_CACHE_DIR 0

RUN mkdir /sirbot
WORKDIR /sirbot

RUN apk add --update --no-cache \
    build-base \
    libffi-dev \
    libxslt-dev \
    postgresql-dev \
    git \
    && pip install pipenv \
    &&  rm -rf /var/cache/apk/*

COPY Pipfil* /sirbot/
RUN pipenv install --system --deploy --dev

COPY . /sirbot
ENTRYPOINT [ "python3", "-m", "sirbot-pyslackers" ]
