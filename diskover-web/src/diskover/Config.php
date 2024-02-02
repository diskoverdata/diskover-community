<?php
/*
diskover-web community edition (ce)
https://github.com/diskoverdata/diskover-community/
https://diskoverdata.com

Copyright 2017-2023 Diskover Data, Inc.
"Community" portion of Diskover made available under the Apache 2.0 License found here:
https://www.diskoverdata.com/apache-license/

All other content is subject to the Diskover Data, Inc. end user license agreement found at:
https://www.diskoverdata.com/eula-subscriptions/

Diskover Data products and features for all versions found here:
https://www.diskoverdata.com/solutions/

*/

// diskover-web community edition (ce) config handling

namespace diskover;
error_reporting(E_ALL & ~E_WARNING & ~E_NOTICE & ~E_DEPRECATED);

class Config
{
    public $config;

    public function getConfig()
    {
        // load settings table in sqlite db
        // Load database and get config settings.
        $db = new ConfigDatabase();
        $db->connect();
        $config_db = $db->getConfigSettings();
        $config = (object) $config_db;
        return $config;
    }
}