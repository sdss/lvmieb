# lvmieb

![Versions](https://img.shields.io/badge/python->3.7-blue)
[![Documentation Status](https://readthedocs.org/projects/lvmieb/badge/?version=latest)](https://lvmieb.readthedocs.io/en/latest/?badge=latest)
[![Travis (.org)](https://img.shields.io/travis/sdss/lvmieb)](https://travis-ci.org/sdss/lvmieb)
[![codecov](https://codecov.io/gh/sdss/lvmieb/branch/master/graph/badge.svg?token=IyQglaQYSF)](https://codecov.io/gh/sdss/lvmieb)

SDSS-V LVM(Local Volume Mapper) IEB(Integrated Electronics Box) control software for the Spectrograpgh

## Quick Start

### Prerequisite

Install [CLU](https://clu.readthedocs.io/en/latest/) by using PyPI.
```
$ pip install sdss-clu
```

Install [RabbitMQ](https://www.rabbitmq.com/) by using apt-get.

```
$ sudo apt-get install -y erlang
$ sudo apt-get install -y rabbitmq-server
$ sudo systemctl enable rabbitmq-server
$ sudo systemctl start rabbitmq-server
```

Install [pyenv](https://github.com/pyenv/pyenv) by using [pyenv installer](https://github.com/pyenv/pyenv-installer).

```
$ curl https://pyenv.run | bash
```

You should add the code below to `~/.bashrc` by using your preferred editor.
```
# pyenv
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"
eval "$(pyenv init --path)"
eval "$(pyenv virtualenv-init -)"
```

### Ping-pong test

Clone this repository.
```
$ git clone https://github.com/sdss/lvmieb
$ cd lvmieb
```

Set the python 3.9.1 virtual environment.
```
$ pyenv install 3.9.1
$ pyenv virtualenv 3.9.1 lvmieb-with-3.9.1
$ pyenv local lvmieb-with-3.9.1
```

Install [poetry](https://python-poetry.org/) and dependencies. For more information, check [sdss/archon](https://github.com/sdss/archon).
```
$ pip install poetry
$ python create_setup.py
$ pip install -e .
```

Start `lvmieb` actor.
```
$ lvmieb start
```

In another terminal, type `clu` and `lvmieb ping` for test.
```
$ clu
lvmieb ping
07:41:22.636 lvmieb > 
07:41:22.645 lvmieb : {
    "text": "Pong."
}
```

Stop `lvmieb` actor.
```
$ lvmieb stop
```
