# diskover web

diskover web is the front-end for [diskover](../README.md), allowing you to manage your files by searching and tagging files for deletion, archival or keeping. It is written in PHP, [Bootstrap](http://getbootstrap.com/) and [jQuery](https://jquery.com/).

### Screenshots

![diskover web dashboard](../docs/diskover-web-dashboard-screenshot.png?raw=True)
![diskover web simple search](../docs/diskover-web-simplesearch-screenshot.png?raw=True)
![diskover web advanced file view](../docs/diskover-web-advancedsearch-screenshot.png?raw=True)
![diskover web search results](../docs/diskover-web-searchresults-screenshot.png?raw=True)
![diskover web file view](../docs/diskover-web-fileview-screenshot.png?raw=True)

### Installation Guide

#### Requirements

* `Linux` (tested on Ubuntu 16.04)
* `PHP 7.0` (tested on PHP 7.0.15)
* `Composer Dependency Manager for PHP`
* `PHP client for Elasticsearch` (elasticsearch-php)
* `Elasticsearch` (tested on Elasticsearch 5.3.0)
* `Apache or Nginx` (if you don't want to use PHP built-in web server)

#### Download

Download diskover if you haven't already.

```sh
$ git clone https://github.com/shirosaidev/diskover.git
$ cd diskover
```

#### Install application dependencies

```sh
$ cd diskover_web
$ composer install
```


### User Guide

#### Getting Started

Edit diskover web settings in `src/diskover/Constants.php`.

```
<?php

namespace diskover;

class Constants {
    // set to your Elasticearch host or ip
    const ES_HOST = 'localhost';
    // don't change following two lines
    const ES_INDEX = 'diskover-*';
    const ES_TYPE = 'file';
    // set following two lines if using X-Pack http-auth
    const ES_USER = '';
    const ES_PASS = '';
}
```

Create index.php symlink.

```sh
$ cd public
$ ln -s dashboard.php index.php
```

Start diskover web using PHP's built-in web server.

```sh
$ cd public
$ php -S <IP>:8000
```

By default diskover web will communicate with the Elasticsearch API at `http://<ES_HOST>:9200`. If you are running ES 
on a different port than default 9200, you will need to pass this information to diskover web when starting
it up via an environment variable:

```sh
$ APP_ES_PORT=<PORT> php -S <IP>:8000
```

Open your web browser and visit `http://<IP>:8000`.


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
