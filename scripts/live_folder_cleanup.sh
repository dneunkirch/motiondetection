#!/usr/bin/env bash


scriptFolder=$(dirname "$(readlink -f "$0")")
config=$(printf "%s/setup.sh" ${scriptFolder})

. ${config}

MIN_AGE='2'

find ${MOTION_LIVE} -name '*.jpg' -type f -mmin +${MIN_AGE} -exec rm {} \;