#!/bin/bash
set -e

USE_FTP=
FTP_USR=anonymous
FTP_PWD=
FTP_HOST=127.0.0.1
FTP_PORT=21
FTP_PATH=

if [ "$RUN_MODE" == "WORKER" ]; then
    echo "Will run in WORKER mode!!!"
    DISKOVER_CMD="python diskover_worker_bot.py"
elif [ "$RUN_MODE" == "SERVER" ]; then
    echo "Will run in SERVER mode!!!"
    DISKOVER_CMD="python diskover.py"

    if [ -z "$STANDALONE" ] && [ "$STANDALONE" == "true" ]; then
        echo "Listening on TCP:9999..."
        DISKOVER_CMD+=" --listen"
    elif [ -z "$DEBUG_ENALBED" ] && [ "$DEBUG_ENALBED" == "true" ]; then
        echo "Debug mode ON"
        DISKOVER_CMD+=" --debug"
    fi
else
    echo "Unsupported RUN_MODE. Supported values are [WORKER, SERVER] Exiting..."
fi

echo "Evaluated DISKOVER_CMD=$DISKOVER_CMD"

while [ "$1" != "" ]; do
        case $1 in
                --ftp-host )            FTP_HOST=$2; shift 2;;
                --ftp-port )            FTP_PORT=$2; shift 2;;
                --ftp-path )            FTP_PATH=$2; shift 2;;
                --ftp-username )        FTP_USR=$2; shift 2;;
                --ftp-password )        FTP_PWD=$2; shift 2;;
                --ftp )                 USE_FTP=1; shift;;
                --)                     shift; break;;
                * )                     DISKOVER_CMD="$DISKOVER_CMD $1"; shift;;
        esac
done

if ! [ -z "$USE_FTP" ]; then
    echo "Will mount ftp://$FTP_HOST:$FTP_PORT/$FTP_PATH on $DISKOVER_ROOTDIR"
    curlftpfs -r -o custom_list="LIST",ftp_port=- "ftp://$FTP_USR:$FTP_PWD@$FTP_HOST:$FTP_PORT/$FTP_PATH" "$DISKOVER_ROOTDIR"
    echo "Will execute: $DISKOVER_CMD"
    eval '$DISKOVER_CMD'
    fusermount -u "$DISKOVER_ROOTDIR"
else
    echo "Will execute: $DISKOVER_CMD"
    eval '$DISKOVER_CMD'
fi
