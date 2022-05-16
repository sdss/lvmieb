# lvmieb

![Versions](https://img.shields.io/badge/python->3.8-blue)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Documentation Status](https://readthedocs.org/projects/lvmieb/badge/?version=latest)](https://lvmieb.readthedocs.io/en/latest/?badge=latest)
[![Test](https://github.com/sdss/lvmieb/actions/workflows/test.yml/badge.svg)](https://github.com/sdss/lvmieb/actions/workflows/test.yml)
[![Docker](https://github.com/sdss/lvmieb/actions/workflows/docker.yml/badge.svg)](https://github.com/sdss/lvmieb/actions/workflows/docker.yml)
[![codecov](https://codecov.io/gh/sdss/lvmieb/branch/main/graph/badge.svg?token=IyQglaQYSF)](https://codecov.io/gh/sdss/lvmieb)

Control software for the SDSS-V LVM (Local Volume Mapper) spectrograph Instrument Electronics Box (IEB).

## Quick Start

### Installation

`lvmieb` uses the [CLU](https://clu.readthedocs.io/en/latest/) framework and requires a RabbitMQ instance running in the background.

`lvmieb` can be installed using `pip`

```console
pip install sdss-lvmieb
```

or by cloning this repository

```console
git clone https://github.com/sdss/lvmieb
```

The preferred installation for development is using [poetry](https://python-poetry.org/)

```console
cd lvmieb
poetry install
```


### Basic ping-pong test

Start the `lvmieb` actor.

```console
lvmieb start
```

In another terminal, type `clu` and `lvmieb ping` for test.

```console
$ clu
lvmieb ping
07:41:22.636 lvmieb >
07:41:22.645 lvmieb : {
    "text": "Pong."
}
```

Stop `lvmieb` actor.

```console
lvmieb stop
```
