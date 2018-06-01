FROM python:3.6-alpine

RUN apk add gcc python3-dev libc-dev libffi-dev openssl-dev --update
COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 8000/tcp

ENV XBOX_IP 127.0.0.1
ENV XBOX_LIVEID FD00000000000000

COPY app.py ./

CMD [ "python", "-u", "./app.py" ]
