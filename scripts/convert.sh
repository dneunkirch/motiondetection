#!/usr/bin/env bash


eventPart1=$1
eventPart2=$2
framerate=$3

scriptFolder=$(dirname "$(readlink -f "$0")")
config=$(printf "%s/setup.sh" ${scriptFolder})

. ${config}

dateString=`date -r ${eventPart1} +%Y-%m-%d_%H-%M-%S`
video=$(printf "%s%s.mp4" ${MOTION_TEMP} ${dateString})
timestamp=$(date +%s%N)
cacheFiles=$(printf "%sevents_*.cache" ${MOTION_WEB})
previewImage=$(printf "%s%s.jpg" ${MOTION_TEMP} ${timestamp})
previewImageX320=$(printf "%s%s_320x180.jpg" ${MOTION_EVENT} ${dateString})
previewImageX640=$(printf "%s%s_640x360.jpg" ${MOTION_EVENT} ${dateString})

if [ -s ${eventPart1} ]
then
    MP4Box -fps ${framerate} -cat ${eventPart1} -cat ${eventPart2} -new ${video}
else
    MP4Box -fps ${framerate} -cat ${eventPart2} -new ${video}
fi

avconv -i ${eventPart2} -frames:v 1 ${previewImage}
convert ${previewImage} -resize 640x360 -quality 70 ${previewImageX640}
convert ${previewImage} -resize 320x180 -quality 70 ${previewImageX320}

duration=$(avconv -i ${video} 2>&1 |  grep "Duration"| cut -d ' ' -f 4 | sed s/,// | sed 's@\..*@@g' | awk '{ split($1, A, ":"); split(A[3], B, "."); print 3600*A[1] + 60*A[2] + B[1] }')
target=$(printf "%s%s_%s.mp4" ${MOTION_EVENT} ${dateString} ${duration})

mv ${video} ${target}
if [ -f ${target} ]
then
    rm ${eventPart1}
    rm ${eventPart2}
    rm ${previewImage}
    chown ${MOTION_WEB_USER} ${target}
    chown ${MOTION_WEB_USER} ${previewImageX320}
    chown ${MOTION_WEB_USER} ${previewImageX640}
fi

rm ${cacheFiles}