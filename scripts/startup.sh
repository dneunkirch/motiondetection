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
setup=$(printf "%s/setup.sh" ${scriptFolder})
config=$(printf "%s/configuration.sh" ${scriptFolder})
source ${setup}
source ${config}

. /lib/lsb/init-functions

PIDFILE="/var/run/motion_detection.pid"
DAEMON=$(printf "%smotion_detection.py" ${MOTION_PYTHON})
NAME="Motion-Detection"

function createSymlink {
    if [ -L ${2} ] ; then
       if [ ! -e ${2} ] ; then
         exit 1
       fi
    elif [ -e ${2} ] ; then
       exit 1
    else
       ln -s $1 $2
    fi
}

function createFolder {
    [ -d "$1" ] || mkdir -p $1
}

case "$1" in

start)
createFolder ${MOTION_TEMP}
createFolder ${MOTION_OUTPUT}
createFolder ${MOTION_FAIL}
createFolder ${MOTION_EVENT}
createFolder ${MOTION_LIVE}


webServerLink=$(printf "%s/motion" ${MOTION_WEB_ROOT})
liveFolderLink=$(printf "%slive" ${MOTION_WEB})
createSymlink ${MOTION_WEB} ${webServerLink}
createSymlink ${MOTION_LIVE} ${liveFolderLink}

chown ${MOTION_WEB_USER} ${MOTION_WEB}
chmod 777 ${MOTION_EVENT}

convertCron=$(printf "* * * * * bash  %sconvert_cron.sh > /dev/null 2>&1" ${scriptFolder})
cleanupCron=$(printf "*/2 * * * * bash  %slive_folder_cleanup.sh > /dev/null 2>&1" ${scriptFolder})

(crontab -l ; echo "$convertCron") | sort - | uniq - | crontab -
(crontab -l ; echo "$cleanupCron") | sort - | uniq - | crontab -

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