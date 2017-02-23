#!/usr/bin/env bash


scriptFolder=$(dirname "$(readlink -f "$0")")
unconvertedFolder=$(printf "%s/../python/unconverted/" ${scriptFolder})
failFolder=$(printf "%s/../python/unconverted_fail/" ${scriptFolder})

source=$(printf "%s*_before_*.h264" ${unconvertedFolder})
convertScript=$(printf "%s/convert.sh" ${scriptFolder})
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
    mv ${part1} ${failFolder}
  fi
  if [ -f ${part2} ]; then
    mv ${part2} ${failFolder}
  fi
done

rm ${pid}

# TODO check for unconverted videos