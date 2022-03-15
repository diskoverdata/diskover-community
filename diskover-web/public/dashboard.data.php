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
use Elasticsearch\Common\Exceptions\Missing404Exception;
error_reporting(E_ALL ^ E_NOTICE);


// Get info about index
$searchParams['index'] = $esIndex;
$searchParams['body'] = [
    'size' => 2,
    'query' => [
        'query_string' => [
            'query' => 'path:"'.$_SESSION['rootpath'].'" AND type:"indexinfo"'
        ]
    ]
];

try {
    $queryResponse = $client->search($searchParams);
} catch (Missing404Exception $e) {
    handleError("Selected indices are no longer available.");
} catch (Exception $e) {
    handleError('ES error: ' . $e->getMessage(), true);
}

$index_info = array();
foreach ($queryResponse['hits']['hits'] as $hit) {
    $index_info[] = $hit['_source'];
}

$totalfiles = 0;
$totalfilesize = 0;
$totalfilesizedu = 0;
$totaldirs = 0;
foreach ($index_info as $i) {
    $totalfiles += $i['file_count'];
    $totalfilesize += $i['file_size'];
    $totalfilesizedu += $i['file_size_du'];
    $totaldirs += $i['dir_count'];
}

// Get info about space
$searchParams['index'] = $esIndex;
$searchParams['body'] = [
    'size' => 1,
    'query' => [
        'query_string' => [
            'query' => 'path:"'.$_SESSION['rootpath'].'" AND type:"spaceinfo"'
        ]
    ]
];

try {
    $queryResponse = $client->search($searchParams);
} catch (Missing404Exception $e) {
    handleError("Selected indices are no longer available.");
} catch (Exception $e) {
    handleError('ES error: ' . $e->getMessage(), true);
}

$space_info = $queryResponse['hits']['hits'][0]['_source'];
$space_available = $space_info['available'];
$space_total = $space_info['total'];
$space_used = $space_info['used'];

// Get info about index2
if ($esIndex2 != "") {
    $searchParams['index'] = $esIndex2;
    $searchParams['body'] = [
        'size' => 2,
        'query' => [
            'query_string' => [
                'query' => 'path:"'.$_SESSION['rootpath'].'" AND type:"indexinfo"'
            ]
        ]
    ];

    $client2 = $mnclient->getClientByIndex($esIndex2);
    try {
        $queryResponse = $client2->search($searchParams);
    } catch (Missing404Exception $e) {
        handleError("Selected indices are no longer available.");
    } catch (Exception $e) {
        handleError('ES error: ' . $e->getMessage(), true);
    }

    $index2_info = array();
    foreach ($queryResponse['hits']['hits'] as $hit) {
        $index2_info[] = $hit['_source'];
    }

    // Get info about space
    $searchParams['index'] = $esIndex2;
    $searchParams['body'] = [
        'size' => 1,
        'query' => [
            'query_string' => [
                'query' => 'path:"'.$_SESSION['rootpath'].'" AND type:"spaceinfo"'
            ]
        ]
    ];

    try {
        $queryResponse = $client2->search($searchParams);
    } catch (Missing404Exception $e) {
        handleError("Selected indices are no longer available.");
    } catch (Exception $e) {
        handleError('ES error: ' . $e->getMessage(), true);
    }
    
    $space2_info = $queryResponse['hits']['hits'][0]['_source'];

    // calculate disk space available change between the two indices
    $space_change = number_format(changePercent($space_info['available'], $space2_info['available']), 1);
}

// Get recommended file delete size/count/cost
$file_recommended_delete_size = 0;
$file_recommended_delete_count = 0;
$file_recommended_delete_cost = 0;

$results = [];
$searchParams = [];

// Setup search query
$searchParams['index'] = $esIndex;

$searchParams['body'] = [
    'size' => 0,
    'track_total_hits' => true,
    'aggs' => [
        'total_size' => [
            'sum' => [
                'field' => 'size_du'
            ]
        ]
    ],
    'query' => [
        'query_string' => [
            'query' => 'mtime:[* TO now/m-6M/d] AND atime:[* TO now/m-6M/d] AND parent_path:' . escape_chars($_SESSION['rootpath']) .'* AND type:"file"'
        ]
    ]
];

$queryResponse = $client->search($searchParams);

// Get total count of recommended files to remove
$cleanlist_filecount = $queryResponse['hits']['total']['value'];

// Get total size of all recommended files to remove
$cleanlist_filesize = $queryResponse['aggregations']['total_size']['value'];

// Calculate percent removable from total files
if ($totalfiles > 0) {
    $percent_removable = round($cleanlist_filecount / $totalfiles * 100);
}

// get sizes of diff file types in index
$results = [];
$searchParams = [];

