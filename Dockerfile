FROM python:3.11-slim as build
RUN apt-get update
RUN apt-get install -y --no-install-recommends \
    build-essential gcc libpcre3 libpcre3-dev

WORKDIR /usr/app

RUN python -m venv /usr/app/venv
ENV PATH="/usr/app/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install -r requirements.txt

# --- multistage build
FROM python:3.9-slim
ENV PATH="/usr/app/venv/bin:$PATH"

RUN useradd uwsgi
WORKDIR /usr/app

COPY --from=build /usr/app/venv ./venv
COPY . .

EXPOSE 8000

CMD [ "uwsgi", "--master", "--enable-threads", "--thunder-lock", "--single-interpreter", \
    "--http", ":8000", "--module", "project.wsgi", "--uid", "uwsgi" ]