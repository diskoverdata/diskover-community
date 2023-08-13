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
require "../src/diskover/Auth.php";
require "d3_inc.php";
require "dashboard.data.php";

$estime = number_format(microtime(true) - $_SERVER["REQUEST_TIME_FLOAT"], 4);

// escape characters in rootpath
$path_escaped = escape_chars($_SESSION['rootpath']);
// encode rootpath
$path_encoded = rawurlencode($_SESSION['rootpath']);

?>
<!DOCTYPE html>
<html lang="en">

<head>
    <?php if (isset($_COOKIE['sendanondata']) && $_COOKIE['sendanondata'] == 1) { ?>
    <!-- Global site tag (gtag.js) - Google Analytics -->
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-DYSE689C04"></script>
    <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){dataLayer.push(arguments);}
    gtag('js', new Date());

    gtag('config', 'G-DYSE689C04');
    </script>
    <?php } ?>
    <meta charset="utf-8" />
    <link rel="icon" type="image/png" href="images/diskoverfavico.png" />
    <meta http-equiv="X-UA-Compatible" content="IE=edge" />
    <title>diskover &mdash; Dashboard</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="stylesheet" href="css/fontawesome-free/css/all.min.css" media="screen" />
    <link rel="stylesheet" href="css/bootswatch.min.css" media="screen" />
    <link rel="stylesheet" href="css/Chart.min.css" media="screen" />
    <link rel="stylesheet" href="css/diskover.css" media="screen" />
</head>

