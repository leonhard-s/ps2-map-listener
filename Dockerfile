FROM python:3.8-slim

COPY . /listener
WORKDIR /listener

RUN python3 -m pip install -r requirements.txt
