<?php
/*
diskover-web community edition (ce)
https://github.com/diskoverdata/diskover-community/
https://diskoverdata.com

Copyright 2017-2022 Diskover Data, Inc.
"Community" portion of Diskover made available under the Apache 2.0 License found here:
https://www.diskoverdata.com/apache-license/

All other content is subject to the Diskover Data, Inc. end user license agreement found at:
https://www.diskoverdata.com/eula-subscriptions/

Diskover Data products and features for all versions found here:
https://www.diskoverdata.com/solutions/

*/

// diskover-web community edition (ce) config handling

namespace diskover;
use diskover\Constants;
use ReflectionClass;

class Config
{
    public $config;

    public function getConfig()
    {
        require 'config_defaults.php';
        // check for any missing config settings in Constants.php and if any are missing use default
        $config = new Constants;
        $refl = new ReflectionClass('diskover\Constants');
        $consts = $refl->getConstants();
        foreach ($config_defaults as $configkey => $configval) {
            if (!array_key_exists($configkey, $consts)) {
                error_log("Missing config setting $configkey. Using default.");
                $config->{$configkey} = $configval;
            } else {
                $config->{$configkey} = $consts[$configkey];
            }
        }
        return $config;
    }
}