$fileGroups_sizes = [
    'docs' => 0, 'images' => 0, 'video' => 0, 'audio' => 0, 'apps' => 0,
    'programming' => 0, 'internet' => 0, 'system' => 0, 'data' => 0, 'disc' => 0,
    'compressed' => 0, 'trash' => 0
];
$fileGroups_totalsize = 0;

$fileGroups_extension = [];

$allextensions = "";

foreach ($fileGroups_sizes as $key => $value) {
    $extensions = "";
    $x = count($fileGroups_extensions[$key]);
    $n = 0;
    foreach ($fileGroups_extensions[$key] as $k => $v) {
        $extensions .= "$v";
        if ($n<$x-1) $extensions .= " OR ";
        $n++;
    }
    $allextensions .= $extensions;

    $searchParams['index'] = $esIndex;

    $query = 'extension:(' . $extensions . ') AND parent_path:' . escape_chars($_SESSION['rootpath']) .'* AND type:file';

    $fileGroups_extension[$key] = $query;

    $searchParams['body'] = [
        'size' => 0,
        'track_total_hits' => true,
        'query' => [
            'query_string' => [
                'query' => $query,
                'analyze_wildcard' => 'true'
            ]
        ],
        'aggs' => [
            'total_size' => [
                'sum' => [
                    'field' => 'size_du'
                ]
            ]
        ]
    ];

    // Send search query to Elasticsearch
    $queryResponse = $client->search($searchParams);

    // Get total size of all files with tag
    $fileGroups_sizes[$key] = $queryResponse['aggregations']['total_size']['value'];
    $fileGroups_totalsize += $fileGroups_sizes[$key];
}

$fileGroups_extension['other'] = 'NOT extension:(' . $allextensions . ') AND parent_path:' . escape_chars($_SESSION['rootpath']) .'* AND type:file';

$docs_percent = round($fileGroups_sizes['docs'] / $totalfilesizedu * 100);
$images_percent = round($fileGroups_sizes['images'] / $totalfilesizedu * 100);
$video_percent = round($fileGroups_sizes['video'] / $totalfilesizedu * 100);
$audio_percent = round($fileGroups_sizes['audio'] / $totalfilesizedu * 100);
$apps_percent = round($fileGroups_sizes['apps'] / $totalfilesizedu * 100);
$programming_percent = round($fileGroups_sizes['programming'] / $totalfilesizedu * 100);
$internet_percent = round($fileGroups_sizes['internet'] / $totalfilesizedu * 100);
$system_percent = round($fileGroups_sizes['system'] / $totalfilesizedu * 100);
$data_percent = round($fileGroups_sizes['data'] / $totalfilesizedu * 100);
$disc_percent = round($fileGroups_sizes['disc'] / $totalfilesizedu * 100);
$compressed_percent = round($fileGroups_sizes['compressed'] / $totalfilesizedu * 100);
$trash_percent = round($fileGroups_sizes['trash'] / $totalfilesizedu * 100);
$other_percent = 100 - ($docs_percent + $images_percent + $video_percent + $audio_percent +
        $apps_percent + $programming_percent + $internet_percent + $system_percent +
        $data_percent + $disc_percent + $compressed_percent + $trash_percent);
$other_size = $totalfilesizedu - $fileGroups_totalsize;


// Get average file and directory sizes
$results = [];
$searchParams = [];

// Setup search query
$searchParams['index'] = $esIndex;

$searchParams['body'] = [
    'size' => 0,
    'track_total_hits' => true,
    'query' => [
        'query_string' => [
            'query' => 'parent_path:' . escape_chars($_SESSION['rootpath']) .'* AND type:file'
        ]
    ],
    'aggs' => [
        'avg_size' => [
            'avg' => [
                'field' => 'size'
            ]
        ],
        'avg_size_du' => [
            'avg' => [
                'field' => 'size_du'
            ]
        ]
    ]
];

$queryResponse = $client->search($searchParams);

$avgfilesize = $queryResponse['aggregations']['avg_size']['value'];
$avgfilesizedu = $queryResponse['aggregations']['avg_size_du']['value'];

$searchParams['body'] = [
    'size' => 0,
    'track_total_hits' => true,
    'query' => [
        'query_string' => [
            'query' => 'parent_path:' . escape_chars($_SESSION['rootpath']) .'* AND type:directory'
        ]
    ],
    'aggs' => [
        'avg_size' => [
            'avg' => [
                'field' => 'size'
            ]
        ],
        'avg_size_du' => [
            'avg' => [
                'field' => 'size_du'
            ]
        ]
    ]
];

$queryResponse = $client->search($searchParams);

$avgdirsize = $queryResponse['aggregations']['avg_size']['value'];
$avgdirsizedu = $queryResponse['aggregations']['avg_size_du']['value'];

?>