#!/bin/bash
# diskover bot launcher multi-processing script
# starts multiple bots to help with diskover redis queue
# https://github.com/shirosaidev/diskover
#
# Copyright (C) Chris Park 2017
# diskover is released under the Apache 2.0 license. See
# LICENSE for the full license text.
#

############# EDIT BELOW FOR YOUR ENVIRONMENT #############

# paths and default config values below
PYTHON=python # path to python command or python if in PATH
DISKOVERBOT=./diskover_worker_bot.py # path to diskover_worker_bot.py
# number of bots to start (cores x 2 might be good start)
WORKERBOTS=8
# run bots in burst mode (quit when all jobs done)
BURST=FALSE
# run bots with more output
VERBOSE=FALSE
# run bots with less output
QUIET=FALSE
# bot log file directory and file prefix
# logs will be named BOTLOG_timestamp
BOTLOG=/tmp/diskover_bot_log
# file to store bot pids
BOTPIDS=/tmp/diskover_bot_pids

###########################################################


VERSION="1.0"

function printhelp {
    echo "Usage: $(basename $0) [OPTION] [ROOTDIR]"
    echo
    echo "Options:"
    echo
    echo "  -w n    number of worker bots to start (default $WORKERBOTS)"
    echo "  -b      burst mode (bots quit when no more jobs"
    echo "  -v      more output (verbose)"
    echo "  -q      less output (quiet)"
    echo "  -k      kill all bots"
    echo "  -s      show all bots running"
    echo "  -V      displays version and exits"
    echo "  -h      displays this help message and exits"
    echo
    echo "diskover worker bot process launcher v$VERSION"
    echo
    echo "Adjust default paths and settings at top of script"
    exit 1
}

KILLBOTS=FALSE
SHOWBOTS=FALSE
while getopts :h?w:bvqskV opt; do
    case "$opt" in
    h) printhelp; exit 0;;
    w) WORKERBOTS=$OPTARG;;
    b) BURST=TRUE;;
    v) VERBOSE=TRUE;;
    q) QUIET=TRUE;;
    s) SHOWBOTS=TRUE;;
    k) KILLBOTS=TRUE;;
    V) echo "$0 v$VERSION"; exit 0;;
    ?) echo "Invalid option ${OPTARG}, use -h for help" >&2; exit 1;;
    esac
done

function banner {
  echo "$(tput setaf 1)

  ________  .__        __
  \\______ \\ |__| _____|  | _________  __ ___________
   |    |  \\|  |/  ___/  |/ /  _ \\  \\/ // __ \\_  __ \\ /)___(\\
   |    \`   \\  |\\___ \\|    <  <_> )   /\\  ___/|  | \\/ (='.'=)
  /_______  /__/____  >__|_ \\____/ \\_/  \\___  >__|   (\"\)_(\"\)
          \\/        \\/     \\/               \\/
                worker bot launcher v$VERSION
                https://github.com/shirosaidev/diskover
                \"Crawling all your stuff, core melting time\"$(tput sgr 0)

"
}

function startbots {
	echo "starting $WORKERBOTS worker bots in background..."
    ARGS=""
    if [ $BURST == TRUE ]; then
        ARGS+=" -b "
    fi
    if [ $VERBOSE == TRUE ]; then
        ARGS+=" -v "
    fi
    if [ $QUIET == TRUE ]; then
        ARGS+=" -q "
    fi
    for (( i = 1; i <= $WORKERBOTS; i++ )); do
        $PYTHON $DISKOVERBOT $ARGS > ${BOTLOG}_${i}_$(date +%H:%M:%S) 2>&1 &
        echo "$(hostname -s).$! (pid $!)"
        echo "$!" >> $BOTPIDS
    done

    echo "DONE!"
}

banner

if [ $KILLBOTS == TRUE ]; then
    echo "killing worker bot pids:"
    for i in `cat $BOTPIDS`; do
        echo "$i"
        kill $i
    done
    echo "all worker bots have been sent shutdown command"
    rm $BOTPIDS
elif [ $SHOWBOTS == TRUE ]; then
    if [ -f $BOTPIDS ]; then
        echo "running worker bots:"
        for i in `cat $BOTPIDS`; do
            echo "$(hostname -s).$i (pid $i)"
        done
    else
        echo "no worker bots running"
    fi
else
    startbots
    echo "all worker bots have started, logging to $BOTLOG"
    echo "worker pids have been stored in $BOTPIDS, use -k flag to shutdown workers"
    echo "exiting, sayonara!"
fi
