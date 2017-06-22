#!/bin/bash
# diskover gource script
# gets ouput from diskover for gource
# https://github.com/shirosaidev/diskover

# gource settings
RESOLUTION="1280x720"
SECPERDAY=1
AUTOSKIPSEC=1
MAXFILELAG=0.1 # should be set to same in diskover.cfg
OTHEROPTIONS="" # "--hide filenames" for example

# script version
VERSION="1.0"

# display help if no args or -h flag
if [ $# -eq 0 ] || [ "$1" == "-h" ] || [ "$1" == "--help" ]; then
  echo "Usage: $(basename $0) [OPTION] [LOGFILE]"
  echo "Gets output from diskover for gource."
  echo
  echo "Options:"
  echo
  echo "  -r, --realtime  realtime crawl data from diskover output"
  echo "  -m, --modified  file modified time data from diskover logfile"
  echo "  -v, --version   displays version and exits"
  exit 1
fi

# get args
while getopts "rmv" opt; do
  case $opt in
    r)
      INPUTTYPE="realtime";
      ;;
    m)
      INPUTTYPE="modified";
      LOGFILE=$2
      if [ "$LOGFILE" == "" ];then
        echo log file required for -m option.
        exit 1
      fi
      ;;
    v)
      echo "$0 v$VERSION";
      exit 0
      ;;
    \\?)
      echo "Invalid option: -$OPTARG" >&2
      exit 1
      ;;
    :)
      echo "Option -$OPTARG requires an argument." >&2
      exit 1
      ;;
    esac
done

function banner {
  # print banner
  echo "$(tput setaf 1)
  ________  .__        __
  \\______ \\ |__| _____|  | _________  __ ___________
   |    |  \\|  |/  ___/  |/ /  _ \\  \\/ // __ \\_  __ \\ /)___(\\
   |    \`   \\  |\\___ \\|    <  <_> )   /\\  ___/|  | \\/ (='.'=)
  /_______  /__/____  >__|_ \\____/ \\_/  \\___  >__|   (\"\)_(\"\)
          \\/        \\/     \\/  gource v$VERSION  \\/
                https://github.com/shirosaidev/diskover$(tput sgr 0)
"
}

function rungource {
  # use crawl realtime streaming output from diskover with gource
  if [[ "$INPUTTYPE" == "realtime" ]]; then
    # check stdin
    if [[ -p /dev/stdin ]]; then
      echo seeing stdin data stream, starting gource
      TITLE="diskover file system crawler (realtime crawl by worker thread)"
      gource --title "$TITLE" --key -$RESOLUTION --seconds-per-day $SECPERDAY \
        --auto-skip-seconds $AUTOSKIPSEC --max-file-lag $MAXFILELAG $OTHEROPTIONS --realtime --log-format custom -
    else
      echo no data stream from diskover to stdin, pipe some diskover data and try again.
      exit 1
    fi
  # use file modified time logfile from diskover with gource
  elif [[ "$INPUTTYPE" == "modified" ]]; then
    echo starting gource using $LOGFILE
    TITLE="diskover file system crawler (file modified time by user)"
    gource --title "$TITLE" --key -$RESOLUTION --seconds-per-day $SECPERDAY \
      --auto-skip-seconds $AUTOSKIPSEC $OTHEROPTIONS $LOGFILE
  fi
}

banner
rungource

echo closing
exit 0
