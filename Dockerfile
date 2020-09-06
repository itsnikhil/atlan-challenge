FROM python:3.6.8
ENV PYTHONBUFFERED 1
RUN mkdir /atlan_challenge
WORKDIR /atlan_challenge
COPY requirements.txt /atlan_challenge/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
COPY . /atlan_challenge/