#!/bin/bash
# This shell script spins up parallel diskover.py crawls to try and split the top level 
# sub directories in -d <root dir> into separate parallel diskover.py processes to help
# speed up crawl times on very lage file trees.
#
# Adjust settings in SETTINGS section below for your env.
#
# parallel_crawl.sh v1.0.1
# Maintainer: shirosai
# https://github.com/shirosaidev/diskover
#
# Copyright (C) Chris Park 2020
# diskover is released under the Apache 2.0 license. See
# LICENSE for the full license text.
#


# Ensure we won't hit limits
for opt in $(ulimit -a | sed 's/.*\-\([a-z]\)[^a-zA-Z].*$/\1/')
do
    ulimit -$opt unlimited
done

ulimit -n 999999


################## SETTINGS ##################

# location where diskover is installed
DISKOVERROOT="/opt/diskover"
# location of python executable, can use python or python3 if in path,
# make sure to set python path to same in diskover-bot-launcher.sh script
# so bots use same version of python
PYTHON="python3"
# location of realpath executable or realpath if in path
REALPATH="realpath"

# number of worker bots to start
BOTS=48
# tree walk threads
THREADS=32
# index emptry dirs, set to 1 to index or 0 not to index
EMPTYDIRS=1
# index 0 byte empty files, set to 1 to index or 0 not to index
EMPTYFILES=1
# split file meta collecting amongst bots, set to 1 to use and 0 to not use
SPLITFILES=1
# minimum number of files in directory for bots to share with other bots
SPLITFILESNUM=10000
# chunk file lists for directories with tons of files, set to 1 to use and 0 to not use
CHUNKFILES=1
# number of files to send in chunk for chunkfiles
CHUNKFILESNUM=1000

# top storage rootdir you want to crawl from
ROOT="/ifs"
# index suffix, uses cli arg 1
INDEXSUF="${1}"
# depth of subdirs to run parallel crawls
DEPTH=1
# directory batch size used by diskover.py and sent to Redis RQ for bots to process
#BATCH="-b 1"
BATCH="-a"
# delay loop between starting diskover.py parallel processes
LOOPDELAY=0.1
# name of index added after diskover- prefix
INDEXNAME="sanitized"
# date string added after INDEXNAME
DATESTRING=$(date +%Y%m%d)

# directory to store verbose output logs, include trailing slash, verbose logs 
# stored in subdirs underneath
LOGDIRROOT="/opt/batch/"

# crawl timeout, kills all diskover.py processes if been running for this long in seconds x 60 sec
CRAWLTIMEOUT=720  # 720 sec x 60 sec = 12 hours

################## SETTINGS END ##################


if [ ! "$(which ${PYTHON})" ]
then
    echo "Can't find python executable.  Check settings.  Aborting."
    exit 1
fi


if [ ! "$(which ${REALPATH})" ]
then
    echo "Can't find realpath executable.  Check settings.  Aborting."
    exit 1
fi

if [ ! -d ${ROOT} ]
then
    echo "Root dir not found.  Check settings.  Aborting."
    exit 1
fi


if [ -z "${INDEXSUF}" ]
then
    INDEXSUF=1
    OK=0
    while [ ${OK} -ne 1 ]
    do
        INDEX="diskover-${INDEXNAME}-${DATESTRING}-${INDEXSUF}"
        LOGDIR="${LOGDIRROOT}${INDEX}"
        if [ -e "${LOGDIR}" ]
        then
            let INDEXSUF=${INDEXSUF}+1
        else
            OK=1
        fi
    done
else
    INDEX="diskover-${INDEXNAME}-${DATESTRING}-${INDEXSUF}"
    LOGDIR="${LOGDIRROOT}${INDEX}"
    if [ -e "${LOGDIR}" ]
    then
        echo "Log directory exists.  Consider specifying a different index.  Aborting."
        exit 1
    fi
fi

mkdir -p "${LOGDIR}" || exit 1

cd ${DISKOVERROOT} || exit 1

# Restart the worker bots
./diskover-bot-launcher.sh -k
sleep 2
./diskover-bot-launcher.sh -k
sleep 2
./diskover-bot-launcher.sh -w ${BOTS}

