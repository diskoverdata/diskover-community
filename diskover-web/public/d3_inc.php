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
error_reporting(E_ALL ^ E_NOTICE);


// get path from cookie
$path = (isset($_GET['path'])) ? $_GET['path'] : getCookie('path');
if (empty($path)) {
    $path = $_SESSION['rootpath'];
}
// remove any trailing slash (unless root)
if ($path !== "/") {
    $path = rtrim($path, '/');
}


function get_dir_info_dashboard($client, $index, $path) {
    // Get total directory size, count (files/subdirs), mtime from Elasticsearch (recursive) for path
    $totalsize = 0;
    $totalcount = 0;
    $totalcount_files = 0;
    $totalcount_subdirs = 0;
    $searchParams['body'] = [];

    // get dir size and items (files/subdirs) from directory doc

    // Setup search query
    $searchParams['index'] = $index;

    // escape any special characters in path
    $escapedpath = escape_chars($path);

    if ($path === '/') {  // root /
        $searchParams['body'] = [
            'size' => 1,
            '_source' => ["size","size_du","file_count","dir_count","mtime"],
            'query' => [
                'query_string' => [
                    'query' => 'parent_path: ' . $escapedpath . ' AND name: "" AND type:"directory"'
                ]
            ]
        ];
    } else {
        $p = escape_chars(dirname($path));
        $f = escape_chars(basename($path));
        $searchParams['body'] = [
            'size' => 1,
            '_source' => ["size","size_du","file_count","dir_count","mtime"],
            'query' => [
                'query_string' => [
                    'query' => 'parent_path: ' . $p . ' AND name: ' . $f . ' AND type:"directory"'
                ]
            ]
        ];
    }

    try {
        // Send search query to Elasticsearch
        $queryResponse = $client->search($searchParams);
    }
    catch(Exception $e) {
        handleError('ES error: ' . $e->getMessage(), false);
    }

    // Get total count of files
    $totalcount_files = (int)$queryResponse['hits']['hits'][0]['_source']['file_count'];

    // Get total count of subdirs
    $totalcount_subdirs = (int)$queryResponse['hits']['hits'][0]['_source']['dir_count'];

    // Get total count (files+subdirs)
    $totalcount = (int)$totalcount_files + $totalcount_subdirs;

    // Get total size of directory and all subdirs
    $totalsize = (int)$queryResponse['hits']['hits'][0]['_source'][$_COOKIE['sizefield']];

    // Get directory modified time
    $modified = utcTimeToLocal($queryResponse['hits']['hits'][0]['_source']['mtime']);

    // Create dirinfo list with total size (of all files), total count (file items/subdir items) and dir modified time
    $dirinfo = [$totalsize, $totalcount, $totalcount_files, $totalcount_subdirs, $modified];

    return $dirinfo;
}

function get_dir_info($client, $index, $path) {
    // Get total directory size, count (files/subdirs), mtime from Elasticsearch (recursive) for path
    $totalsize = 0;
    $totalcount = 0;
    $totalcount_files = 0;
    $totalcount_subdirs = 0;
    $searchParams['body'] = [];

    // get dir size and items (files/subdirs) from directory doc

    // Setup search query
    $searchParams['index'] = $index;

    // escape any special characters in path
    $escapedpath = escape_chars($path);

    if ($path === '/') {  // root /
        $searchParams['body'] = [
            'size' => 1,
            '_source' => ["size","size_du","file_count","dir_count","mtime"],
            'query' => [
                'query_string' => [
                    'query' => 'parent_path: ' . $escapedpath . ' AND name: "" AND type:"directory"'
                ]
            ]
        ];
    } else {
        $p = escape_chars(dirname($path));
        $f = escape_chars(basename($path));
        $searchParams['body'] = [
            'size' => 1,
            '_source' => ["size","size_du","file_count","dir_count","mtime"],
            'query' => [
                'query_string' => [
                    'query' => 'parent_path: ' . $p . ' AND name: ' . $f . ' AND type:"directory"'
                ]
            ]
        ];
    }

    try {
        // Send search query to Elasticsearch
        $queryResponse = $client->search($searchParams);
    }
    catch(Exception $e) {
        handleError('ES error: ' . $e->getMessage(), false);
    }

    // Get total count of files
    $totalcount_files = (int)$queryResponse['hits']['hits'][0]['_source']['file_count'];

    // Get total count of subdirs
    $totalcount_subdirs = (int)$queryResponse['hits']['hits'][0]['_source']['dir_count'];

    // Get total count (files+subdirs)
    $totalcount = (int)$totalcount_files + $totalcount_subdirs;

    // Get total size of directory and all subdirs
    $totalsize = (int)$queryResponse['hits']['hits'][0]['_source'][$_COOKIE['sizefield']];

    // Get directory modified time
    $modified = utcTimeToLocal($queryResponse['hits']['hits'][0]['_source']['mtime']);

    // Create dirinfo list with total size (of all files), total count (file items/subdir items) and dir modified time
    $dirinfo = [$totalsize, $totalcount, $totalcount_files, $totalcount_subdirs, $modified];

    return $dirinfo;
}

