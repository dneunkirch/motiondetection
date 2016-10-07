#!/usr/bin/env bash


scriptFolder=$(dirname "$(readlink -f "$0")")
config=$(printf "%s/setup.sh" ${scriptFolder})

. ${config}

source=$(printf "%s*_before_*.h264" ${MOTION_OUTPUT})
convertScript=$(printf "%sconvert.sh" ${scriptFolder})
pid=$(printf "%s.convert_cron.pid" ${scriptFolder})


if [ -f ${pid} ]; then
  pidId=`cat ${pid}`
  if [ -e /proc/${pidId} ]; then
    exit 0
  else
   rm ${pid}
  fi
fi
echo $$ > ${pid}
videoCount=$(find ${source} 2> /dev/null | wc -l)
if [ "$videoCount" -eq "0" ];then
    rm ${pid}
    exit 0
fi

for part1 in ${source}
do
  framerate=$(echo "$part1" | sed 's/.*_\([0-9]*\).h264/\1/')
  part2=${part1/before/after}
  bash ${convertScript} ${part1} ${part2} ${framerate}
  if [ -f ${part1} ]; then
    mv ${part1} ${MOTION_FAIL}
  fi
  if [ -f ${part2} ]; then
    mv ${part2} ${MOTION_FAIL}
  fi
done

rm ${pid}