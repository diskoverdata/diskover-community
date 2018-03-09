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

# paths and default config values below
PYTHON=python3 # path to python command or python if in PATH
PARALLEL=parallel # path to GNU parallel command or parallel if in PATH
DISKOVER=./diskover.py # path to diskover.py
FIND=find # path to find or find if in PATH
PARALLEL_JOBLOG=/tmp/diskover-mp-joblog # default job log location, override with -l path

# diskover.py options (don't use thread flags here)
DISKOVER_OPTS="-s 1"
# diskover.py index
DISKOVER_INDEX="diskover-index"
# default proccess to run in parallel can be % of cpu cores (100%, 200%, etc)
# or num (8, 20, etc), 0 to run as many as possible
MAXPROCS="100%"
# default number of directory meta crawler worker threads per
# proccess (diskover's -w flag), num cores is good start
MAX_DIR_THREADS=4
# default number of file meta crawler worker threads per
# proccess (diskover's -W flag), num cores is a good start
MAX_FILE_THREADS=4
# default number of threads to calculate rootdir size (diskover's -t flag)
# num of cores x 2 is a good start
MAXTHREADS=8
# maximum depth levels to allow diskover to crawl
MAXDEPTH=100
# minimum depth levels to find directories for crawling from rootdir
MINDEPTH=1
# directory excludes for find (separate with -name <string> , can include wildcards)
# example '( -empty -name ".*" -name "*.snapshot*" -name "*.Snapshot*" )'
EXCLUDES='( -empty -name ".*" -name "*.snapshot*" -name "*.Snapshot*" )'
###########################################################


# script version
VERSION="1.2"

function printhelp {
    echo "Usage: $(basename $0) [OPTION] [ROOTDIR]"
    echo
    echo "Options:"
    echo
    echo "  -i name, --index name              diskover ES index name (default $DISKOVER_INDEX)"
    echo "  -p n, --procs n                    maximum parallel job processes, can be % of cpu"
    echo "                                     cores (100%, 200%, etc) or num (8, 20, etc),"
    echo "                                     0 to run as many as possible (default $MAXPROCS)"
    echo "  -w n, --dirthreads n               maximum dir meta crawler threads to use per process,"
    echo "                                     a good start is cores x 2 (default $MAX_DIR_THREADS)"
    echo "  -W n, --filethreads n              maximum file meta crawler threads to use per process,"
    echo "                                     a good start is cores x 2 (default $MAX_FILE_THREADS)"
    echo "  -t n, --threads n                  maximum threads to calc root dir size (default $MAXTHREADS)"
    echo "  -d n, --mindepth n                 minimum depth level to find directories for"
    echo "                                     crawling from ROOTDIR (default $MINDEPTH)"
    echo "  -m n, --maxdepth n                 maximum depth to let diskover crawl from"
    echo "                                     mindepth (default $MAXDEPTH)"
    echo "  -o \"opts\", --diskoveropt \"opts\"    diskover cli options, put in quotes (default $DISKOVER_OPTS)"
    echo "  -l path, --joblog path             parallel job log file path"
    echo "                                     (default $PARALLEL_JOBLOG)"
    echo "  -v, --version                      displays version and exits"
    echo "  -h, --help                         displays this help message and exits"
    echo
    echo "diskover multiproc parallel scanner v$VERSION"
    echo
    echo "Runs diskover.py in parallel for each directory in ROOTDIR."
    echo
    echo "Requirements: gnu parallel, python, diskover.py"
    echo "Adjust default paths and settings at top of script"
    exit 1
}