function get_files($client, $index, $path, $filter, $time, $maxfiles=100) {
    // gets the 100 largest files in the current directory (path)
    // sorted by size/filename
    $items = [];
    $searchParams['body'] = [];

    // Setup search query
    $searchParams['index'] = $index;

    // search size
    $searchParams['size'] = $maxfiles;

    $escapedpath = escape_chars($path);
    $searchParams['body'] = [
                '_source' => ["parent_path","name","size","size_du","mtime"],
                'query' => [
                    'query_string' => [
                        'query' => 'parent_path: ' . $escapedpath . ' AND '.$_COOKIE['sizefield'].': >=' . $filter . ' AND mtime: [* TO ' . $time . '] AND type:"file"'
                    ]
                ],
                'sort' => [
                    'size' => [
                    'order' => 'desc'
                    ],
                    'name' => [
                    'order' => 'asc'
                    ]
                ]
        ];

    // check if we need to apply any filters to search
    $searchParams = filterSearchResults($searchParams);

    try {
        $queryResponse = $client->search($searchParams);
    }
    catch(Exception $e) {
        handleError('ES error: ' . $e->getMessage(), false);
    }

    // Get files
    $results = $queryResponse['hits']['hits'];

    // Add files to items array
    foreach ($results as $result) {
        if ($path === '/') {  // root /
            $items[] = [
                "name" => $result['_source']['parent_path'] . $result['_source']['name'],
                "size" => $result['_source'][$_COOKIE['sizefield']],
                "modified" => utcTimeToLocal($result['_source']['mtime']),
                "type" => 'file'
            ];
        } else {
            $items[] = [
                "name" => $result['_source']['parent_path'] . '/' . $result['_source']['name'],
                "size" => $result['_source'][$_COOKIE['sizefield']],
                "modified" => utcTimeToLocal($result['_source']['mtime']),
                "type" => 'file'
            ];
        }
    }

    return $items;
}


function get_sub_dirs($client, $index, $path, $filter, $use_count, $sortdirs, $maxdirs) {
    // gets the largest sub dirs by filesize or item count (use_count true)
    // non-recursive
    // sorted by size/filename
    // returns directory path and directory info
    $totalsize = 0;
    $totalcount = 0;
    $totalcount_files = 0;
    $totalcount_subdirs = 0;
    $dirs = [];

    $searchParams['body'] = [];

    // Setup search query
    $searchParams['index'] = $index;

    // search size
    $searchParams['size'] = $maxdirs;

    // diff query if root path /
    if ($path === '/') {
        $query = '(parent_path: \/ NOT parent_path: \/*\/* NOT name: "") AND '.$_COOKIE['sizefield'].': >=' . $filter . ' AND type:"directory"';
    } else {
        // escape special characters
        $escapedpath = escape_chars($path);
        $query = '(parent_path: ' . $escapedpath . ' NOT parent_path: ' . $escapedpath . '\/*) AND '.$_COOKIE['sizefield'].': >=' . $filter . ' AND type:"directory"';
    }

    $searchParams['body'] = [
        '_source' => ["parent_path","name","size","size_du","file_count","dir_count","mtime"],
            'query' => [
                'query_string' => [
                'query' => $query,
                'analyze_wildcard' => 'true'
            ]
        ]
    ];

    // sort directories by size or file count
    if ($sortdirs === 1) {
        if ($use_count === 1) {
            $searchParams['body']['sort'] = [
                'file_count' => [
                    'order' => 'desc'
                ],
                'name' => [
                    'order' => 'asc'
                ]
            ];
        } else {
            $searchParams['body']['sort'] = [
                'size' => [
                    'order' => 'desc'
                ],
                'name' => [
                    'order' => 'asc'
                ]
            ];
        }
    } else {
        $searchParams['body']['sort'] = [
            'name' => [
                'order' => 'asc'
            ]
        ];
    }

    // check if we need to apply any filters to search
    $searchParams = filterSearchResults($searchParams);

    try {
        // Send search query to Elasticsearch and get results
        $queryResponse = $client->search($searchParams);
    }
    catch(Exception $e) {
        handleError('ES error: ' . $e->getMessage(), false);
    }

    // Get directories
    $results = $queryResponse['hits']['hits'];

    foreach ($results as $arr) {
        if ($path === '/') {
            $fullpath = $arr['_source']['parent_path'] . $arr['_source']['name'];
        } else {
            $fullpath = $arr['_source']['parent_path'] . '/' . $arr['_source']['name'];  
        }

        // Get total count of files
        $totalcount_files = (int)$arr['_source']['file_count'];

        // Get total count of subdirs
        $totalcount_subdirs = (int)$arr['_source']['dir_count'];

        // Get total count (files+subdirs)
        $totalcount = (int)$totalcount_files + $totalcount_subdirs;

        // Get total size of directory and all subdirs
        $totalsize = (int)$arr['_source'][$_COOKIE['sizefield']];

        // Get directory modified time
        $modified = utcTimeToLocal($arr['_source']['mtime']);

        // Add to dirs array a new array with full path, total size (of all files), total count (file items/subdir items) and dir modified time
        $dirs[] = [$fullpath, $totalsize, $totalcount, $totalcount_files, $totalcount_subdirs, $modified];
    }

    return $dirs;
}

