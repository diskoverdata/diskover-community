# diskover - Elasticsearch file system crawler and storage analytics

<img align="left" width="249" height="189" src="docs/diskover.png?raw=true" hspace="5" vspace="5">

diskover is a multi-threaded file system crawler that uses [Elasticsearch](https://www.elastic.co) and [Kibana](https://www.elastic.co/products/kibana) to index your file metadata and visualize your storage analytics. diskover crawls and indexes your files on a local computer or remote server using NFS or SMB.

File metadata is bulk added and streamed into Elasticsearch, allowing you to **search and visualize your files in Kibana without having to wait until the crawl is finished**. diskover is written in Python and runs on Linux, OS X/macOS and Windows.

diskover aims to help manage your storage by identifying old and unused files and give better insights into file duplication and wasted space. It is designed to help deal with managing large amounts of data growth and provide detailed storage analytics.

## Screenshots

Kibana dashboards / saved searches and visualizations (included in diskover download)
![kibana-screenshot](docs/kibana-dashboarddark2-screenshot.png?raw=true)
[diskover-web](https://shirosaidev.github.io/diskover-web/) (diskover's web file manager and file system search engine)
![diskover-web](https://github.com/shirosaidev/diskover-web/raw/master/docs/diskover-web-filetree-screenshot.png?raw=true)
Gource visualization support (see videos below)
![diskover-gource](docs/diskover-gource1-screenshot.png?raw=true)

### diskover Gource videos

* [File modifications over time](https://youtu.be/InlfK8GQ-kM)
* [Realtime file crawl using 8 threads](https://youtu.be/qKLJjZ0TMqA)

## Installation Guide

### Requirements

* `Linux, OS X/macOS or Windows` (tested on OS X 10.11.6, Ubuntu 16.04 and Windows 7)
* `Python 2.7. or Python 3.5.` (tested on Python 2.7.14, 3.5.3)
* `Python elasticsearch client module` [elasticsearch](https://pypi.python.org/pypi/elasticsearch) (tested on 5.4.0)
* `Python requests module` [requests](https://pypi.python.org/pypi/requests)
* `Python scandir module` [scandir](https://pypi.python.org/pypi/scandir)
* `Elasticsearch` (local or [AWS ES Service](https://aws.amazon.com/elasticsearch-service/), tested on Elasticsearch 5.4.2)
* `Kibana` (tested on Kibana 5.4.2)

### Windows Additional Requirements

* [CygWin](http://cygwin.com)
* [PyWin32](https://sourceforge.net/projects/pywin32/files/pywin32/)

### Optional Installs

* [diskover-web](https://shirosaidev.github.io/diskover-web/) (diskover's web file manager for searching/tagging files)
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
For Windows, run CygWin terminal as administrator and then run diskover.

**Defaults for crawl with no flags is to index from . (current directory) and files >0 MB and 0 days modified time. Empty files are skipped. Use -h to see cli options.**

A successfull crawl should look like this:

```
  ________  .__        __
  \______ \ |__| _____|  | _________  __ ___________
   |    |  \|  |/  ___/  |/ /  _ \  \/ // __ \_  __ \ /)___(\
   |    `   \  |\___ \|    <  <_> )   /\  ___/|  | \/ (='.'=)
  /_______  /__/____  >__|_ \____/ \_/  \___  >__|   (\")_(\")
          \/        \/     \/   v1.2.0      \/
                      https://github.com/shirosaidev/diskover

2017-09-10 13:23:53,385 [INFO][diskover] Connecting to Elasticsearch
2017-09-10 13:23:53,437 [INFO][diskover] Checking ES index: diskover-2017.04.22
2017-09-10 13:23:53,581 [WARNING][diskover] ES index exists, deleting
2017-09-10 13:23:53,823 [INFO][diskover] Creating ES index
2017-09-10 13:23:54,055 [INFO][diskover] Crawling using 4 threads
Crawling: [100%] |########################################| 10684/10684
2017-09-10 13:24:37,443 [INFO][diskover] Finished crawling

********************************* CRAWL STATS *********************************
 Directories: 10684 / Skipped: 0
 Files: 68818 (56.99 GB) / Skipped: 899 (0B)
 Elapsed time: 0h:00m:44s
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
