#!/usr/bin/env bash

scriptFolder=$(dirname "$(readlink -f "$0")")
events=$(printf "%s/../python/events/" ${scriptFolder})
MIN_AGE='5' # in days

find ${events} -type f -mtime +${MIN_AGE} -exec rm {} \;
curl -X GET http://localhost:8080/reset_cache