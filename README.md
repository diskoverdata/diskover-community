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


# User Guide

## Requirements

* `Python 2.7.` (tested on Python 2.7.10, have not tested on Python 3)
* `Python client for Elasticsearch`
* `GNU find command` (most likely you already have this)
* `Elasticsearch (local or aws es service)`
* `Kibana`


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
cd /some/path/you/want/to/crawl
sudo python /path/to/diskover.py
```


## Diskover CLI options

* `-h, --help` displays help
* `-d, --topdir` directory to start crawling from (default: .)
* `-m, --mtime` minimum days ago for modified time (default: 30)
* `-s, --minsize` minimum file size in MB (default: 5)
* `-t, --threads` number of threads to use (default: 2)
* `-v VERBOSE, --verbose` run in verbose level (default: 0)


## Config file

Diskcover will read a local config file (`diskover.cfg`). **It needs to be in the same directory as `diskover.py`**. Here you can exclude any directories and files you don't want to index separated by `,` (**spaces after comma are treated as part of file/directory name**). Elasticsearch hostname (endpoint), port and index name are also set here. If you are using AWS ES, set `aws = True` and `port = 443` and set the host to the endpoint in your AWS ES console. Lines beginning with `;` are comments and ignored by Diskover. If you are running Elasticsearch on your localhost or lan, set `aws = False` and the default port is `9200`.

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

The command line options for Diskover should help speed up the crawl times such as setting minimum file size and modified time. Also excluding certain files/directories will help. Running with verbose logging will increase crawl times.

You could also speed up the crawl by running multiple Diskover processes and bulk loading into different `diskover-<name>` indices in Elasticsearch. I haven't tested this but in theory that should help to pull in data faster for analysis. Diskover bulk loads data into Elasticsearch while the crawl is running so you can view in Kibana during the scan.

Here are some benchmarks running on my macbook pro, this includes time to crawl my local filesystem and index in Elasticsearch (in seconds) using the default of 2 threads. The files were all 1KB.

```sh
[2017-04-23 10:02:58] *** Directories Crawled: 10001
[2017-04-23 10:02:58] *** Files Indexed: 10000
[2017-04-23 10:02:58] *** Elapsed time: 16.2423961163

[2017-04-23 10:46:24] *** Directories Crawled: 100001
[2017-04-23 10:46:24] *** Files Indexed: 100000
[2017-04-23 10:46:24] *** Elapsed time: 167.5496099
```


# Elasticsearch

## Indices

Diskover creates an index with the name from the config file. **If an existing index exists with the same name, it will be deleted and a new index created.** If you are doing crawls every month you could name the indices diskover-2017.04, diskover-2017.05, diskover-2017-06, etc.


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
