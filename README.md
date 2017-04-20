# Diskover FileSystem Crawler

Welcome to Diskover FS Crawler 

This crawler helps to index files from your local file system or nfs mounts.
It crawls your file system and indexes files and adds to [Elasticsearch](https://www.elastic.co) or [Amazon Elasticsearch Service](https://aws.amazon.com/elasticsearch-service/). It is written in Python using Queue and threading modules for multi-threading the indexing. The indexed files are bulk added and streamed into Elasticsearch while the crawl is running allowing you to visualize the data in Kibana without having to wait until the crawl is finished.

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

## Getting Started

You need to have at least **Python 2.7.** and have installed Python client for Elasticsearch using `pip`:

```sh
pip install elasticsearch
```

You also need GNU `find` command which is used for building the directory queue list. It needs to be in your PATH, which is usually in `/usr/bin`:

```sh
which find
```

Start Diskcover FS crawler as root user with:

```sh
sudo python diskover.py
```


## Diskover CLI options

* `-h, --help` displays help
* `-d, --topdir` directory to start crawling from (default: .)
* `-m, --mtime` minimum days ago for modified time (default: 30)
* `-s, --minsize` minimum file size in MB (default: 5)
* `-t, --threads` number of threads to use (default: 2)


## Config file

Diskcover will read a local config file (`diskover.cfg`). Here you can exclude any directories and files you don't want to index separated by comma. Elasticsearch hostname (endpoint), port and index name are also set here.

```
[excluded_dirs]
dirs = .snapshot

[excluded_files]
files = Thumbs.db, .DS_Store, ._.DS_Store, .localized

[elasticsearch]
aws = False
;host = search-crawl-es-cluster-hr4yztrvzb7qucroyyjk1vokyb.ap-northeast-1.es.amazonaws.com
;port = 443
host = localhost
port = 9200
indexname = logstash-diskover
```


# Elasticsearch

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


## Saved objects for Diskover Kibana dashboard

You can import the saved objects file `export.json` into Kibana for the dashboard visualizations in `kibana-screenshot.png`. In Kibana go to Management > Saved Objects > Import.


# License

```
This software is licensed under the Apache 2 license, quoted below.

Copyright 2016-2017 Chris Park

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
