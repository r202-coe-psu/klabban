FROM debian:sid

RUN echo 'deb http://mirrors.psu.ac.th/debian/ bookworm main contrib non-free' > /etc/apt/sources.list
# RUN apt update 
RUN apt update --fix-missing && apt dist-upgrade -y
RUN apt install -y python3 python3-dev python3-pip python3-venv build-essential locales npm nodejs

RUN sed -i '/th_TH.UTF-8/s/^# //g' /etc/locale.gen && locale-gen
ENV LANG th_TH.UTF-8
ENV LANGUAGE th_TH:en

WORKDIR /
RUN python3 -m venv /venv
ENV PYTHON=/venv/bin/python3
RUN $PYTHON -m pip install wheel poetry gunicorn
ENV POETRY_REQUESTS_TIMEOUT=400


WORKDIR /app
COPY klabban/cmd /app/klabban/cmd
COPY poetry.lock pyproject.toml /app/

RUN touch README.md
RUN . /venv/bin/activate && \
    poetry config virtualenvs.create false && \
    poetry install --no-interaction --only main

WORKDIR /app
COPY klabban/web/static/package.json klabban/web/static/
RUN npm install --prefix klabban/web/static

COPY . /app

RUN npm --prefix klabban/web/static run tw:minify
RUN npm install --prefix klabban/web/static
