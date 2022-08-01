FROM python:3.9.10-slim
ENV PYTHONUNBUFFERED 1

RUN apt-get update && apt-get install -y gdal-bin python3-pip libpango-1.0-0 libharfbuzz0b libpangoft2-1.0-0 libffi-dev libjpeg-dev libopenjp2-7-dev

ADD requirements.txt /code/
ADD requirements_prod.txt /code/

WORKDIR /code
RUN pip install -r requirements.txt -r requirements_prod.txt
ADD ./wlm /code/wlm

WORKDIR /code/wlm