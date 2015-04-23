# Copyright (c) The SimpleFIN Team
# See LICENSE for details.

FROM ubuntu:14.04
MAINTAINER iffy

# system deps
RUN apt-get update
RUN apt-get install -y python-dev
RUN apt-get install -y build-essential
RUN apt-get install -y python-pip
RUN apt-get install -y git
RUN apt-get install -y libsqlite3-dev
RUN apt-get install -y curl

RUN pip install -U pip

#------------------------------------------------------------------------------
# python deps
#------------------------------------------------------------------------------
WORKDIR /work
COPY requirements.txt /work/requirements.txt
RUN pip install -r /work/requirements.txt

#------------------------------------------------------------------------------
# make some encryption keys
#------------------------------------------------------------------------------
ENV USERNAME banka
COPY util/genkey.py util/genkey.py
RUN python util/genkey.py .gpghome


COPY . /work


EXPOSE 80

WORKDIR /work

CMD ["/usr/local/bin/siloscript", "--help"]
