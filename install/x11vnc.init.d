X11VNC=/usr/bin/x11vnc
X11VNCARGS="-passwd secret -display :99 -N -forever"
PIDFILE=/var/run/x11vnc.pid
case "$1" in
  start)
    echo -n "Starting x11vnc"
    start-stop-daemon --start --quiet --pidfile $PIDFILE --make-pidfile --background --exec $X11VNC -- $X11VNCARGS
    echo "."
    ;;
  stop)
    echo -n "Stopping x11vnc"
    start-stop-daemon --stop --quiet --pidfile $PIDFILE
    echo "."
    ;;
  restart)
    $0 stop
    $0 start
    ;;
  *)
        echo "Usage: /etc/init.d/x11vnc {start|stop|restart}"
        exit 1
esac
 
exit 0
