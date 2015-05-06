# Copyright (c) The SimpleFIN Team
# See LICENSE for details.

FROM ubuntu:14.04
MAINTAINER iffy

# system deps
RUN apt-get update
RUN apt-get install -y python-dev
RUN apt-get install -y build-essential
RUN apt-get install -y python-pip
RUN pip install -U pip
RUN pip install ansible

# Manually maintained copy of dependencies in install/makeworker.yml just to
# make caching better
RUN apt-get install -y git
RUN apt-get install -y libsqlite3-dev
RUN apt-get install -y curl
RUN apt-get install -y libz-dev
RUN apt-get install -y libxml2-dev
RUN apt-get install -y libxslt1-dev
RUN apt-get install -y x11vnc
RUN apt-get install -y xvfb
RUN apt-get install -y firefox
RUN apt-get install -y xfonts-100dpi
RUN apt-get install -y xfonts-75dpi
RUN apt-get install -y xfonts-scalable
RUN apt-get install -y xfonts-cyrillic

WORKDIR /work
COPY . /work
RUN ansible-playbook -i dockerutil/inventory -c local --extra-vars "worker_user=root worker_virtualenv= banka_path=/work" -vvvv install/localinstall.yml


ADD dockerutil/start.sh /home/root/start.sh

#------------------------------------------------------------------------------
# Use INSECURE, shared, globally available key
#------------------------------------------------------------------------------
RUN mv util/samplekeys .gpghome

EXPOSE 80

ENTRYPOINT ["sh", "/home/root/start.sh"]
