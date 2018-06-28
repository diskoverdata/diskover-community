#!/bin/bash
# optimizes elasticsearch diskover indices
# https://github.com/shirosaidev/diskover
#
# Copyright (C) Chris Park 2017-2018
# diskover is released under the Apache 2.0 license. See
# LICENSE for the full license text.
#
HOST=$1
USER=$2
PASSWORD=$3
CURL_BIN=$(which curl)
if [ -z "$HOST" ]; then
  echo "Host is missing"
  exit 1
fi
if [ -z "$CURL_BIN" ]; then
  echo "Curl binary is missing"
  exit 1
fi
for indice in $(${CURL_BIN} -XGET http://${HOST}:9200/_cat/indices | sort -rk 7 | awk '{print $3}' | grep 'diskover'); do
  if [ ! -z "$indice" ]; then
    echo $(date +"%Y%m%d %H:%M") Processing indice ${indice}
    if [ ! -z "$USER" ]; then
      ${CURL_BIN} -u ${USER}:${PASSWORD} -XPOST http://${HOST}:9200/${indice}/_forcemerge?max_num_segments=1
    else
      ${CURL_BIN} -XPOST http://${HOST}:9200/${indice}/_forcemerge?max_num_segments=1
    fi
    echo
  fi
done
exit 0