function walk_tree($client, $index, $path, $filter, $time, $depth, $maxdepth, $use_count=0, $show_files=1, $sortdirs=1, $maxdirs=100) {
    $items = [];
    $subdirs = [];
    if ($depth === $maxdepth) {
        return $items;
    }

    // get files in current path (not recursive)
    if ($show_files === 1) {
        $items = get_files($client, $index, $path, $filter, $time);
    }

    // get directories (inc. their total size and file count) in current path (not recursive)
    $subdirs = get_sub_dirs($client, $index, $path, $filter, $use_count, $sortdirs, $maxdirs);

    // return if there are no sub directories
    if (count($subdirs) === 0) {
        return $items;
    }

    // loop through all subdirs and add to subdirs_size, subdirs_count, etc arrays
    $subdirs_size = [];
    $subdirs_count = [];
    $subdirs_count_files = [];
    $subdirs_count_subdirs = [];
    $subdirs_modified = [];

    foreach ($subdirs as $d) {
        // if directory is empty don't show it in the tree
        if ($d[1] === 0 || $d[2] === 0) {
            continue;
        } else {
            $subdirs_size[$d[0]] = $d[1];
            $subdirs_count[$d[0]] = $d[2];
            $subdirs_count_files[$d[0]] = $d[3];
            $subdirs_count_subdirs[$d[0]] = $d[4];
            $subdirs_modified[$d[0]] = $d[5];
        }
    }

    $subdirs = ($use_count === 1) ? $subdirs_count : $subdirs_size;

    // add subdirs to items array
    foreach ($subdirs as $key => $value) {
        $items[] = [
            "name" => $key,
            "size" => $subdirs_size[$key],
            "count" => $subdirs_count[$key],
            "count_files" => $subdirs_count_files[$key],
            "count_subdirs" => $subdirs_count_subdirs[$key],
            "modified" => $subdirs_modified[$key],
            "type" => 'directory',
            "children" => walk_tree($client, $index, $key, $filter, $time, $depth+=1, $maxdepth, $use_count, $show_files, $sortdirs, $maxdirs)
        ];
        $depth-=1;
    }

    if ($sortdirs === 0) {
         // sort subdirs in "natural order"
         usort($items, 'subdirs_name_sort');
    }

    return $items;
}


function subdirs_name_sort($a, $b) {
    // get file name only
    $a['name'] = basename($a['name']);
    $b['name'] = basename($b['name']);
    // remove any . or _ from start of name
    $a['name'] = ltrim($a['name'], '._');
    $b['name'] = ltrim($b['name'], '._');
    return strcasecmp($a['name'], $b['name']);
}


