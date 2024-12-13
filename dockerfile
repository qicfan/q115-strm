FROM python:3.12-slim
EXPOSE 12123
WORKDIR /app

ENV PATH=/app:$PATH

RUN cp /etc/apt/sources.list.d/debian.sources /etc/apt/sources.list.d/debian.sources.bak \
  && sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources
RUN apt update && apt install -y git nginx cron

COPY . .
RUN chmod -R 0755 /app/frontend/*

RUN cp /app/docker/q115strm.conf /etc/nginx/conf.d/q115strm.conf && \
    pip install -r requirements.txt

VOLUME ["/app/data", "/115", "/CloudNAS/115"]

ENTRYPOINT ["/bin/bash", "./start.sh"]