# display help if no args
if [ $# -eq 0 ] || [ $1 == "-h" ] || [ $1 == "--help" ]; then
  printhelp
fi

# get args
while test $# -gt 1; do
    case "$1" in
    -i|--index)
      shift
      if test $# -gt 0; then
          DISKOVER_INDEX="$1"
      else
          echo diskover-<name> index name required for -i option.
          exit 1
      fi
      shift
      ;;
    -p|--procs)
      shift
      if test $# -gt 0; then
          MAXPROCS="$1"
      else
          echo number of parallel jobs required for -p option.
          exit 1
      fi
      shift
      ;;
    -w|--dirthreads)
        shift
        if test $# -gt 0; then
            MAX_DIR_THREADS=$1
        else
            echo number of dir threads required for -w option.
            exit 1
        fi
        shift
      ;;
    -W|--filethreads)
        shift
        if test $# -gt 0; then
            MAX_FILE_THREADS=$1
        else
            echo number of file threads required for -W option.
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
    -d|--mindepth)
        shift
        if test $# -gt 0; then
            MINDEPTH=$1
        else
            echo depth level required for -d option.
            exit 1
        fi
        shift
    ;;
    -m|--maxdepth)
        shift
        if test $# -gt 0; then
            MAXDEPTH=$1
        else
            echo depth level required for -m option.
            exit 1
        fi
        shift
    ;;
    -o|--diskoveropt)
        shift
        if test $# -gt 0; then
            DISKOVER_OPTS="$1"
        else
            echo diskover cli flags required for -o option.
            exit 1
        fi
        shift
        ;;
    -l|--joblog)
        shift
        if test $# -gt 0; then
            PARALLEL_JOBLOG="$1"
        else
            echo parallel job log file path required for -l option.
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
          \\/        \\/     \\/               \\/
                multi-proc parallel crawler v$VERSION
                https://github.com/shirosaidev/diskover
                \"Crawling all your stuff, core melting time\"$(tput sgr 0)

"
}

function startcrawl {
	echo "starting background parallel crawls for $ROOTDIR (max $MAXPROCS procs/$MAX_DIR_THREADS dir threads, $MAX_FILE_THREADS file threads per proc)"
    echo "excluding $EXCLUDES"
    echo "press ctrl+c to stop crawls"
    echo
    # create index and index rootdir directory doc
    echo "creating es index $DISKOVER_INDEX and indexing $ROOTDIR directory..."
	time $PYTHON $DISKOVER -w $MAX_DIR_THREADS -W $MAX_FILE_THREADS -i $DISKOVER_INDEX $DISKOVER_OPTS --maxdepth 1 -q -d $ROOTDIR
    echo "DONE!"
    echo
    # find all directories in rootdir and start crawls for each using parallel
    echo "finding all directories in $ROOTDIR (depth: $MINDEPTH up to max $MAXDEPTH) and starting parallel crawls..."
    if test "$PARALLEL_JOBLOG" != ""; then
        echo "writing parallel joblog to $PARALLEL_JOBLOG..."
        time $FIND $ROOTDIR -maxdepth $MINDEPTH -mindepth $MINDEPTH -type d -and -not $EXCLUDES | \
        $PARALLEL -j $MAXPROCS --bar --progress --joblog $PARALLEL_JOBLOG $PYTHON $DISKOVER -w $MAX_DIR_THREADS -W $MAX_FILE_THREADS -i $DISKOVER_INDEX $DISKOVER_OPTS --maxdepth $MAXDEPTH -R -n -q -d {}
    else
        time $FIND $ROOTDIR -maxdepth $MINDEPTH -mindepth $MINDEPTH -type d -and -not $EXCLUDES | \
        $PARALLEL -j $MAXPROCS --bar --progress $PYTHON $DISKOVER -w $MAX_DIR_THREADS -W $MAX_FILE_THREADS -i $DISKOVER_INDEX $DISKOVER_OPTS --maxdepth $MAXDEPTH -R -n -q -d {}
    fi
    echo "DONE!"
    echo
    # calculate rootdir size/items
    echo "calculating rootdir $ROOTDIR directory size/items usng $MAXTHREADS threads..."
	time $PYTHON $DISKOVER -t $MAXTHREADS -i $DISKOVER_INDEX -c -q -d $ROOTDIR
    echo "DONE!"
}

banner
startcrawl

echo "all parallel crawls have finished"
exit 0
