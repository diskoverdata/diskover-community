#!/bin/sh
export TERM=xterm-256color
cd /app/diskover || exit

# check for env var for workername
[[ -z "$WORKERNAME" ]] && ARGS="" || ARGS="-n $WORKERNAME"

# start up diskoverd task daemon
python3 diskoverd.py $ARGS
