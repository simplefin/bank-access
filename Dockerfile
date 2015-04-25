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
# nodejs
#------------------------------------------------------------------------------
WORKDIR /tmp/node
RUN curl -o node.tar.gz http://nodejs.org/dist/v0.12.2/node-v0.12.2.tar.gz && \
    ls && \
    tar xf node.tar.gz && \
    cd node-* && \
    ./configure && make && make install && \
    cd /tmp && rm -rf /tmp/node


#------------------------------------------------------------------------------
# nodejs deps
#------------------------------------------------------------------------------
WORKDIR /work
COPY package.json /work/package.json
RUN npm install

#------------------------------------------------------------------------------
# python deps
#------------------------------------------------------------------------------
COPY requirements.txt /work/requirements.txt
RUN pip install -r /work/requirements.txt

COPY . /work

EXPOSE 80

RUN apt-get clean
RUN rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

CMD ["/usr/local/bin/siloscript", "--help"]
