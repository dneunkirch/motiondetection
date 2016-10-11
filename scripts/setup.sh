#!/usr/bin/env bash

checkoutFolder="/etc/motiondetection" # without tailing slash
webServerRoot="/var/www/html"         # without tailing slash
webServerUser="www-data"              # without tailing slash
liveFolder="/run/shm/live/"           # with tailing slash

scriptFolder=$(printf "%s/scripts/" ${checkoutFolder})
pythonFolder=$(printf "%s/python/" ${checkoutFolder})
webFolder=$(printf "%s/web/" ${checkoutFolder})
tempFolder=$(printf "%s/temp/" ${checkoutFolder})
outputFolder=$(printf "%s/output/" ${checkoutFolder})
failFolder=$(printf "%s/fail/" ${checkoutFolder})
eventFolder=$(printf "%sevents/" ${webFolder})

export MOTION_SCRIPTS=${scriptFolder}
export MOTION_PYTHON=${pythonFolder}
export MOTION_TEMP=${tempFolder}
export MOTION_OUTPUT=${outputFolder}
export MOTION_FAIL=${failFolder}
export MOTION_WEB=${webFolder}
export MOTION_EVENT=${eventFolder}
export MOTION_LIVE=${liveFolder}
export MOTION_WEB_USER=${webServerUser}
export MOTION_WEB_ROOT=${webServerRoot}