<body>
    <?php include "nav.php"; ?>

    <div class="container-fluid" id="mainwindow" style="margin-top:70px">
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
                        <canvas id="mtime-barChart" height="90"></canvas>
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
                            <div title="Docs: <?php echo formatBytes($fileGroups_sizes['docs']) . ' (' . $docs_percent . ' %)'; ?>" class="progress-bar" style="background-color: #4A924D; width: <?php echo $docs_percent; ?>%"></div>
                            <div title="Images: <?php echo formatBytes($fileGroups_sizes['images']) . ' (' . $images_percent . ' %)'; ?>" class="progress-bar" style="background-color: #3465CC; width: <?php echo $images_percent; ?>%"></div>
                            <div title="Video: <?php echo formatBytes($fileGroups_sizes['video']) . ' (' . $video_percent . ' %)'; ?>" class="progress-bar" style="background-color: #DC3912; width: <?php echo $video_percent; ?>%"></div>
                            <div title="Audio: <?php echo formatBytes($fileGroups_sizes['audio']) . ' (' . $audio_percent . ' %)'; ?>" class="progress-bar" style="background-color: #129618; width: <?php echo $audio_percent; ?>%"></div>
                            <div title="Apps: <?php echo formatBytes($fileGroups_sizes['apps']) . ' (' . $apps_percent . ' %)'; ?>" class="progress-bar" style="background-color: #A84554; width: <?php echo $apps_percent; ?>%"></div>
                            <div title="Programming: <?php echo formatBytes($fileGroups_sizes['programming']) . ' (' . $programming_percent . ' %)'; ?>" class="progress-bar" style="background-color: #980299; width: <?php echo $programming_percent; ?>%"></div>
                            <div title="Internet: <?php echo formatBytes($fileGroups_sizes['internet']) . ' (' . $internet_percent . ' %)'; ?>" class="progress-bar" style="background-color: #3B3EAC; width: <?php echo $internet_percent; ?>%"></div>
                            <div title="System: <?php echo formatBytes($fileGroups_sizes['system']) . ' (' . $system_percent . ' %)'; ?>" class="progress-bar" style="background-color: #4B4846; width: <?php echo $system_percent; ?>%"></div>
                            <div title="Data: <?php echo formatBytes($fileGroups_sizes['data']) . ' (' . $data_percent . ' %)'; ?>" class="progress-bar" style="background-color: #1C7B9C; width: <?php echo $data_percent; ?>%"></div>
                            <div title="Disc: <?php echo formatBytes($fileGroups_sizes['disc']) . ' (' . $disc_percent . ' %)'; ?>" class="progress-bar" style="background-color: #A13B5D; width: <?php echo $disc_percent; ?>%"></div>
                            <div title="Compressed: <?php echo formatBytes($fileGroups_sizes['compressed']) . ' (' . $compressed_percent . ' %)'; ?>" class="progress-bar" style="background-color: #4F7F1A; width: <?php echo $compressed_percent; ?>%"></div>
                            <div title="Trash: <?php echo formatBytes($fileGroups_sizes['trash']) . ' (' . $trash_percent . ' %)'; ?>" class="progress-bar" style="background-color: #FFD52F; width: <?php echo $trash_percent; ?>%"></div>
                            <div title="Other: <?php echo formatBytes($other_size) . ' (' . $other_percent . ' %)'; ?>" class="progress-bar" style="background-color: #8B8A88; width: <?php echo $other_percent; ?>%"></div>
                        </div>
                        <span class="filetypechart">
                            <a href="search.php?&submitted=true&p=1&q=<?php echo rawurlencode($fileGroups_extension['docs']); ?>&doctype=file&path=<?php echo $path_encoded ?>" target="_blank"><i class="fas fa-square" style="color: #4A924D" title="<?php echo $docs_percent; ?>%"></i> Docs: <?php echo formatBytes($fileGroups_sizes['docs']) . ' (' . $docs_percent . ' %)'; ?></a>&nbsp;
                            <a href="search.php?&submitted=true&p=1&q=<?php echo rawurlencode($fileGroups_extension['images']); ?>&doctype=file&path=<?php echo $path_encoded ?>" target="_blank"><i class="fas fa-square" style="color: #3465CC" title="<?php echo $images_percent; ?>%"></i> Images: <?php echo formatBytes($fileGroups_sizes['images']) . ' (' . $images_percent . ' %)'; ?></a>&nbsp;
                            <a href="search.php?&submitted=true&p=1&q=<?php echo rawurlencode($fileGroups_extension['video']); ?>&doctype=file&path=<?php echo $path_encoded ?>" target="_blank"><i class="fas fa-square" style="color: #DC3912" title="<?php echo $video_percent; ?>%"></i> Video: <?php echo formatBytes($fileGroups_sizes['video']) . ' (' . $video_percent . ' %)'; ?></a>&nbsp;
                            <a href="search.php?&submitted=true&p=1&q=<?php echo rawurlencode($fileGroups_extension['audio']); ?>&doctype=file&path=<?php echo $path_encoded ?>" target="_blank"><i class="fas fa-square" style="color: #129618" title="<?php echo $audio_percent; ?>%"></i> Audio: <?php echo formatBytes($fileGroups_sizes['audio']) . ' (' . $audio_percent . ' %)'; ?></a>&nbsp;
                            <a href="search.php?&submitted=true&p=1&q=<?php echo rawurlencode($fileGroups_extension['apps']); ?>&doctype=file&path=<?php echo $path_encoded ?>" target="_blank"><i class="fas fa-square" style="color: #A84554" title="<?php echo $apps_percent; ?>%"></i> Apps: <?php echo formatBytes($fileGroups_sizes['apps']) . ' (' . $apps_percent . ' %)'; ?></a>&nbsp;
                            <a href="search.php?&submitted=true&p=1&q=<?php echo rawurlencode($fileGroups_extension['programming']); ?>&doctype=file&path=<?php echo $path_encoded ?>" target="_blank"><i class="fas fa-square" style="color: #980299" title="<?php echo $programming_percent; ?>%"></i> Programming: <?php echo formatBytes($fileGroups_sizes['programming']) . ' (' . $programming_percent . ' %)'; ?></a>&nbsp;
                            <a href="search.php?&submitted=true&p=1&q=<?php echo rawurlencode($fileGroups_extension['internet']); ?>&doctype=file&path=<?php echo $path_encoded ?>" target="_blank"><i class="fas fa-square" style="color: #3B3EAC" title="<?php echo $internet_percent; ?>%"></i> Internet: <?php echo formatBytes($fileGroups_sizes['internet']) . ' (' . $internet_percent . ' %)'; ?></a>&nbsp;
                            <a href="search.php?&submitted=true&p=1&q=<?php echo rawurlencode($fileGroups_extension['system']); ?>&doctype=file&path=<?php echo $path_encoded ?>" target="_blank"><i class="fas fa-square" style="color: #4B4846" title="<?php echo $system_percent; ?>%"></i> System: <?php echo formatBytes($fileGroups_sizes['system']) . ' (' . $system_percent . ' %)'; ?></a>&nbsp;
                            <a href="search.php?&submitted=true&p=1&q=<?php echo rawurlencode($fileGroups_extension['data']); ?>&doctype=file&path=<?php echo $path_encoded ?>" target="_blank"><i class="fas fa-square" style="color: #1C7B9C" title="<?php echo $data_percent; ?>%"></i> Data: <?php echo formatBytes($fileGroups_sizes['data']) . ' (' . $data_percent . ' %)'; ?></a>&nbsp;
                            <a href="search.php?&submitted=true&p=1&q=<?php echo rawurlencode($fileGroups_extension['disc']); ?>&doctype=file&path=<?php echo $path_encoded ?>" target="_blank"><i class="fas fa-square" style="color: #A13B5D" title="<?php echo $disc_percent; ?>%"></i> Disc: <?php echo formatBytes($fileGroups_sizes['disc']) . ' (' . $disc_percent . ' %)'; ?></a>&nbsp;
                            <a href="search.php?&submitted=true&p=1&q=<?php echo rawurlencode($fileGroups_extension['compressed']); ?>&doctype=file&path=<?php echo $path_encoded ?>" target="_blank"><i class="fas fa-square" style="color: #4F7F1A" title="<?php echo $compressed_percent; ?>%"></i> Compressed: <?php echo formatBytes($fileGroups_sizes['compressed']) . ' (' . $compressed_percent . ' %)'; ?></a>&nbsp;
                            <a href="search.php?&submitted=true&p=1&q=<?php echo rawurlencode($fileGroups_extension['trash']); ?>&doctype=file&path=<?php echo $path_encoded ?>" target="_blank"><i class="fas fa-square" style="color: #FFD52F" title="<?php echo $trash_percent; ?>%"></i> Trash: <?php echo formatBytes($fileGroups_sizes['trash']) . ' (' . $trash_percent . ' %)'; ?></a>&nbsp;
                            <a href="search.php?&submitted=true&p=1&q=<?php echo rawurlencode($fileGroups_extension['other']); ?>&doctype=file&path=<?php echo $path_encoded ?>" target="_blank"><i class="fas fa-square" style="color: #8B8A88" title="<?php echo $other_percent; ?>%"></i> Other: <?php echo formatBytes($other_size) . ' (' . $other_percent . ' %)'; ?></a>&nbsp;
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
        <a href="#" class="btn btn-sm btn-default reload-results" title="Reload chart data"><i class="glyphicon glyphicon-refresh"></i> Reload</a>
    </div>
    <hr>
    <div class="container-fluid">
        <div class="row">
            <div class="col-lg-6">
                <div>
                    <i class="fas fa-star" style="color:yellow"></i> <strong><a href="https://github.com/diskoverdata/diskover-community/stargazers" target="_blank">Star</a></strong> us on GitHub.
                </div>
            </div>
            <div class="col-lg-6">
                <div class="pull-right">
                    <b>diskover-web</b> v<?php echo $VERSION; ?>
                </div>
            </div>
        </div>
        <div class="row">
            <div class="col-lg-12">
                <div class="pull-right small text-primary">
                    <?php
                    $time = number_format(microtime(true) - $_SERVER["REQUEST_TIME_FLOAT"], 4);
                    echo "ES Time: {$estime}, Page Load Time: {$time}";
                    ?>
                </div>
            </div>
        </div>
    </div>
    <br>

    <?php include 'modals.php' ?>

    <script language="javascript" src="js/jquery.min.js"></script>
    <script language="javascript" src="js/bootstrap.min.js"></script>
    <script language="javascript" src="js/diskover.js"></script>
    <script language="javascript" src="js/d3.v3.min.js"></script>
    <script language="javascript" src="js/spin.min.js"></script>
    <script language="javascript" src="js/Chart.bundle.min.js"></script>
    <script language="javascript" src="js/diskover-dashboard.js"></script>

</body>

</html>