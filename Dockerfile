FROM python:3.10-slim-bullseye

MAINTAINER Jose Sanchez-Gallego, gallegoj@uw.ed
LABEL org.opencontainers.image.source https://github.com/sdss/lvmieb

WORKDIR /opt

COPY . lvmieb

RUN apt-get -y update
RUN apt-get -y install build-essential libbz2-dev

RUN pip3 install -U pip setuptools wheel
RUN cd lvmieb && pip3 install .
RUN rm -Rf lvmieb

ENTRYPOINT lvmieb actor start --debug
