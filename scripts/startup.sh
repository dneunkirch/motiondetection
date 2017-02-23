#!/usr/bin/env bash

### BEGIN INIT INFO
# Provides:          Motion Detection
# Required-Start:
# Required-Stop:
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: starts motion-detection
# Description:       starts motion-detection
### END INIT INFO

scriptFolder=$(dirname "$(readlink -f "$0")")

. /lib/lsb/init-functions

pythonFolder=$(printf "%s../python/" ${scriptFolder})

PIDFILE="/var/run/motion_detection.pid"
DAEMON=$(printf "%smotion_detection.py" ${pythonFolder})
NAME="Motion-Detection"


case "$1" in

start)
convertCron=$(printf "* * * * * bash  %sconvert_cron.sh > /dev/null 2>&1" ${scriptFolder})
cleanupEventCron=$(printf "0 6 * * * bash  %sevent_folder_cleanup.sh > /dev/null 2>&1" ${scriptFolder})

(crontab -l ; echo "$convertCron") | sort - | uniq - | crontab -
(crontab -l ; echo "$cleanupEventCron") | sort - | uniq - | crontab -

log_daemon_msg "Starting $NAME"
start-stop-daemon --user=root --start --background --pidfile ${PIDFILE} --make-pidfile --startas ${DAEMON}
log_end_msg $?
;;

stop)
log_daemon_msg "Stopping $NAME"
start-stop-daemon --stop --pidfile ${PIDFILE} --retry 10
log_end_msg $?
;;

status)
status_of_proc -p "$PIDFILE" ${DAEMON} ${NAME} && exit 0 || exit $?
;;

restart)
$0 stop
$0 start
;;

*)
echo "Usage: $0 {status|start|stop|restart}"
exit 1
esac