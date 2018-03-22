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

# path to python command or python if in PATH
PYTHON=python
# path to diskover_worker_bot.py
DISKOVERBOT=./diskover_worker_bot.py
# number of bots to start (cores x 2 might be good start)
WORKERBOTS=8
# run bots in burst mode (quit when all jobs done)
BURST=FALSE
# file to store bot pids
BOTPIDS=/tmp/diskover_bot_pids

###########################################################


VERSION="1.1"

function printhelp {
    echo "Usage: $(basename $0) [OPTION] [ROOTDIR]"
    echo
    echo "Options:"
    echo
    echo "  -w n    number of worker bots to start (default $WORKERBOTS)"
    echo "  -b      burst mode (bots quit when no more jobs)"
    echo "  -s      show all bots running"
    echo "  -k      kill all bots"
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
while getopts :h?w:bskV opt; do
    case "$opt" in
    h) printhelp; exit 0;;
    w) WORKERBOTS=$OPTARG;;
    b) BURST=TRUE;;
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
                Worker Bot Launcher v$VERSION
                https://github.com/shirosaidev/diskover
                \"Crawling all your stuff, core melting time\"$(tput sgr 0)

"
}

function startbots {
	echo "Starting $WORKERBOTS worker bots in background..."
    ARGS=""
    if [ $BURST == TRUE ]; then
        ARGS+="-b"
    fi
    for (( i = 1; i <= $WORKERBOTS; i++ )); do
        $PYTHON $DISKOVERBOT $ARGS > /dev/null 2>&1 &
        echo "$(hostname -s).$! (pid $!)"
        echo "$!" >> $BOTPIDS
    done

    echo "DONE!"
}

banner

if [ $KILLBOTS == TRUE ]; then
    if [ -f $BOTPIDS ]; then
        echo "Killing worker bot pids:"
        for PID in `cat $BOTPIDS`; do
            echo "$PID"
            if `ps -p $PID > /dev/null 2>&1`; then
                kill $PID
            fi
        done
        echo "All worker bots have been sent shutdown command"
        rm $BOTPIDS
    else
        echo "No worker bots running or pid file can't be found"
    fi
elif [ $SHOWBOTS == TRUE ]; then
    if [ -f $BOTPIDS ]; then
        echo "Running worker bots:"
        for PID in `cat $BOTPIDS`; do
            if `ps -p $PID > /dev/null 2>&1`; then
                echo "$(hostname -s).$PID (pid $PID)"
            fi
        done
    else
        echo "No worker bots running"
    fi
else
    startbots
    echo "All worker bots have started"
    echo "Worker pids have been stored in $BOTPIDS, use -k flag to shutdown workers"
    echo "Exiting, sayonara!"
fi
