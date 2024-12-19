FROM python:3.12-slim
EXPOSE 12123
WORKDIR /app

ENV PATH=/app:$PATH
ENV TZ="Asia/Shanghai"

# RUN cp /etc/apt/sources.list.d/debian.sources /etc/apt/sources.list.d/debian.sources.bak \
#   && sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources
RUN apt update && apt install -y git cron

COPY . .
RUN chmod -R 0755 /app/frontend/*

RUN pip install -r requirements.txt

VOLUME ["/app/data"]

ENTRYPOINT ["python", "main.py"]