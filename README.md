# diskover - Elasticsearch file system crawler and Kibana disk usage analyzer

![diskover](docs/diskover.png?raw=True)

diskover is a file system crawler that helps index your files in [Elasticsearch](https://www.elastic.co) and visualize your disk usage in [Kibana](https://www.elastic.co/products/kibana). It crawls and indexes your files on a local or remote server using nfs or cifs. File metadata is bulk added and streamed into Elasticsearch allowing you to **visualize your data in Kibana without having to wait until the crawl is finished**. diskover is written in Python and runs in Linux, OS X/macOS and Windows.


### Screenshots

Kibana dashboard
![kibana-screenshot](docs/kibana-dashboarddark-screenshot.png?raw=True)
diskover web
![diskover-web-screenshot](docs/diskover-web-simplesearch-screenshot.png?raw=True)


### diskover web

[diskover web](diskover_web/README.md) is the front-end for diskover used for searching and tagging files in your Elasticsearch indices. It is designed to help quickly search your storage servers and tag files for clean up.


### Installation Guide

#### Requirements

* `Linux, OS X/macOS or Windows` (tested on OS X 10.11.6, Ubuntu 16.04 and Windows 7)
* `Python 2.7. or Python 3.5.` (tested on Python 2.7.10, 2.7.12, 3.5.3)
* `Python elasticsearch client module` [elasticsearch](https://pypi.python.org/pypi/elasticsearch/5.3.0)
* `Python requests module` [requests](https://pypi.python.org/pypi/requests)
* `Python scandir module` [scandir](https://pypi.python.org/pypi/scandir) (included in Python 3.5.)
* `Elasticsearch` (local or [AWS ES Service](https://aws.amazon.com/elasticsearch-service/), tested on Elasticsearch 5.3.0)
* `Kibana` (tested on Kibana 5.3.0)

#### Windows Additional Requirements

* [CygWin](http://cygwin.com)
* [PyWin32](https://sourceforge.net/projects/pywin32/files/pywin32/)

#### Optional Install

* [X-Pack](https://www.elastic.co/downloads/x-pack) (for graphs, reports, monitoring and http auth)

#### Download

```sh
$ git clone https://github.com/shirosaidev/diskover.git
$ cd diskover
```

You need to have at least **Python 2.7. or Python 3.5.** and have installed required Python dependencies using `pip`.

```sh
$ sudo pip install -r requirements.txt
```

### User Guide

#### Getting Started

Start diskover as root user with:

```sh
$ cd /path/you/want/to/crawl
$ sudo python /path/to/diskover.py
```

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


#### diskover CLI arguments

```
usage: diskover.py [-h] [-d TOPDIR] [-m MTIME] [-s MINSIZE] [-t THREADS]
                   [-i INDEX] [-n] [--tagdupes] [--version] [-v] [--debug]

optional arguments:
  -h, --help            show this help message and exit
  -d TOPDIR, --topdir TOPDIR
                        Directory to start crawling from (default: .)
  -m MTIME, --mtime MTIME
                        Minimum days ago for modified time (default: 30)
  -s MINSIZE, --minsize MINSIZE
                        Minimum file size in MB (default: 5)
  -t THREADS, --threads THREADS
                        Number of threads to use (default: 2)
  -i INDEX, --index INDEX
                        Elasticsearch index name (default: from config)
  -n, --nodelete        Do not delete existing index (default: delete index)
  --tagdupes            Tags duplicate files (default: don't tag)
  --version             Prints version and exits
  -v, --verbose         Increase output verbosity
  --debug               Debug message output
```


#### Config file

diskover will read a local config file `diskover.cfg`. **It needs to be in the same directory as `diskover.py`**.

Here you can exclude any directories and files you don't want to index separated by `,` (**spaces after comma are treated as part of file/directory name**).

Elasticsearch hostname (endpoint), port and index name are also set here. If you are using AWS ES, set `aws = True` and `port = 443` and set the host to the endpoint in your AWS ES console. If you are running Elasticsearch on your localhost or lan, comment out or set `aws = False` and the default port is `9200`. **If you installed Elasticsearch X-Pack, uncomment and set user/password for http-auth**.

Lines beginning with `;` are comments and ignored by diskover.

```
[excluded_dirs]
; directories you want to exclude from crawl
dirs = .snapshot,DO_NOT_DELETE,Databases

[excluded_files]
; files you want to exclude from crawl
files = Thumbs.db,.DS_Store,._.DS_Store,.localized,desktop.ini

[elasticsearch]
; uncomment the below three lines if you are using AWS ES
;aws = True
;host = search-diskover-es-cluster-eg3yztrvzb6qucroyyjk2vokza.ap-northeast-1.es.amazonaws.com
;port = 443
; below two lines are for local ES, comment out if you are using AWS ES
host = localhost
port = 9200
; uncomment the below two lines if you installed X-Pack, for http-auth
;user = elastic
;password = changeme
; index name for ES, cli arg overwrites this
indexname = diskover-2017.04.22
```

#### Speeding up crawl times

diskover **skips empty directories and empty files** and will **only index files >= `modified time` and >= `minimum file size`** from the command line options. Excluding certain files/directories will help speed up crawl times as well. **Running with verbose logging will increase crawl times**.

For example, if you wanted to find and index files that are >= 10 MB that have been modified >= 180 days ago, you could run diskover with:

```sh
$ cd /path/you/want/to/crawl
$ sudo python /path/to/diskover.py -m 180 -s 10
```

You could also speed up the crawl by running multiple `diskover.py` processes and bulk loading into the same `diskover-<name>` index in Elasticsearch. Below is a diagram showing this example.

![diskover-diagram](docs/diskover-diagram.png?raw=True)

#### Benchmarks

Here are some benchmarks running on my Macbook Pro, this includes time to crawl my local filesystem and index in Elasticsearch (in seconds) using the default of 2 threads and single `diskover.py` running.

```
Directories Crawled: 10001
Files Indexed: 10000
Elapsed time: 16.2423961163

Directories Crawled: 100001
Files Indexed: 100000
Elapsed time: 167.5496099
```


### Elasticsearch

#### Indices

diskover creates an index with the name from the config file or from the cli option `-i`. **If an existing index exists with the same name, it will be deleted and a new index created, unless `-n or --nodelete` cli argument is used**. 

If you are doing crawls every week for example, you could name the indices diskover-2017.04.09, diskover-2017.04.16, diskover-2017.04.23, etc. **Index names are required to be `diskover-<string>`**.

#### Append data to existing index

If you are running concurrent `diskover.py` processes you will need to use the `-n or --nodelete` cli argument to append  data to an existing index. See above diagram for example.

#### Duplicate files

![kibana-screenshot](docs/kibana-dashboard-dupes-screenshot.png?raw=True)

If you run `diskover.py` using the `--tagdupes` flag, files which are duplicates (based on same filehash field) will have their `is_dupe` field set to `true`. Default for `is_dupe` is `false`.

#### Generated fields

diskover creates the following fields:

|         Field        |                Description                  |                    Example                  |
|----------------------|---------------------------------------------|---------------------------------------------|
| `last_modified`      | Last modification date                      | `2017-03-15T19:26:28`                       |
| `last_access`        | Last access date                            | `2017-05-04T06:03:34`                       |
| `last_change`        | Last change date                            | `2017-04-20T05:21:49`                       |
| `indexing_date`      | Indexing date                               | `2017-05-17T06:09:12`                       |
| `filesize`           | File size in bytes                          | `50502536`                                  |
| `filename`           | Original file name                          | `"mypic.png"`                               |
| `extension`          | Original file name extension                | `"png"`                                     |
| `path_parent`        | Parent path name of file                    | `"/tmp/dir1/dir2"`                          |
| `path_full`          | Actual real path name                       | `"/tmp/dir1/dir2/mypic.png"`                |
| `owner`              | Owner name                                  | `"cpark"`                                   |
| `group`              | Group name                                  | `"staff"`                                   |
| `hardlinks`          | Hardlink count                              | `1`                                         |
| `inode`              | Inode number                                | `652490`                                    |
| `filehash`           | MD5 hash of file                            | `3a6949b4b74846a482016d0779560327`          |
| `tag`                | File tag for diskover web                   | `untagged`                                  |
| `is_dupe`            | Duplicate file                              | `false`                                     |

**Note: All date fields are stored as UTC time in Elasticsearch. Kibana displays dates using your local timezone.**

#### Filehash

In order to speed up crawl times, a md5 hash for each file is made from combining the strings `filename+filesize+last_modified` and hashing that string, rather than the contents of the file. This seems to be a fast high-level way to create a hash of the file. **You should run the md5 command on the files to compare their hashes before you delete the dupes**.

### Kibana

For the index pattern use `diskover-*`. **Make sure the `Index contains time-based events` box is `unchecked`** when you create index patterns. You could also use `modified_time` as your timestamp if you want to filter using time ranges in Kibana. This could be useful if you didn't run the crawl using an old `-m` modified file time.

#### diskover dashboard

![kibana-screenshot](docs/kibana-dashboardlight-screenshot.png?raw=True)

To use the diskover dashboards, import the saved objects file `export.json` into Kibana for the dashboard visualizations. In Kibana go to `Management > Saved Objects > Import`.

If nothing is showing in the dashboard, go to `Management > Index Patterns > diskover-*` and then hit the `refresh icon`.

#### Kibana Field Formatting

This will help make the dashboard easier to read like in the screenshot for filesize and dates. In Kibana go to `Management > Index Patterns > diskover-*`. In the `Fields tab` click the `edit icon` under controls column for `filesize` field. Change the format to `bytes` and click `Update Field`. For `access_time, modified_time, and change_time`, edit the fields and change the format to `date` and set the format pattern to `MM-DD-YYYY, HH:mm` and click `Update Field`.

#### Kibana Search Filters

Once you have imported the `export.json` into Kibana, in Kibana's `Discover` page click `open`. There will be a few saved searches in there to help you filter for old files and find duplicate files.

Here are some filter examples:

* `last_modified:[now-5y TO now-3M]` filters files that haven't been modified in over 3 months and less than 5 years
* `last_modified:[now-5y TO now-6M] AND last_access:[now-5y TO now-6M]` filters files that haven't been modified or accessed in over 6 months and less than 5 years
* `last_modified:[now-5y TO now-1y] AND last_access:[now-5y TO now-1y]` filters files that haven't been modified or access in over 1 year and less than 5 years
* `extension:(jpg OR gif OR png OR tif OR tiff OR dpx OR exr OR psd OR bmp OR tga)` filters for image files
* `extension:(aif OR iff OR m3u OR m4a OR mid OR mp3 OR mpa OR wav OR wma)` filters for audio files
* `extension:(asf OR avi OR flv OR m4v OR mov OR mp4 OR mpg OR rm OR vob OR wmv)` filters for video files
* `extension:(cache OR tmp OR temp OR bak OR old)` filters for temp files
* `extension:(7z OR deb OR gz OR pkg OR rar OR rpm OR tar OR zip OR zipx)` filters for compressed files
* `filename:img*.dpx` filters for image sequence img001.dpx, img002.dpx, im003.dpx, etc.
* `is_dupe:true` filters for duplicate files

#### Tracking directory tree size over time

To track a directory tree's change in size over time, create a new index each time crawling from the top-level directory of the project.

Every week or month for example: diskover-PROJA-2017.05.10, diskover-PROJA-2017.05.17, etc.

Then create a new Kibana index pattern `diskover-PROJA-*` to filter to just those indices.

To visualy see the change over time, create a line chart in Kibana using `sum of filesize` for `y-axis` and set `x-axis` to `date-histogram` using `indexing_date` field. Set `interval` to `weekly` or `monthly`.

### X-Pack

#### Graphs

To create graphs you need to install [X-Pack](https://www.elastic.co/downloads/x-pack). After X-Pack is installed, edit `diskover.cfg` for http auth credentials since X-Pack adds http auth to Elasticsearch and Kibana.

#### Dupes graph

![kibana-screenshot](docs/kibana-graph-dupes-screenshot.png?raw=True)

* index pattern: `diskover-*`
* verticies field source #1: `filehash` set to `50 max terms per hop`
* verticies field source #2: `inode` set to `50 max terms per hop`
* verticies field source #3: `path_parent` set to `50 max terms per hop`
* settings: uncheck `Significant links` and set `Certainty to 1`
* search filter: `hardlinks: 1 AND is_dupe: true`

#### Hardlinks graph

![kibana-screenshot](docs/kibana-graph-hardlinks-screenshot.png?raw=True)

* index pattern: `diskover-*`
* verticies field source #1: `path_parent` set to `50 max terms per hop`
* verticies field source #2: `inode` set to `50 max terms per hop`
* settings: uncheck `Significant links` and set `Certainty to 1`
* search filter: `hardlinks: >1`


## License

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
