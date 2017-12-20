# diskover - Elasticsearch file system crawler and storage analytics

[![License](https://img.shields.io/github/license/shirosaidev/diskover.svg?label=License&maxAge=86400)](./LICENSE)
[![Release](https://img.shields.io/github/release/shirosaidev/diskover.svg?label=Release&maxAge=60)](https://github.com/shirosaidev/diskover/releases/latest)
[![Donate Patreon](https://img.shields.io/badge/Donate%20%24-Patreon-brightgreen.svg)](https://www.patreon.com/diskover)
[![Donate PayPal](https://img.shields.io/badge/Donate%20%24-PayPal-brightgreen.svg)](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=CLF223XAS4W72)

<img align="left" width="249" height="189" src="docs/diskover.png?raw=true" hspace="5" vspace="5">

diskover is an open-source file system crawler and disk usage application that uses [Elasticsearch](https://www.elastic.co) to index and search your file metadata. diskover crawls and indexes your files on a local computer or remote server using NFS or SMB.

diskover helps identify old and unused files and give better insights into data change, file duplication and wasted space. It is designed to help deal with managing large amounts of data growth and provide detailed storage analytics.

diskover includes a built-in TCP socket server for remote commands, "crawl-bot" for continuos scanning and plug-in support for expanding diskover's indexing capabilities. It is written in Python and runs on Linux and OS X/macOS.

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
   ___       ___       ___       ___       ___       ___       ___       ___
  /\  \     /\  \     /\  \     /\__\     /\  \     /\__\     /\  \     /\  \
 /::\  \   _\:\  \   /::\  \   /:/ _/_   /::\  \   /:/ _/_   /::\  \   /::\  \
/:/\:\__\ /\/::\__\ /\:\:\__\ /::-"\__\ /:/\:\__\ |::L/\__\ /::\:\__\ /::\:\__\
\:\/:/  / \::/\/__/ \:\:\/__/ \;:;-",-" \:\/:/  / |::::/  / \:\:\/  / \;:::/  /
 \::/  /   \:\__\    \::/  /   |:|  |    \::/  /   L;;/__/   \:\/  /   |:\/__/
  \/__/     \/__/     \/__/     \|__|     \/__/    v1.4.1     \/__/     \|__|
                                      https://shirosaidev.github.io/diskover
                                      Bringing light to the darkness.
                                      Support diskover on Patreon :)

    
2017-12-20 15:08:41,664 [INFO][diskover] Connecting to Elasticsearch
2017-12-20 15:08:41,676 [INFO][diskover] Checking ES index: diskover-index
2017-12-20 15:08:41,680 [WARNING][diskover] ES index exists, deleting
2017-12-20 15:08:41,968 [INFO][diskover] Creating ES index
2017-12-20 15:08:42,192 [INFO][diskover] Adding disk space info to ES index
2017-12-20 15:08:42,197 [INFO][diskover] Starting crawl using 20 threads
Crawling: 100%|████████████████████| 10147/10147 [0h:00m:00s, 322.7 dir/s]
2017-12-20 15:09:13,107 [INFO][diskover] Finished crawling

********************************* CRAWL STATS *********************************
 Directories: 10147 / Skipped: 92
 Files: 64267 (54.01 GB) / Skipped: 1211 (46.21 GB)
 Elapsed time: 0h:00m:31s
*******************************************************************************
```

## User Guide

[Read the wiki](https://github.com/shirosaidev/diskover/wiki) for more documentation on how to use diskover.

## Discussions/Questions

For discussions or questions about diskover, please ask on [Google Group](https://groups.google.com/forum/?hl=en#!forum/diskover).

## Bugs

For bugs about diskover, please use the [issues page](https://github.com/shirosaidev/diskover/issues).

## Donations

To continue developing diskover and keep making it better, please consider supporting my work on [Patreon](https://www.patreon.com/diskover) or [PayPal](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=CLF223XAS4W72). Thank you so much to all the users and supporters.

## License

See the [license file](https://github.com/shirosaidev/diskover/blob/master/LICENSE).
