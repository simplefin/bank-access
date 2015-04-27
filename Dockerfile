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

# for lxml
RUN apt-get install -y libz-dev libxml2-dev libxslt1-dev

RUN pip install -U pip

#------------------------------------------------------------------------------
# firefox and vnc
#------------------------------------------------------------------------------
RUN apt-get update && apt-get install -y x11vnc xvfb firefox
RUN apt-get install -y xfonts-100dpi \
  xfonts-75dpi \
  xfonts-scalable \
  xfonts-cyrillic

#------------------------------------------------------------------------------
# python deps
#------------------------------------------------------------------------------
WORKDIR /work
COPY requirements.txt /work/requirements.txt
RUN pip install -r /work/requirements.txt


COPY . /work
ADD dockerutil/start.sh /home/root/start.sh

#------------------------------------------------------------------------------
# Use INSECURE, shared, globally available key
#------------------------------------------------------------------------------
RUN mv util/samplekeys .gpghome


EXPOSE 80

ENTRYPOINT ["sh", "/home/root/start.sh"]
