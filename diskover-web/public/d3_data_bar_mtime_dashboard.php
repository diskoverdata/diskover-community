<?php
/*
diskover-web community edition (ce)
https://github.com/diskoverdata/diskover-community/
https://diskoverdata.com

Copyright 2017-2021 Diskover Data, Inc.
"Community" portion of Diskover made available under the Apache 2.0 License found here:
https://www.diskoverdata.com/apache-license/
 
All other content is subject to the Diskover Data, Inc. end user license agreement found at:
https://www.diskoverdata.com/eula-subscriptions/
  
Diskover Data products and features for all versions found here:
https://www.diskoverdata.com/solutions/

*/

require '../vendor/autoload.php';
use diskover\Constants;
require "../src/diskover/Diskover.php";
require "d3_inc.php";

// check if path in session cache
if ($_SESSION["diskover_cache_chartfilemtime_dashboard"][$esIndex][$_SESSION['rootpath']] && $_GET['usecache'] == 1) {
    $data = $_SESSION["diskover_cache_chartfilemtime_dashboard"][$esIndex][$_SESSION['rootpath']];
} else {
    // get dir total size and file count
    $dirinfo = get_dir_info_dashboard($client, $esIndex, $_SESSION['rootpath']);

    $data = [
        "name" => $_SESSION['rootpath'],
        "size" => $dirinfo[0],
        "count" => $dirinfo[2],
        "children" => get_file_mtime_dashboard($client, $esIndex, $_SESSION['rootpath'])
    ];

    // cache path data in session
    $_SESSION["diskover_cache_chartfilemtime_dashboard"][$esIndex][$_SESSION['rootpath']] = $data;
}

echo json_encode($data);