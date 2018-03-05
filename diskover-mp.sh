#!/bin/bash
# diskover parallel multi-processing crawl script
# runs diskover.py in parallel for each directory in rootdir
# Requirements: gnu parallel, python, diskover.py
# https://github.com/shirosaidev/diskover
#
# Copyright (C) Chris Park 2017
# diskover is released under the Apache 2.0 license. See
# LICENSE for the full license text.
#

############# EDIT BELOW FOR YOUR ENVIRONMENT #############

# paths
PYTHON=python3 # path to python command or python if in PATH
PARALLEL=parallel # path to GNU parallel command or parallel if in PATH
DISKOVER=./diskover.py # path to diskover.py

DISKOVER_OPTS="-e -s 0" # diskover.py options
DISKOVER_INDEX="diskover-index" # diskover.py index
MAXPROCS="100%" # default proccess to run in parallel (can be number or cpu %)
MAXTHREADS=8 # default number of threads per proccess (diskover's -t flag)

###########################################################


# script version
VERSION="1.1"

function printhelp {
    echo "Usage: $(basename $0) [OPTION] [ROOTDIR]"
    echo
    echo "Options:"
    echo
    echo "  -p, --procs      maximum parallel processes (default $MAXPROCS)"
    echo "  -t, --threads    maximum threads to use per process (default $MAXTHREADS)"
    echo "  -v, --version    displays version and exits"
    echo "  -h, --help       displays this help message and exits"
    echo
    echo "diskover multiproc parallel scanner v$VERSION"
    echo
    echo "Runs diskover.py in parallel for each directory in ROOTDIR."
    echo
    echo "Requirements: gnu parallel, python, diskover.py"
    echo "Adjust paths and settings at top of script"
    exit 1
}

# display help if no args
if [ $# -eq 0 ] || [ $1 == "-h" ] || [ $1 == "--help" ]; then
  printhelp
fi

# get args
while test $# -gt 1; do
    case "$1" in
    -p|--procs)
      shift
      if test $# -gt 0; then
          MAXPROCS=$1
      else
          echo number of processes required for -p option.
          exit 1
      fi
      shift
      ;;
    -t|--threads)
      shift
      if test $# -gt 0; then
          MAXTHREADS=$1
      else
          echo number of threads required for -t option.
          exit 1
      fi
      shift
      ;;
    -v|--version)
      echo "$0 v$VERSION";
      exit 0
      ;;
     *)
      echo "Invalid option, use -h for help" >&2
      exit 1
      ;;
    esac
done

if test $# -gt 0; then
    ROOTDIR="$1"
else
  echo ROOTDIR required.
  exit 1
fi

function banner {
  # print banner
  echo "$(tput setaf 1)
  ________  .__        __
  \\______ \\ |__| _____|  | _________  __ ___________
   |    |  \\|  |/  ___/  |/ /  _ \\  \\/ // __ \\_  __ \\ /)___(\\
   |    \`   \\  |\\___ \\|    <  <_> )   /\\  ___/|  | \\/ (='.'=)
  /_______  /__/____  >__|_ \\____/ \\_/  \\___  >__|   (\"\)_(\"\)
          \\/        \\/     \\/ mp-crawl v$VERSION \\/
                https://github.com/shirosaidev/diskover$(tput sgr 0)
"
}

function startcrawl {
	echo "starting background parallel crawls for $ROOTDIR (max $MAXPROCS procs/$MAXTHREADS threads per proc)"
    echo "press ctrl+c to stop crawls"
    echo
    # create index and index rootdir directory doc
    echo "creating es index and indexing $ROOTDIR directory..."
	time $PYTHON $DISKOVER -t $MAXTHREADS -i $DISKOVER_INDEX $DISKOVER_OPTS --maxdepth 1 -q -d $ROOTDIR
    echo "DONE!"
    echo
    # find all directories in rootdir and start crawls for each using parallel
    echo "finding all directories in $ROOTDIR..."
    echo "there are `find $ROOTDIR -maxdepth 1 -mindepth 1 -type d ! -empty | wc -l | xargs` directories..."
    echo "starting parallel crawls..."
    time find $ROOTDIR -maxdepth 1 -mindepth 1 -type d | \
    $PARALLEL -j $MAXPROCS --bar --progress --eta $PYTHON $DISKOVER -t $MAXTHREADS -i $DISKOVER_INDEX $DISKOVER_OPTS -R -n -q -d {}
    echo "DONE!"
    echo
    # calculate rootdir size/items
    echo "calculating rootdir $ROOTDIR directory size/items..."
	time $PYTHON $DISKOVER -t $MAXTHREADS -i $DISKOVER_INDEX -c -q -d $ROOTDIR
    echo "DONE!"
}

banner
startcrawl

echo "all parallel crawls have finished"
exit 0
