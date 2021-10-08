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
if ($_SESSION["diskover_cache_dirsize_search"][$esIndex][$path] && $_GET['usecache'] == 1) {
    $data = $_SESSION["diskover_cache_dirsize_search"][$esIndex][$path];
} else {
    // get mtime in ES format
    $time = gettime($time);

    // get dir total size and file count
    $dirinfo = get_dir_info($client, $esIndex, $path);

    $data = [
        "name" => $path,
        "size" => $dirinfo[0],
        "count" => $dirinfo[1],
        "count_files" => $dirinfo[2],
        "count_subdirs" => $dirinfo[3],
        "modified" => $dirinfo[4],
        "type" => 'directory',
        "children" => walk_tree($client, $esIndex, $path, $filter, $time, $depth = 0, $maxdepth = 1, $use_count, $show_files, $sortdirs = 1, $maxdirs = 10)
    ];

    // cache path data in session
    $_SESSION["diskover_cache_dirsize_search"][$esIndex][$path] = $data;
}

echo json_encode($data);
