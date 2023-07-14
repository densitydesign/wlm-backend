FROM python:3.9.10-slim
ENV PYTHONUNBUFFERED 1

RUN apt-get update && apt-get install -y cron gdal-bin python3-pip libpq-dev libpango-1.0-0 libharfbuzz0b libpangoft2-1.0-0 libffi-dev libjpeg-dev libopenjp2-7-dev

ADD requirements.txt /code/
ADD requirements_prod.txt /code/

WORKDIR /code
RUN pip install -r requirements.txt -r requirements_prod.txt
ADD ./wlm /code/wlm

ADD scripts /scripts/
RUN mkdir /logs

ENV PATH="/scripts:${PATH}"
WORKDIR /code/wlm