function get_file_mtime_dashboard($client, $index, $path) {
    /* gets file modified ranges for the dashboard, 
    similiar to get_file_mtime but with less date ranges */
    $items = [];
    $searchParams['body'] = [];

    // Setup search query
    $searchParams['index'] = $index;

    $escapedpath = escape_chars($path);

    if ($escapedpath === '\/') {  // root /
            $searchParams['body'] = [
                'size' => 0,
                'query' => [
                    'query_string' => [
                        'query' => 'parent_path: ' . $escapedpath . '* AND type:"file"',
                        'analyze_wildcard' => 'true'
                    ]
                ]
            ];
    } else {
        $searchParams['body'] = [
            'size' => 0,
            'query' => [
                'query_string' => [
                    'query' => '(parent_path: ' . $escapedpath . ' OR
                    parent_path: ' . $escapedpath . '\/*) AND type:"file"',
                    'analyze_wildcard' => 'true'
                ]
            ]
        ];
    }

    $searchParams['body'] += [
        'aggs' => [
            'mtime_ranges' => [
                'range' => [
                    'field' => 'mtime',
                    'keyed' => true,
                    'ranges' => [
                        ['key' => '0 - 30 days', 'from' => 'now/m-1M/d', 'to' => 'now/m'],
                        ['key' => '30 - 90 days', 'from' => 'now/m-3M/d', 'to' => 'now/m-1M/d'],
                        ['key' => '90 - 180 days', 'from' => 'now/m-6M/d', 'to' => 'now/m-3M/d'],
                        ['key' => '180 days - 1 year', 'from' => 'now/m-1y/d', 'to' => 'now/m-6M/d'],
                        ['key' => '1 - 2 years', 'from' => 'now/m-2y/d', 'to' => 'now/m-1y/d'],
                        ['key' => '> 2 years', 'to' => 'now/m-2y/d']
                    ]
                ],
                'aggs' => [
                    'file_size' => [
                        'sum' => [
                            'field' => $_COOKIE['sizefield']
                        ]
                    ]
                ]
            ]
        ]
    ];

    try {
        $queryResponse = $client->search($searchParams);
    }
    catch(Exception $e) {
        handleError('ES error: ' . $e->getMessage(), false);
    }

    // Get mtime ranges
    $results = $queryResponse['aggregations']['mtime_ranges']['buckets'];

    // Add mtimes to items array
    foreach ($results as $key => $result) {
        $items[] = [
                    "mtime" => $key,
                    "count" => $result['doc_count'],
                    "size" => $result['file_size']['value']
                    ];
    }

    return $items;
}

function get_file_mtime_searchresults($client, $index, $path) {
    /* gets file modified ranges for search results chart, 
    similiar to get_file_mtime but with less date ranges */
    $items = [];
    $searchParams['body'] = [];

    // Setup search query
    $searchParams['index'] = $index;

    $escapedpath = escape_chars($path);

    if ($escapedpath === '\/') {  // root /
            $searchParams['body'] = [
                'size' => 0,
                'query' => [
                    'query_string' => [
                        'query' => 'parent_path: ' . $escapedpath . '* AND type:"file"',
                        'analyze_wildcard' => 'true'
                    ]
                ]
            ];
    } else {
        $searchParams['body'] = [
            'size' => 0,
            'query' => [
                'query_string' => [
                    'query' => '(parent_path: ' . $escapedpath . ' OR
                    parent_path: ' . $escapedpath . '\/*) AND type:"file"',
                    'analyze_wildcard' => 'true'
                ]
            ]
        ];
    }

    $searchParams['body'] += [
        'aggs' => [
            'mtime_ranges' => [
                'range' => [
                    'field' => 'mtime',
                    'keyed' => true,
                    'ranges' => [
                        ['key' => '0 - 30 days', 'from' => 'now/m-1M/d', 'to' => 'now/m'],
                        ['key' => '30 - 90 days', 'from' => 'now/m-3M/d', 'to' => 'now/m-1M/d'],
                        ['key' => '90 - 180 days', 'from' => 'now/m-6M/d', 'to' => 'now/m-3M/d'],
                        ['key' => '180 days - 1 year', 'from' => 'now/m-1y/d', 'to' => 'now/m-6M/d'],
                        ['key' => '1 - 2 years', 'from' => 'now/m-2y/d', 'to' => 'now/m-1y/d'],
                        ['key' => '> 2 years', 'to' => 'now/m-2y/d']
                    ]
                ],
                'aggs' => [
                    'file_size' => [
                        'sum' => [
                            'field' => $_COOKIE['sizefield']
                        ]
                    ]
                ]
            ]
        ]
    ];

    // check if we need to apply any filters to search
    $searchParams = filterSearchResults($searchParams);

    try {
        $queryResponse = $client->search($searchParams);
    }
    catch(Exception $e) {
        handleError('ES error: ' . $e->getMessage(), false);
    }

    // Get mtime ranges
    $results = $queryResponse['aggregations']['mtime_ranges']['buckets'];

    // Add mtimes to items array
    foreach ($results as $key => $result) {
        $items[] = [
                    "mtime" => $key,
                    "count" => $result['doc_count'],
                    "size" => $result['file_size']['value']
                    ];
    }

    return $items;
}

function get_file_ext_dashboard($client, $index, $path) {
    // gets the top 10 file extensions for the dashboard
    $items = [];
    $searchParams['body'] = [];

    // Setup search query
    $searchParams['index'] = $index;

    $escapedpath = escape_chars($path);
    if ($escapedpath === '\/') {  // root /
            $searchParams['body'] = [
                'size' => 0,
                'query' => [
                    'query_string' => [
                        'query' => 'parent_path: ' . $escapedpath . '* AND type:"file"',
                        'analyze_wildcard' => 'true'
                    ]
                ]
            ];
    } else {
        $searchParams['body'] = [
            'size' => 0,
            'query' => [
                'query_string' => [
                    'query' => '(parent_path: ' . $escapedpath . ' OR
                    parent_path: ' . $escapedpath . '\/*) AND type:"file"',
                    'analyze_wildcard' => 'true'
                ]
            ]
        ];
    }

    $searchParams['body'] += [
            'aggs' => [
                'top_extensions' => [
                    'terms' => [
                        'field' => 'extension',
                        'order' => [
                            'ext_size' => 'desc'
                        ],
                        'size' => 10
                    ],
                    'aggs' => [
                        'ext_size' => [
                            'sum' => [
                                'field' => $_COOKIE['sizefield']
                            ]
                        ]
                    ]
                ]
            ]
        ];

    try {
        $queryResponse = $client->search($searchParams);
    }
    catch(Exception $e) {
        handleError('ES error: ' . $e->getMessage(), false);
    }

    // Get file extensions
    $results = $queryResponse['aggregations']['top_extensions']['buckets'];

    // Add file extension to items array
    foreach ($results as $result) {
        $items[] = [
                    "name" => $result['key'],
                    "count" => $result['doc_count'],
                    "size" => $result['ext_size']['value']
                    ];
    }

    return $items;
}

function get_file_ext_searchresults($client, $index, $path) {
    // gets the top 10 file extensions for search results chart
    $items = [];
    $searchParams['body'] = [];

    // Setup search query
    $searchParams['index'] = $index;

    $escapedpath = escape_chars($path);
    if ($escapedpath === '\/') {  // root /
            $searchParams['body'] = [
                'size' => 0,
                'query' => [
                    'query_string' => [
                        'query' => 'parent_path: ' . $escapedpath . '* AND type:"file"',
                        'analyze_wildcard' => 'true'
                    ]
                ]
            ];
    } else {
        $searchParams['body'] = [
            'size' => 0,
            'query' => [
                'query_string' => [
                    'query' => '(parent_path: ' . $escapedpath . ' OR
                    parent_path: ' . $escapedpath . '\/*) AND type:"file"',
                    'analyze_wildcard' => 'true'
                ]
            ]
        ];
    }

    $searchParams['body'] += [
            'aggs' => [
                'top_extensions' => [
                    'terms' => [
                        'field' => 'extension',
                        'order' => [
                            'ext_size' => 'desc'
                        ],
                        'size' => 10
                    ],
                    'aggs' => [
                        'ext_size' => [
                            'sum' => [
                                'field' => $_COOKIE['sizefield']
                            ]
                        ]
                    ]
                ]
            ]
        ];

    // check if we need to apply any filters to search
    $searchParams = filterSearchResults($searchParams);

    try {
        $queryResponse = $client->search($searchParams);
    }
    catch(Exception $e) {
        handleError('ES error: ' . $e->getMessage(), false);
    }

    // Get file extensions
    $results = $queryResponse['aggregations']['top_extensions']['buckets'];

    // Add file extension to items array
    foreach ($results as $result) {
        $items[] = [
                    "name" => $result['key'],
                    "count" => $result['doc_count'],
                    "size" => $result['ext_size']['value']
                    ];
    }

    return $items;
}