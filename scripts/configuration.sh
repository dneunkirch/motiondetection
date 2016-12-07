#!/usr/bin/env bash

export MOTION_SCORE_DAY=0.4
export MOTION_SCORE_NIGHT=1

export MOTION_CAMERA_ROTATION=0
export MOTION_CAMERA_SATURATION=20
export MOTION_CAMERA_SHARPNESS=20

export MOTION_NIGHT_MODE_ALLOWED="True"
export MOTION_LOCATION_LATITUDE="37.263056"
export MOTION_LOCATION_LONGITUDE="-115.79302"

export MOTION_LIVE_REFRESH_INTERVAL_SECONDS=5

scriptFolder=$(dirname "$(readlink -f "$0")")
localConfig=$(printf "%s/local_configuration.sh" ${scriptFolder})

if [ -f ${localConfig} ]
then
    source ${localConfig}
fi