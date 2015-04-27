# Copyright (c) The SimpleFIN Team
# See LICENSE for details.
set -e
export DISPLAY=:99
mkdir ~/.vnc
x11vnc -storepasswd secret ~/.vnc/passwd >> /var/log/vnc.log 2>> /var/log/vnc.log
Xvfb :99 -shmem -screen 0 1024x768x16 >> /var/log/vnc.log 2>> /var/log/vnc.log &
x11vnc -passwd secret -display :99 -N -forever >> /var/log/vnc.log 2>> /var/log/vnc.log &
exec "$@"