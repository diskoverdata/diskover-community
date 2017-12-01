# diskover - Elasticsearch file system crawler and storage analytics

[![License](https://img.shields.io/github/license/shirosaidev/diskover.svg?label=License&maxAge=86400)](./LICENSE)
[![Release](https://img.shields.io/github/release/shirosaidev/diskover.svg?label=Release&maxAge=60)](https://github.com/shirosaidev/diskover/releases/latest)

<img align="left" width="249" height="189" src="docs/diskover.png?raw=true" hspace="5" vspace="5">

diskover is a file system analytics application that includes a multi-threaded disk crawler that uses [Elasticsearch](https://www.elastic.co) to index your file metadata. diskover crawls and indexes your files on a local computer or remote server using NFS or SMB.

File metadata is bulk added and streamed into Elasticsearch, allowing you to search and visualize your files in [diskover-web](https://github.com/shirosaidev/diskover-web) or [Kibana](https://www.elastic.co/products/kibana) without having to wait until the crawl is finished. diskover is written in Python and runs on Linux and OS X/macOS.

diskover aims to help manage your storage by identifying old and unused files and give better insights into data change "hotfiles", file duplication and wasted space. It is designed to help deal with managing large amounts of data growth and provide detailed storage analytics.

diskover includes a built-in UDP socket server for remote commands and also has plug-in support for expanding diskover's indexing capabilities.

## Screenshots

[diskover-web](https://github.com/shirosaidev/diskover-web) (diskover's web file manager, analytics app, file system search engine, rest-api)
![diskover-web](https://github.com/shirosaidev/diskover-web/raw/master/docs/diskover-web-dashboard-screenshot.png?raw=true)
Kibana dashboards / saved searches and visualizations (included in diskover download)
![kibana-screenshot](docs/kibana-dashboarddark2-screenshot.png?raw=true)
Gource visualization support (see videos below)
![diskover-gource](docs/diskover-gource1-screenshot.png?raw=true)

### diskover Gource videos

* [File modifications over time](https://youtu.be/InlfK8GQ-kM)
* [Realtime file crawl using 8 threads](https://youtu.be/qKLJjZ0TMqA)

## Installation Guide

### Requirements

* `Linux or OS X/macOS` (tested on OS X 10.11.6, Ubuntu 16.04)
* `Python 2.7. or Python 3.5.` (tested on Python 2.7.14, 3.5.3)
* `Python elasticsearch client module` [elasticsearch](https://pypi.python.org/pypi/elasticsearch) (tested on 5.4.0, 5.5.1)
* `Python requests module` [requests](https://pypi.python.org/pypi/requests)
* `Python scandir module` [scandir](https://pypi.python.org/pypi/scandir)
* `Elasticsearch` (local or [AWS ES Service](https://aws.amazon.com/elasticsearch-service/), tested on Elasticsearch 5.4.2, 5.6.4)

### Optional Installs

* [diskover-web](https://github.com/shirosaidev/diskover-web) (diskover's web file manager and analytics app)
* [Kibana](https://www.elastic.co/products/kibana) (for visualizing Elasticsearch data, tested on Kibana 5.4.2, 5.6.4)
* [X-Pack](https://www.elastic.co/downloads/x-pack) (for graphs, reports, monitoring and http auth)
* [Gource](http://gource.io) (for Gource visualizations of diskover Elasticsearch data)

### Download

```sh
$ git clone https://github.com/shirosaidev/diskover.git
$ cd diskover
```

[Download latest version](https://github.com/shirosaidev/diskover/releases/latest)

### Requirements

You need to have at least **Python 2.7. or Python 3.5.** and have installed required Python dependencies using `pip`.

```sh
$ sudo pip install -r requirements.txt
```

## Getting Started

Start diskover as root user with:

```sh
$ cd /path/you/want/to/crawl
$ sudo python /path/to/diskover.py
```

**Defaults for crawl with no flags is to index from . (current directory) and files >0 MB and 0 days modified time. Empty files are skipped. Use -h to see cli options.**

A successfull crawl should look like this:

```
  __               __
 /\ \  __         /\ \
 \_\ \/\_\    ____\ \ \/'\     ___   __  __     __   _ __     //
 /'_` \/\ \  /',__\\ \ , <    / __`\/\ \/\ \  /'__`\/\`'__\  ('>
/\ \L\ \ \ \/\__, `\\ \ \\`\ /\ \L\ \ \ \_/ |/\  __/\ \ \/   /rr
\ \___,_\ \_\/\____/ \ \_\ \_\ \____/\ \___/ \ \____\\ \_\  *\))_
 \/__,_ /\/_/\/___/   \/_/\/_/\/___/  \/__/   \/____/ \/_/ v1.4.0
                  https://github.com/shirosaidev/diskover

2017-11-30 17:38:24,203 [INFO][diskover] Connecting to Elasticsearch
2017-11-30 17:38:24,207 [INFO][diskover] Checking ES index: diskover-2017.11.30
2017-11-30 17:38:24,209 [WARNING][diskover] ES index exists, deleting
2017-11-30 17:38:24,353 [INFO][diskover] Creating ES index
2017-11-30 17:38:24,466 [INFO][diskover] Crawling using 8 threads
2017-11-30 17:38:24,466 [INFO][diskover] Adding disk space info to ES index
Crawling: 100%|████████████████████| 22352/22352 [0h:00m:00s, 267.6 dir/s]
2017-11-30 17:39:50,738 [INFO][diskover] Finished crawling

********************************* CRAWL STATS *********************************
 Directories: 22352 / Skipped: 0
 Files: 127733 (54.88 GB) / Skipped: 1325 (0B)
 Elapsed time: 0h:01m:26s
*******************************************************************************
```

## User Guide

[Read the wiki](https://github.com/shirosaidev/diskover/wiki) for more documentation on how to use diskover.

## Discussions/Questions

For discussions or questions about diskover, please ask on [Google Group](https://groups.google.com/forum/?hl=en#!forum/diskover).

## Bugs

For bugs about diskover, please use the [issues page](https://github.com/shirosaidev/diskover/issues).

## License

See the [license file](https://github.com/shirosaidev/diskover/blob/master/LICENSE).
