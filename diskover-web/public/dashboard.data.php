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

require '../vendor/autoload.php';
use Elasticsearch\Common\Exceptions\Missing404Exception;
require "d3_inc.php";

session_write_close();


// escape characters in rootpath
$path_escaped = escape_chars($_SESSION['rootpath']);
// encode rootpath
$path_encoded = rawurlencode($_SESSION['rootpath']);
// hex color codes for fileGroups
$fileGroups_colors = [
    '4A924D', '3465CC', 'DC3912', '129618', 'A84554', '980299', '3B3EAC',
    '4B4846', '1C7B9C', 'A13B5D', '4F7F1A', 'FFD52F'
];
$randcolor = array('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'a', 'b', 'c', 'd', 'e', 'f');


// Get info about index
$searchParams['index'] = $esIndex;
$searchParams['body'] = [
    'size' => 2,
    'query' => [
        'query_string' => [
            'query' => 'path:"' . $_SESSION['rootpath'] . '" AND type:"indexinfo"'
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
            'query' => 'path:"' . $_SESSION['rootpath'] . '" AND type:"spaceinfo"'
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
            'query' => 'mtime:[* TO now/m-6M/d] AND atime:[* TO now/m-6M/d] AND parent_path:' . escape_chars($_SESSION['rootpath']) . '* AND type:"file"'
        ]
    ]
];

try {
    // Send search query to Elasticsearch
    $queryResponse = $client->search($searchParams);
} catch (Missing404Exception $e) {
    handleError("Selected indices are no longer available.");
} catch (Exception $e) {
    handleError('ES error: ' . $e->getMessage(), false);
}

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

$fileGroups_sizes = [];
foreach ($fileGroups_extensions as $key => $value) {
    $fileGroups_sizes[$key] = 0;
}
$fileGroups_totalsize = 0;

$fileGroups_extension = [];
$allextensions = "";
foreach ($fileGroups_sizes as $key => $value) {
    $extensions = "";
    $x = count($fileGroups_extensions[$key]);
    $n = 0;
    foreach ($fileGroups_extensions[$key] as $k => $v) {
        $extensions .= "$v";
        if ($n < $x - 1) $extensions .= " OR ";
        $n++;
    }
    $allextensions .= $extensions;

    $searchParams['index'] = $esIndex;

    $query = 'extension:(' . $extensions . ') AND parent_path:' . escape_chars($_SESSION['rootpath']) . '* AND type:file';

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

    $searchParams = filterChartResults($searchParams);

    try {
        // Send search query to Elasticsearch
        $queryResponse = $client->search($searchParams);
    } catch (Missing404Exception $e) {
        handleError("Selected indices are no longer available.");
    } catch (Exception $e) {
        handleError('ES error: ' . $e->getMessage(), false);
    }

    // Get total size of all files with tag
    $fileGroups_sizes[$key] = $queryResponse['aggregations']['total_size']['value'];
    $fileGroups_totalsize += $fileGroups_sizes[$key];
}

$fileGroups_extension['other'] = 'NOT extension:(' . $allextensions . ') AND parent_path:' . escape_chars($_SESSION['rootpath']) . '* AND type:file';

$fileGroups_percents = [];
$fileGroups_percent_total = 0;
foreach ($fileGroups_sizes as $key => $value) {
    if ($key == 'other') continue;
    $fileGroups_percents[$key] = round($value / $totalfilesizedu * 100);
    $fileGroups_percent_total += round($value / $totalfilesizedu * 100);
}
$fileGroups_percents['other'] = 100 - $fileGroups_percent_total;


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
            'query' => 'parent_path:' . escape_chars($_SESSION['rootpath']) . '* AND type:file'
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

try {
    // Send search query to Elasticsearch
    $queryResponse = $client->search($searchParams);
} catch (Missing404Exception $e) {
    handleError("Selected indices are no longer available.");
} catch (Exception $e) {
    handleError('ES error: ' . $e->getMessage(), false);
}

$avgfilesize = $queryResponse['aggregations']['avg_size']['value'];
$avgfilesizedu = $queryResponse['aggregations']['avg_size_du']['value'];

$searchParams['body'] = [
    'size' => 0,
    'track_total_hits' => true,
    'query' => [
        'query_string' => [
            'query' => 'parent_path:' . escape_chars($_SESSION['rootpath']) . '* AND type:directory'
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

try {
    // Send search query to Elasticsearch
    $queryResponse = $client->search($searchParams);
} catch (Missing404Exception $e) {
    handleError("Selected indices are no longer available.");
} catch (Exception $e) {
    handleError('ES error: ' . $e->getMessage(), false);
}

$avgdirsize = $queryResponse['aggregations']['avg_size']['value'];
$avgdirsizedu = $queryResponse['aggregations']['avg_size_du']['value'];

// Get search results from Elasticsearch for top 10 largest files
$results = [];
$searchParams = [];

// Setup search query
$searchParams['index'] = $esIndex;

// Setup search query for largest files
$searchParams['body'] = [
    'size' => 10,
    '_source' => ['name', 'size', 'size_du', 'atime'],
    'query' => [
        'query_string' => [
            'query' => 'parent_path:' . $path_escaped . '* AND NOT (parent_path:"/" AND name:"") AND type:file',
            'analyze_wildcard' => 'true'
        ]
    ],
    'sort' => [
        'size' => [
            'order' => 'desc'
        ]
    ]
];

try {
    // Send search query to Elasticsearch
    $queryResponse = $client->search($searchParams);
} catch (Missing404Exception $e) {
    handleError("Selected indices are no longer available. Please select a different index.");
} catch (Exception $e) {
    handleError('ES error: ' . $e->getMessage(), false);
}

$largestfiles = $queryResponse['hits']['hits'];

// Get search results from Elasticsearch for top 10 largest directories
$results = [];
$searchParams = [];

// Setup search query
$searchParams['index'] = $esIndex;

// Setup search query for largest directories
$searchParams['body'] = [
    'size' => 10,
    '_source' => ['name', 'size', 'size_du', 'mtime', 'dir_count', 'file_count'],
    'query' => [
        'query_string' => [
            'query' => 'parent_path:' . $path_escaped . '* AND NOT (parent_path:"/" AND name:"") AND type:directory',
            'analyze_wildcard' => 'true'
        ]
    ],
    'sort' => [
        'size' => [
            'order' => 'desc'
        ]
    ]
];

try {
    // Send search query to Elasticsearch
    $queryResponse = $client->search($searchParams);
} catch (Missing404Exception $e) {
    handleError("Selected indices are no longer available. Please select a different index.");
} catch (Exception $e) {
    handleError('ES error: ' . $e->getMessage(), false);
}

$largestdirs = $queryResponse['hits']['hits'];

$estime = number_format(microtime(true) - $_SERVER["REQUEST_TIME_FLOAT"], 4);

?>

<div class="row">
    <div class="col-lg-3 col-md-3 col-sm-4">
        <div class="panel panel-success">
            <div class="panel-heading">
                <h3 class="panel-title"><i class="fas fa-file"></i> Total Files</h3>
            </div>
            <div class="panel-body">
                <h1><?php echo number_format($totalfiles); ?></h1>
            </div>
            <div class="panel-footer text-center">
                Size: <?php echo formatBytes($totalfilesize); ?> (Avg: <?php echo formatBytes($avgfilesize); ?>)
                / Allocated: <?php echo formatBytes($totalfilesizedu); ?> (Avg: <?php echo formatBytes($avgfilesizedu); ?>)
            </div>
        </div>
    </div>
    <div class="col-lg-3 col-md-3 col-sm-4">
        <div class="panel panel-info">
            <div class="panel-heading">
                <h3 class="panel-title"><i class="fas fa-folder"></i> Total Directories</h3>
            </div>
            <div class="panel-body">
                <h1><?php echo number_format($totaldirs); ?></h1>
            </div>
            <div class="panel-footer text-center">
                Avg size: <?php echo formatBytes($avgdirsize); ?>
                / Avg allocated: <?php echo formatBytes($avgdirsizedu); ?>
            </div>
        </div>
    </div>
    <div class="col-lg-3 col-md-3 col-sm-4">
        <div class="panel panel-danger">
            <div class="panel-heading">
                <h3 class="panel-title" style="display:inline-block"><i class="glyphicon glyphicon-th-list"></i> Files on Cleanlist</h3> <i title="files with mtime and atime > 6 months old" class="far fa-question-circle"></i>
            </div>
            <div class="panel-body">
                <h1><?php echo number_format($cleanlist_filecount); ?></h1>
            </div>
            <div class="panel-footer text-center">
                Total disk space gain: <?php echo formatBytes($cleanlist_filesize); ?>
            </div>
        </div>
    </div>
    <div class="col-lg-3 col-md-3 col-sm-4">
        <div class="panel panel-warning">
            <div class="panel-heading">
                <h3 class="panel-title" style="display:inline-block"><i class="glyphicon glyphicon-erase"></i> Percent Removable</h3> <i title="percent of files on cleanlist compared to total files" class="far fa-question-circle"></i>
            </div>
            <div class="panel-body">
                <h1><?php echo $percent_removable; ?> %</h1>
            </div>
            <div class="panel-footer text-center">
                <a href="search.php?&submitted=true&p=1&q=mtime%3A%5B*%20TO%20now%2Fm-6M%2Fd%5D%20AND%20atime%3A%5B*%20TO%20now%2Fm-6M%2Fd%5D%20AND%20parent_path%3A<?php echo rawurlencode($path_escaped) ?>*%20AND%20type%3Afile&path=<?php echo $path_encoded ?>" target="_blank">More info <i class="glyphicon glyphicon-circle-arrow-right"></i></a>
            </div>
        </div>
    </div>
</div>
<div class="row">
    <div class="col-lg-12 col-md-12 col-sm-12">
        <div class="panel panel-default">
            <div class="panel-heading">
                <h3 class="panel-title">Hot/Cold Data</h3>
            </div>
            <div class="panel-body" id="mtime-Chart-container">
                <canvas id="mtime-barChart" height="125"></canvas>
            </div>
            <div class="panel-body" id="atime-Chart-container">
                <canvas id="atime-barChart" height="125"></canvas>
            </div>
        </div>
    </div>
</div>
<div class="row">
    <div class="col-lg-12">
        <div class="panel panel-default">
            <div class="panel-heading">
                <h3 class="panel-title">File Type Usage</h3>
            </div>
            <div class="panel-body">
                <div class="progress" style="height:20px;margin-bottom:5px">
                    <?php $i = 0;
                    foreach ($fileGroups_percents as $key => $value) {
                        if ($key == 'other') {
                            $color = '8B8A88';
                        } else {
                            if (array_key_exists($i, $fileGroups_colors)) {
                                $color = $fileGroups_colors[$i];
                            } else {
                                // pick random hex color
                                $fileGroups_colors[$i] = $randcolor[rand(0, 15)] . $randcolor[rand(0, 15)] . $randcolor[rand(0, 15)] . $randcolor[rand(0, 15)] . $randcolor[rand(0, 15)] . $randcolor[rand(0, 15)];
                                $color = $fileGroups_colors[$i];
                            }
                        }
                    ?>
                        <a href="search.php?&submitted=true&p=1&q=<?php echo rawurlencode($fileGroups_extension[$key]); ?>&doctype=file&path=<?php echo $path_encoded ?>" target="_blank">
                        <div title="<?php echo $key . ": " . formatBytes($fileGroups_sizes[$key]) . ' (' . $value . ' %)'; ?>" class="progress-bar" style="background-color: #<?php echo $color; ?>; width: <?php echo $value; ?>%"></div>
                        </a>
                    <?php $i++;
                    } ?>
                </div>
                <span class="filetypechart">
                <?php $i = 0;
                    foreach ($fileGroups_percents as $key => $value) {
                        if ($key == 'other') {
                            $color = '8B8A88';
                        } else {
                            $color = $fileGroups_colors[$i];
                        }
                    ?>
                        <a href="search.php?&submitted=true&p=1&q=<?php echo rawurlencode($fileGroups_extension[$key]); ?>&doctype=file&path=<?php echo $path_encoded ?>" target="_blank"><i class="fas fa-square" style="color: #<?php echo $color; ?>" title="<?php echo $value; ?>%"></i> <?php echo $key . ": " . formatBytes($fileGroups_sizes[$key]) . ' (' . $value . ' %)'; ?></a>&nbsp;
                    <?php $i++;
                    } ?>
                </span>
            </div>
        </div>
    </div>
</div>
<div class="row">
    <div class="col-lg-6 col-md-6 col-sm-12">
        <div class="panel panel-default">
            <div class="panel-heading">
                <h3 class="panel-title">Available Space</h3>
            </div>
            <div class="panel-body">
                <span><i class="fas fa-hdd" style="margin-right: 2px; color: grey"></i> <?php echo $_SESSION['rootpath']; ?></span>
                <span class="pull-right"><b><?php echo formatBytes($space_available); ?> available</b> of <?php echo formatBytes($space_total); ?> (<?php echo round($space_available / $space_total * 100); ?> %)
                    <?php if ($esIndex2 != "") { ?>
                        <?php echo ($space_change > 0) ? "<span style=\"color:#29FE2F\"><i class=\"fa fa-caret-up\"></i>" : "<span style=\"color:red\"><i class=\"fa fa-caret-down\"></i>";
                        echo " " . $space_change . " %"; ?></span>
            <?php } ?>
            </span>
            <div class="progress" style="height:20px;margin-bottom:5px;">
                <?php
                $available_percent = round($space_available / $space_total * 100);
                $used_percent = 100 - $available_percent;
                ?>
                <div title="Used: <?php echo formatBytes($space_used) . ' (' . $used_percent . ' %)'; ?>" class="progress-bar" style="background-color: #3465CC; width: <?php echo $used_percent; ?>%"></div>
                <div title="Available: <?php echo formatBytes($space_available) . ' (' . $available_percent . ' %)'; ?>" class="progress-bar" style="background-color: #ccc; width: <?php echo $available_percent; ?>%"></div>
            </div>
            <span><i class="fas fa-square" style="color: #3465CC" title="<?php echo $used_percent; ?>%"></i> Used: <?php echo formatBytes($space_used) . ' (' . $used_percent . ' %)'; ?>&nbsp;
                <i class="fas fa-square" style="color: #ccc" title="<?php echo $available_percent; ?>%"></i> Available: <?php echo formatBytes($space_available) . ' (' . $available_percent . ' %)'; ?>&nbsp;
            </span>
            </div>
            <div class="panel-footer">
                <?php echo formatBytes($space_total); ?> Total Capacity
            </div>
        </div>
    </div>
    <div class="col-lg-6 col-md-6 col-sm-12">
        <div class="panel panel-default">
            <div class="panel-heading">
                <h3 class="panel-title">Top File Types</h3>
            </div>
            <div class="panel-body" id="topFileTypes-Chart-container">
                <div style="margin:0 auto; width:100%">
                    <div style="width:40%; display:inline-block">
                        <canvas id="topFileTypesBySize-barChart" height="180"></canvas>
                    </div>
                    <div style="margin-left:5%; margin-bottom:0px; width:50%; display:inline-block">
                        <canvas id="topFileTypesByCount-pieChart" height="160"></canvas>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
<div class="row">
    <div class="col-lg-6 col-md-6 col-sm-12">
        <div class="panel panel-default">
            <div class="panel-heading">
                <h3 class="panel-title"><i class="glyphicon glyphicon-scale"></i> Largest Files</h3>
            </div>
            <div class="panel-body">
                <table class="table table-striped table-hover">
                    <thead>
                        <tr>
                            <th>Name</th>
                            <th>Size</th>
                            <th>Allocated</th>
                            <th>Last Accessed</th>
                        </tr>
                    </thead>
                    <tbody>
                        <?php
                        foreach ($largestfiles as $key => $value) {
                        ?>
                            <tr>
                                <td class="path"><a href="view.php?id=<?php echo $value['_id'] . '&amp;docindex=' . $value['_index'] . '&amp;doctype=file'; ?>" target="_blank"><i class="fas fa-file-alt" style="color:#738291;padding-right:3px;"></i> <?php echo $value['_source']['name']; ?></a></td>
                                <th><?php echo formatBytes($value['_source']['size']); ?></td>
                                <th><?php echo formatBytes($value['_source']['size_du']); ?></td>
                                <th><?php echo utcTimeToLocal($value['_source']['atime']); ?></td>
                            </tr>
                        <?php } ?>
                    </tbody>
                </table>
            </div>
            <div class="panel-footer text-center">
                <a href="search.php?&submitted=true&p=1&q=parent_path:<?php echo rawurlencode($path_escaped) ?>*&sort=size&sortorder=desc&sort2=name&sortorder2=asc&doctype=file&path=<?php echo $path_encoded ?>" target="_blank">Show more <i class="glyphicon glyphicon-circle-arrow-right"></i></a>
            </div>
        </div>
    </div>
    <div class="col-lg-6 col-md-6 col-sm-12">
        <div class="panel panel-default">
            <div class="panel-heading">
                <h3 class="panel-title"><i class="glyphicon glyphicon-scale"></i> Largest Directories</h3>
            </div>
            <div class="panel-body">
                <table class="table table-striped table-hover">
                    <thead>
                        <tr>
                            <th>Name</th>
                            <th>Date Modified</th>
                            <th>Size</th>
                            <th>Allocated</th>
                            <th>Items</th>
                        </tr>
                    </thead>
                    <tbody>
                        <?php
                        foreach ($largestdirs as $key => $value) {
                        ?>
                            <tr>
                                <td class="path"><a href="view.php?id=<?php echo $value['_id'] . '&amp;docindex=' . $value['_index'] . '&amp;doctype=directory'; ?>" target="_blank"><i class="fas fa-folder" style="color:#E9AC47;padding-right:3px"></i> <?php if ($value['_source']['name'] === '' && $value['_source']['parent_path'] === '/') {
                                                                                                                                                                                                                                                                echo '/';
                                                                                                                                                                                                                                                            } else {
                                                                                                                                                                                                                                                                echo $value['_source']['name'];
                                                                                                                                                                                                                                                            } ?></a></td>
                                <th><?php echo utcTimeToLocal($value['_source']['mtime']); ?></td>
                                <th><?php echo formatBytes($value['_source']['size']); ?></td>
                                <th><?php echo formatBytes($value['_source']['size_du']); ?></td>
                                <th><?php echo number_format($value['_source']['file_count'] + $value['_source']['dir_count']); ?></td>
                            </tr>
                        <?php } ?>
                    </tbody>
                </table>
            </div>
            <div class="panel-footer text-center">
                <a href="search.php?&submitted=true&p=1&q=parent_path:<?php echo rawurlencode($path_escaped) ?>*&sort=size&sortorder=desc&sort2=name&sortorder2=asc&doctype=directory&path=<?php echo $path_encoded ?>" target="_blank">Show more <i class="glyphicon glyphicon-circle-arrow-right"></i></a>
            </div>
        </div>
    </div>
</div>
<form><input type="hidden" id="estime" name="estime" value="<?php echo $estime ?>" /></form>