SFARGS=""
if [ ${SPLITFILES} -eq 1 ]
then
    SFARGS+="--splitfiles --splitfilesnum ${SPLITFILESNUM}"
fi
CFARGS=""
if [ ${CHUNKFILES} -eq 1 ]
then
    CFARGS+="--chunkfiles --chunkfilesnum ${CHUNKFILESNUM}"
fi
EXTRAARGS=""
if [ ${EMPTYDIRS} -eq 1 ]
then
    EXTRAARGS+="-e"
fi
if [ ${EMPTYFILES} -eq 1 ]
then
    EXTRAARGS+=" -s 0"
fi

# First let's get the ROOT directory indexed
if [ ${DEPTH} -eq 0 ]
then
    echo "Depth set to 0, running all..."
    ${PYTHON} diskover.py -F ${EXTRAARGS} -i "${INDEX}" -d "${ROOT}" ${BATCH} -T ${THREADS} ${SFARGS} --verbose
else
    echo "Collecting directories up to a depth of ${DEPTH}..."
    FINDB=$(date +%s)
    TLDS=$(find "${ROOT}" -maxdepth ${DEPTH} -type d)
    FINDA=$(date +%s)
    FINDD=$(echo ${FINDA}-${FINDB}|bc)
    echo "Directories collected in ${FINDD} seconds..."
    while read TLD
    do
        CURLOG="${LOGDIR}/${INDEX}_$(echo ${TLD} | sed 's/\//_/g' | sed 's/ /_/g').log"
        CURDEPTH=$(realpath --relative-to="${ROOT}" "${TLD}" | awk -F'/' '{ print NF }')
        #echo "DEBUG: TLD = ${TLD}"
        #echo "DEBUG: CUR = ${CURDEPTH}"
        if [ "${TLD}" == "${ROOT}" ]
        then
            echo "Starting diskover for root ${TLD}... Logs --> ${CURLOG}"
            ${PYTHON} diskover.py -F ${EXTRAARGS} -i "${INDEX}" -d "${TLD}" --maxdepth 1 ${BATCH} -T ${THREADS} ${SFARGS} ${CFARGS} --verbose > "${CURLOG}" 2>&1
        elif [ ${CURDEPTH} -lt ${DEPTH} ]
        then
            echo "Starting diskover for ${TLD}... Logs --> ${CURLOG}"
            ${PYTHON} diskover.py ${EXTRAARGS} -i "${INDEX}" -d "${TLD}" --maxdepth 1 --reindexrecurs ${BATCH} -T ${THREADS} ${SFARGS} ${CFARGS} --verbose > "${CURLOG}" 2>&1
        else
            echo "Starting diskover for ${TLD} and sending to background... Logs --> ${CURLOG}"
            ${PYTHON} diskover.py ${EXTRAARGS} -i "${INDEX}" -d "${TLD}" --reindexrecurs ${BATCH} -T ${THREADS} ${SFARGS} ${CFARGS} --verbose > "${CURLOG}" 2>&1 &
        fi
        sleep ${LOOPDELAY}
    done <<< "${TLDS}"

fi

echo "All diskover processes started..."

# Wait until all of the diskover processes are finished

RUNNING=$(ps auxwww | grep diskover.py | grep -v grep | wc -l)
CTR=0
while [ ${RUNNING} -gt 0 ]
do
    RUNNING=$(ps auxwww | grep diskover.py | grep -v grep | wc -l)
    echo "Waiting for diskover processes to finish..."
    sleep 60
    let CTR=${CTR}+1
    if [ ${CTR} -gt ${CRAWLTIMEOUT} ]
    then
        echo "Killing diskover.py processes..."
        pkill -f diskover.py
    fi
done

# Now let's do the dircalcs
${PYTHON} diskover.py -i "${INDEX}" -d "${ROOT}" ${BATCH} --dircalcsonly --maxdcdepth 0 --verbose

# Kill the bots
./diskover-bot-launcher.sh -k
sleep 2

echo "Done."
