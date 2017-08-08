# diskover - Elasticsearch file system crawler and disk space analyzer using Kibana

![diskover](docs/diskover.png?raw=true)

diskover is a file system crawler that indexes your files metadata in [Elasticsearch](https://www.elastic.co) and visualizes your disk usage in [Kibana](https://www.elastic.co/products/kibana). It crawls and indexes your files on a local computer or remote server using nfs or cifs.

File metadata is bulk added and streamed into Elasticsearch, allowing you to **search and visualize your files in Kibana without having to wait until the crawl is finished**. diskover is written in Python and runs on Linux, OS X/macOS and Windows.

diskover aims to help manage your storage by identify old and unused files and give better insights into file duplication and wasted space.

## Screenshots

Kibana dashboard (multiple dashboards and saved searches/visualizations)
![kibana-screenshot](docs/kibana-dashboarddark2-screenshot.png?raw=true)
[diskover-web](https://github.com/shirosaidev/diskover-web) (diskover's web file manager)
![diskover-web](https://github.com/shirosaidev/diskover-web/raw/master/docs/diskover-web-sunburst-screenshot.png?raw=true)
Gource visualization support (see videos below)
![diskover-gource](docs/diskover-gource1-screenshot.png?raw=true)

### diskover Gource videos

* [File modifications over time](https://youtu.be/InlfK8GQ-kM)
* [Realtime file crawl using 8 threads](https://youtu.be/qKLJjZ0TMqA)

## Installation Guide

### Requirements

* `Linux, OS X/macOS or Windows` (tested on OS X 10.11.6, Ubuntu 16.04 and Windows 7)
* `Python 2.7. or Python 3.5.` (tested on Python 2.7.10, 2.7.12, 3.5.3)
* `Python elasticsearch client module` [elasticsearch](https://pypi.python.org/pypi/elasticsearch) (tested on 5.3.0, 5.4.0)
* `Python requests module` [requests](https://pypi.python.org/pypi/requests)
* `Python scandir module` [scandir](https://pypi.python.org/pypi/scandir) (included in Python 3.5.)
* `Elasticsearch` (local or [AWS ES Service](https://aws.amazon.com/elasticsearch-service/), tested on Elasticsearch 5.3.0, 5.4.2)
* `Kibana` (tested on Kibana 5.3.0, 5.4.2)

### Windows Additional Requirements

* [CygWin](http://cygwin.com)
* [PyWin32](https://sourceforge.net/projects/pywin32/files/pywin32/)

### Optional Installs

* [diskover-web](https://github.com/shirosaidev/diskover-web) (diskover's web panel for searching/tagging files)
* [X-Pack](https://www.elastic.co/downloads/x-pack) (for graphs, reports, monitoring and http auth)
* [Gource](http://gource.io) (for Gource visualizations of diskover Elasticsearch data)

### Download

```sh
$ git clone https://github.com/shirosaidev/diskover.git
$ cd diskover
```

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

**Defaults for crawl with no flags is to only index files 5+ MB and 30+ days modified time. Use -h to see cli options.**

A successfull crawl should look like this:

```
   ___       ___       ___       ___       ___       ___       ___       ___
  /\  \     /\  \     /\  \     /\__\     /\  \     /\__\     /\  \     /\  \
 /::\  \   _\:\  \   /::\  \   /:/ _/_   /::\  \   /:/ _/_   /::\  \   /::\  \
/:/\:\__\ /\/::\__\ /\:\:\__\ /::-"\__\ /:/\:\__\ |::L/\__\ /::\:\__\ /::\:\__\
\:\/:/  / \::/\/__/ \:\:\/__/ \;:;-",-" \:\/:/  / |::::/  / \:\:\/  / \;:::/  /
 \::/  /   \:\__\    \::/  /   |:|  |    \::/  /   L;;/__/   \:\/  /   |:\/__/
  \/__/     \/__/     \/__/     \|__|     \/__/    v1.0.12    \/__/     \|__|
                                      https://github.com/shirosaidev/diskover

2017-05-17 21:17:09,254 [INFO][diskover] Connecting to Elasticsearch
2017-05-17 21:17:09,260 [INFO][diskover] Checking for ES index: diskover-2017.04.22
2017-05-17 21:17:09,262 [WARNING][diskover] ES index exists, deleting
2017-05-17 21:17:09,340 [INFO][diskover] Creating ES index
Crawling: [100%] |########################################| 8570/8570
2017-05-17 21:17:16,972 [INFO][diskover] Finished crawling
2017-05-17 21:17:16,973 [INFO][diskover] Directories Crawled: 8570
2017-05-17 21:17:16,973 [INFO][diskover] Files Indexed: 322
2017-05-17 21:17:16,973 [INFO][diskover] Elapsed time: 7.72081303596
```

## User Guide

[Read the wiki](https://github.com/shirosaidev/diskover/wiki) for more documentation on how to use diskover.

## Discussions/Questions

For discussions or questions about diskover, please ask on [Google Group](https://groups.google.com/forum/?hl=en#!forum/diskover).

## Bugs

For bugs about diskover, please use the [issues page](https://github.com/shirosaidev/diskover/issues).

## License

See the [license file](https://github.com/shirosaidev/diskover/blob/master/LICENSE).
