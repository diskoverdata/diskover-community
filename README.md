# Diskover FileSystem Crawler

Welcome to Diskover FS Crawler

What if you are running low on disk space. You need to free some up, by finding files that are a waste of space and deleting them (or moving them to archive). How do you find the right files to delete?

Diskover helps to index files from your local file system or nfs mounts.
It crawls your file system and indexes files and adds to [Elasticsearch](https://www.elastic.co) or [Amazon Elasticsearch Service](https://aws.amazon.com/elasticsearch-service/). It is written in Python and uses multi-threading to speed up indexing crawl times. The indexed files are bulk added and streamed into Elasticsearch while the crawl is running allowing you to visualize the data in [Kibana](https://www.elastic.co/products/kibana) without having to wait until the crawl is finished.

![alt tag](https://github.com/shirosaidev/diskover/blob/master/kibana-screenshot.png)

# Installation Guide

## Download diskover

```sh
git clone https://github.com/shirosaidev/diskover.git
cd diskover
```

The distribution contains:

```
$ tree
.
├── LICENSE
├── README.md
├── diskover.cfg
├── diskover.py
├── export.json
└── kibana-screenshot.png
```

## Update diskover

```sh
cd diskover
git pull
```


# User Guide

## Requirements

* `Linux or Mac OS X` (tested on Mac OS X 10.11.6 and Ubuntu 16.04, have not tested on Windows)
* `Python 2.7.` (tested on Python 2.7.10 and 2.7.12, have not tested on Python 3)
* `Python client for Elasticsearch`
* `GNU find command` (most likely you already have this)
* `Elasticsearch` (local or AWS ES service, tested on Elasticsearch 5.3.0)
* `Kibana` (tested on Kibana 5.3.0)


## Getting Started

You need to have at least **Python 2.7.** and have installed Python client for Elasticsearch using `pip`:

```sh
python --version
```

```sh
pip install elasticsearch
```

If you don't have pip, you can install it with:

```sh
sudo easy_install pip
```

You also need GNU `find` command which is used for building the directory queue list. It needs to be in your PATH, which is usually in `/usr/bin`:

```sh
which find
```

Start Diskcover FS crawler as root user with:

```sh
cd /path/you/want/to/crawl
sudo python /path/to/diskover.py
```

A successfull crawl should look like this:

```sh

   ___       ___       ___       ___       ___       ___       ___       ___
  /\  \     /\  \     /\  \     /\__\     /\  \     /\__\     /\  \     /\  \
 /::\  \   _\:\  \   /::\  \   /:/ _/_   /::\  \   /:/ _/_   /::\  \   /::\  \
/:/\:\__\ /\/::\__\ /\:\:\__\ /::-"\__\ /:/\:\__\ |::L/\__\ /::\:\__\ /::\:\__\
\:\/:/  / \::/\/__/ \:\:\/__/ \;:;-",-" \:\/:/  / |::::/  / \:\:\/  / \;:::/  /
 \::/  /   \:\__\    \::/  /   |:|  |    \::/  /   L;;/__/   \:\/  /   |:\/__/
  \/__/     \/__/     \/__/     \|__|     \/__/    v1.0.1     \/__/     \|__|
                                      https://github.com/shirosaidev/diskover


[2017-04-27 23:02:05] [status] Connecting to Elasticsearch
[2017-04-27 23:02:05] [info] Checking for ES index
[2017-04-27 23:02:05] [warning] ES index exists, deleting
[2017-04-27 23:02:05] [info] Creating ES index
[2017-04-27 23:02:05] [status] Finding directories to crawl
Crawling: [100%] |████████████████████████████████████████| 7743/7744
[2017-04-27 23:02:11] [info] Directories Crawled: 7744
[2017-04-27 23:02:11] [info] Files Indexed: 350
[2017-04-27 23:02:11] [info] Elapsed time: 6.34155106544
```


## Diskover CLI options

* `-h, --help` displays help
* `-d TOPDIR, --topdir=TOPDIR` directory to start crawling from (default: .)
* `-m DAYS, --mtime=DAYS` minimum days ago for modified time (default: 30)
* `-s MINSIZE, --minsize=MINSIZE` minimum file size in MB (default: 5)
* `-t, NUM_THREADS, --threads=NUM_THREADS` number of threads to use (default: 2)
* `-i, INDEXNAME, --index=INDEXNAME` elasticsearch index name (default: from config)
* `-v VERBOSE, --verbose=VERBOSE` run in verbose level (default: 0)
* `--debug=DEBUG, --debug=DEBUG` run in debug mode (default: false)


## Config file

Diskcover will read a local config file (`diskover.cfg`). **It needs to be in the same directory as `diskover.py`**.

Here you can exclude any directories and files you don't want to index separated by `,` (**spaces after comma are treated as part of file/directory name**).

Elasticsearch hostname (endpoint), port and index name are also set here. If you are using AWS ES, set `aws = True` and `port = 443` and set the host to the endpoint in your AWS ES console. If you are running Elasticsearch on your localhost or lan, set `aws = False` and the default port is `9200`.

Lines beginning with `;` are comments and ignored by Diskover.

```
[excluded_dirs]
dirs = .snapshot,DO_NOT_DELETE

[excluded_files]
files = Thumbs.db,.DS_Store,._.DS_Store,.localized,desktop.ini

[elasticsearch]
aws = False
;host = search-diskover-es-cluster-eg3yztrvzb6qucroyyjk2vokza.ap-northeast-1.es.amazonaws.com
;port = 443
host = localhost
port = 9200
indexname = diskover-2017.04.22
```

## Benchmarks and speeding up crawl times

Diskover skips empty directories and will only index files that are older than `modified time` and larger than `minimum file size` from the command line options. Excluding certain files/directories will help speed up crawl times as well. **Running with verbose logging will increase crawl times**.

For example, if you wanted to find all the old files that are larger than 10MB that haven't been modified in more than 6 months, you could run Diskover with:

```sh
cd /path/you/want/to/crawl
sudo python /path/to/diskover.py -m 180 -s 10
```

You could also speed up the crawl by running multiple Diskover processes and bulk loading into different `diskover-<name>` indices in Elasticsearch. I haven't tested this but in theory that should help to pull in data faster for analysis. Diskover bulk loads data into Elasticsearch while the crawl is running so you can view in Kibana during the scan.

Here are some benchmarks running on my macbook pro, this includes time to crawl my local filesystem and index in Elasticsearch (in seconds) using the default of 2 threads. The files were all 1KB.

```sh
[2017-04-23 10:02:58] [info] Directories Crawled: 10001
[2017-04-23 10:02:58] [info] Files Indexed: 10000
[2017-04-23 10:02:58] [info] Elapsed time: 16.2423961163

[2017-04-23 10:46:24] [info] Directories Crawled: 100001
[2017-04-23 10:46:24] [info] Files Indexed: 100000
[2017-04-23 10:46:24] [info] Elapsed time: 167.5496099
```


# Elasticsearch

## Indices

Diskover creates an index with the name from the config file or from the cli option `-i`. **If an existing index exists with the same name, it will be deleted and a new index created.** If you are doing crawls every week for example, you could name the indices diskover-2017.04.09, diskover-2017.04.16, diskover-2017.04.23, etc.


## Generated fields

Diskover creates the following fields :

|         Field        |                Description                  |                    Example                  |
|----------------------|---------------------------------------------|---------------------------------------------|
| `last_modified`      | Last modification date                      | `1389220808`                                |
| `last_access`        | Last access date                            | `1482435694`                                |
| `last_change`        | Last change date                            | `1389220808`                                |
| `indexing_date`      | Indexing date                               | `1492612283`                                |
| `filesize`           | File size in bytes                          | `50502536`                                  |
| `filename`           | Original file name                          | `"mypic.png"`                               |
| `extension`          | Original file name extension                | `"png"`                                     |
| `path_parent`        | Parent path name of file                    | `"/tmp/dir1/dir2"`                          |
| `path_full`          | Actual real path name                       | `"/tmp/dir1/dir2/mypic.png"`                |
| `owner`              | Owner name                                  | `"cpark"`                                   |
| `group`              | Group name                                  | `"staff"`                                   |
| `hardlinks`          | Hardlink count                              | `1`                                         |
| `inode`              | Inode number                                | `652490`                                    |


## Kibana

For the index pattern use `diskover-*`. **Make sure the `Index contains time-based events` box is `unchecked`** when you create index patterns.


### Diskover Dashboard

To use the Diskover dashboard (screenshot), import the saved objects file `export.json` into Kibana for the dashboard visualizations. In Kibana go to `Management > Saved Objects > Import`.


### Kibana Field Formatting

This will help make the dashboard easier to read like in the screenshot for filesize and dates. In Kibana go to `Management > Index Patterns > diskover-*`. In the `Fields tab` click the `edit icon` under controls column for `filesize` field. Change the format to `bytes` and click `Update Field`. For `access_time, modified_time, and change_time`, edit the fields and change the format to `date` and set the format pattern to `MM-DD-YYYY, HH:mm` and click `Update Field`.


# License

```
This software is licensed under the Apache 2 license, quoted below.

Copyright 2017 Chris Park

Licensed under the Apache License, Version 2.0 (the "License"); you may not
use this file except in compliance with the License. You may obtain a copy of
the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
License for the specific language governing permissions and limitations under
the License.
```
