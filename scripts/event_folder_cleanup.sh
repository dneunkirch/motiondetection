#!/usr/bin/env bash

scriptFolder=$(dirname "$(readlink -f "$0")")
config=$(printf "%s/setup.sh" ${scriptFolder})

. ${config}

MIN_AGE='5' # in days

find ${MOTION_EVENT} -type f -mtime +${MIN_AGE} -exec rm {} \;
rm ${MOTION_WEB}events_*.cache