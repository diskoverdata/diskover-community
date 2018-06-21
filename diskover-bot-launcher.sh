#!/bin/bash
# diskover bot launcher multi-processing script
# starts multiple bots to help with diskover redis queue
# https://github.com/shirosaidev/diskover
#
# Copyright (C) Chris Park 2017-2018
# diskover is released under the Apache 2.0 license. See
# LICENSE for the full license text.
#

############# EDIT BELOW FOR YOUR ENVIRONMENT #############
# paths and default config values below

# path to python command or python if in PATH
PYTHON=python
# path to diskover_worker_bot.py
DISKOVERBOT=./diskover_worker_bot.py
# path to killredisconn.py
KILLREDISCONN=./killredisconn.py
# number of bots to start (cores x 2 might be good start)
WORKERBOTS=8
# run bots in burst mode (quit when all jobs done)
BURST=FALSE
# file to store bot pids
BOTPIDS=/tmp/diskover_bot_pids
# queue that worker bots should listen on
# queues: diskover, diskover_crawl, diskover_scrapemeta, diskover_bulkadd, diskover_calcdir
# default ALL (listen on all queues)
QUEUE=ALL

###########################################################


VERSION="1.4"

function printhelp {
    echo "Usage: $(basename $0) [OPTION] [ROOTDIR]"
    echo
    echo "Options:"
    echo
    echo "  -w n          number of worker bots to start (default $WORKERBOTS)"
    echo "  -q queue      which queue bots should listen on (default ALL)"
    echo "  -b            burst mode (bots quit when no more jobs)"
    echo "  -s            show all bots running"
    echo "  -k            kill all bots"
    echo "  -r            restart all running bots"
    echo "  -R            remove any stuck/idle worker bot connections in Redis"
    echo "  -f            force remove all worker bot connections in Redis"
    echo "  -V            displays version and exits"
    echo "  -h            displays this help message and exits"
    echo
    echo "diskover worker bot process launcher v$VERSION"
    echo
    echo "Adjust default paths and settings at top of script"
    exit 1
}

KILLBOTS=FALSE
RESTARTBOTS=FALSE
REMOVEBOTS=FALSE
FORCEREMOVEBOTS=FALSE
SHOWBOTS=FALSE
while getopts :h?w:q:bskrRfV opt; do
    case "$opt" in
    h) printhelp; exit 0;;
    w) WORKERBOTS=$OPTARG;;
    q) QUEUE=$OPTARG;;
    b) BURST=TRUE;;
    s) SHOWBOTS=TRUE;;
    k) KILLBOTS=TRUE;;
    r) RESTARTBOTS=TRUE;;
    R) REMOVEBOTS=TRUE;;
    f) FORCEREMOVEBOTS=TRUE; REMOVEBOTS=TRUE;;
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
    if [ $QUEUE != "ALL" ]; then
        ARGS+="-q $QUEUE"
    fi
    for (( i = 1; i <= $WORKERBOTS; i++ )); do
        $PYTHON $DISKOVERBOT $ARGS > /dev/null 2>&1 &
        echo "$(hostname -s).$! (pid $!)"
        echo "$!" >> $BOTPIDS
    done

    echo "DONE!"
    echo "All worker bots have started"
    echo "Worker pids have been stored in $BOTPIDS, use -k flag to shutdown workers or -r to restart"
    echo "Exiting, sayonara!"
}

function killbots {
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
        echo "Pid file can't be found, killing any bots..."
        pkill -f diskover_worker_bot.py
        echo "All worker bots have been sent shutdown command"
    fi
}

function removebots {
    echo "Removing any stuck/idle worker bot connections in Redis..."
    if [ $FORCEREMOVEBOTS == TRUE ]; then
        $PYTHON $KILLREDISCONN -f
    else
        $PYTHON $KILLREDISCONN
    fi
    echo "Done"
}

function showbots {
    if [ -f $BOTPIDS ]; then
        echo "Running worker bots:"
        for PID in `cat $BOTPIDS`; do
            if `ps -p $PID > /dev/null 2>&1`; then
                echo "$(hostname -s).$PID (pid $PID)"
            fi
        done
    else
        echo "Pid file can't be found, running worker bot pids:"
        pgrep -f diskover_worker_bot.py
    fi
}

function countbots {
    if [ -f $BOTPIDS ]; then
        WORKERBOTS=`cat $BOTPIDS | wc -l | tr -d '[:space:]'`
    else
        WORKERBOTS=`pgrep -f diskover_worker_bot.py | wc -l | tr -d '[:space:]'`
    fi
}

banner

if [ $KILLBOTS == TRUE ]; then
    killbots
elif [ $REMOVEBOTS == TRUE ]; then
    removebots
elif [ $SHOWBOTS == TRUE ]; then
    showbots
elif [ $RESTARTBOTS == TRUE ]; then
    countbots
    killbots
    echo sleeping for 2 seconds...
    sleep 2
    startbots
else
    startbots
fi
