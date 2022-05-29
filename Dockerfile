FROM ubuntu:20.04

LABEL maintainer="changgonkim@khu.ac.kr"

WORKDIR /opt

COPY . lvmieb

RUN apt-get -y update
RUN apt-get -y install build-essential libbz2-dev

# Install Python 3.9
RUN apt-get install -y software-properties-common
RUN add-apt-repository ppa:deadsnakes/ppa
RUN apt-get install -y python3.9 python3-pip


RUN pip3 install -U pip setuptools wheel
RUN cd lvmieb && pip3 install .

# Connect repo to package
LABEL org.opencontainers.image.source https://github.com/sdss/lvmieb

ENTRYPOINT lvmieb actor start --debug
