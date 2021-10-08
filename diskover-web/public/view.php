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
use Elasticsearch\Common\Exceptions\Missing404Exception;
require "../src/diskover/Auth.php";
require "../src/diskover/Diskover.php";


$message = $_REQUEST['message'];

// Check if file ID was provided
if (empty($_REQUEST['id'])) {
    handleError('ES doc id not found');
} else {
    // Try to get file info from from index
    try {
        $searchParams = [];
        $searchParams['index'] = $_REQUEST['docindex'];
        $searchParams['body'] = [
            'query' => [
                'ids' => [
                    'type' => '_doc',
                    'values' => [ $_REQUEST['id'] ]
                ]
            ]
        ];
        $queryResponse = $client->search($searchParams);

        $docid = $queryResponse['hits']['hits'][0]['_id'];
        $docindex = $queryResponse['hits']['hits'][0]['_index'];
        $docsource = $queryResponse['hits']['hits'][0]['_source'];
        $doctype = $docsource['type'];
    } catch (Missing404Exception $e) {
        handleError('ES error: ' . $e->getMessage());
    } catch (Exception $e) {
        handleError('ES error: ' . $e->getMessage());
    }

    // set fullpath, parentpath and filename and check for root /
    $parentpath = $docsource['parent_path'];
    $parentpath_wildcard = escape_chars($parentpath) . '\/*';
    if ($parentpath === "/") {
        if ($docsource['name'] === "") { // root /
            $filename = '/';
            $fullpath = '/';
            $fullpath_wildcard = '\/*';
        } else {
            $filename = $docsource['name'];
            $fullpath = '/' . $filename;
            $fullpath_wildcard = escape_chars($fullpath) . '\/*';
            $parentpath_wildcard = '\/*';
        }
    } else {
        $fullpath = $parentpath . '/' . $docsource['name'];
        $filename = $docsource['name'];
        $fullpath_wildcard = escape_chars($fullpath) . '\/*';
    }
}

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
    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge" />
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>diskover &mdash; File View</title>
    <link rel="stylesheet" href="css/fontawesome-free/css/all.min.css" media="screen" />
    <link rel="stylesheet" href="css/bootswatch.min.css" media="screen" />
    <link rel="stylesheet" href="css/diskover.css" media="screen" />
    <link rel="icon" type="image/png" href="images/diskoverfavico.png" />
</head>

<body>
    <?php include "nav.php"; ?>
    <div class="container" style="margin-top:70px">
        <div class="well well-lg">
            <div class="row">
                <div class="col-xs-12">
                    <?php
                    if ($doctype == 'directory') {
                        $fullpathhref = "search.php?index=" . $esIndex . "&index2=" . $esIndex2 . "&submitted=true&p=1&q=parent_path:" . rawurlencode(escape_chars($fullpath)) . "&path=" . rawurlencode($fullpath);
                    } else {
                        $fullpathhref = "search.php?index=" . $esIndex . "&index2=" . $esIndex2 . "&submitted=true&p=1&q=parent_path:" . rawurlencode(escape_chars($parentpath)) . " AND name:" . rawurlencode($filename) . "&path=" . rawurlencode($parentpath);
                    }
                    ?>
                    <h2 class="path"><?php echo ($doctype == 'file') ? '<i class="fas fa-file-alt" style="color:#738291;"></i>' : '<i class="fas fa-folder" style="color:#E9AC47;"></i>'; ?> <span id="filename"><a href="<?php echo $fullpathhref; ?>"><?php echo $filename; ?></a></span></h2>
                    <div style="padding-bottom:10px"><a href="#" class="btn btn-default btn-xs file-btns" onclick="copyToClipboard('#filename')"><i class="glyphicon glyphicon-copy"></i> Copy file name</a></div>
                    <h4 class="path">Full path: <span id="fullpath"><a href="<?php echo $fullpathhref; ?>"><?php echo $fullpath; ?></a></span></h4> <a href="#" class="btn btn-default btn-xs file-btns" onclick="copyToClipboard('#fullpath')"><i class="glyphicon glyphicon-copy"></i> Copy path</a>
                    <?php if ($_REQUEST['doctype'] == 'directory') { ?>
                        <div class="dropdown" style="display:inline-block;">
                            <button title="analytics" class="btn btn-default dropdown-toggle btn-xs file-btns" type="button" data-toggle="dropdown"><i class="glyphicon glyphicon-stats"></i>
                                <span class="caret"></span></button>
                            <ul class="dropdown-menu">
                                <li class="small"><a href="#"><i class="glyphicon glyphicon-tree-conifer"></i> load path in file tree <span class="label label-info">Essential</span></a></li>
                                <li class="small"><a href="#"><i class="glyphicon glyphicon-th-large"></i> load path in treemap <span class="label label-info">Essential</span></a></li>
                                <li class="small"><a href="#"><i class="glyphicon glyphicon-fire"></i> load path in heatmap <span class="label label-info">Pro</span></a></li>
                            </ul>
                        </div>
                        <div class="dropdown" style="display:inline-block;">
                            <button title="search" class="btn btn-default dropdown-toggle btn-xs file-btns" type="button" data-toggle="dropdown"><i class="glyphicon glyphicon-search"></i>
                                <span class="caret"></span></button>
                            <ul class="dropdown-menu">
                                <li class="small"><a href="search.php?index=<?php echo $esIndex; ?>&amp;index2=<?php echo $esIndex2; ?>&amp;submitted=true&amp;p=1&amp;q=parent_path:<?php echo rawurlencode(escape_chars($fullpath)); ?>"><i class="glyphicon glyphicon-search"></i> search path (non-recursive)</a></li>
                                <li class="small"><a href="search.php?index=<?php echo $esIndex; ?>&amp;index2=<?php echo $esIndex2; ?>&amp;submitted=true&amp;p=1&amp;q=parent_path:(<?php echo rawurlencode(escape_chars($fullpath)) . ' OR ' . rawurlencode($fullpath_wildcard); ?>)"><i class="glyphicon glyphicon-search"></i> search path (recursive)</a></li>
                            </ul>
                        </div>
                        <br />
                    <?php } ?>
                    <h5 class="path"><i class="fas fa-folder" style="color:#E9AC47;"></i> <span style="color:gray">Parent path: <span id="parentpath"><a href="search.php?submitted=true&p=1&q=parent_path:<?php echo rawurlencode(escape_chars($parentpath)); ?>&path=<?php echo rawurlencode($parentpath); ?>"><?php echo $parentpath; ?></a></span> </span></h5> <a href="#" class="btn btn-default btn-xs file-btns" onclick="copyToClipboard('#parentpath')"><i class="glyphicon glyphicon-copy"></i> Copy path</a>
                    <div class="dropdown" style="display:inline-block;">
                        <button title="analytics" class="btn btn-default dropdown-toggle btn-xs file-btns" type="button" data-toggle="dropdown"><i class="glyphicon glyphicon-stats"></i>
                            <span class="caret"></span></button>
                        <ul class="dropdown-menu">
                            <li class="small"><a href="#"><i class="glyphicon glyphicon-tree-conifer"></i> load path in file tree <span class="label label-info">Essential</span></a></li>
                            <li class="small"><a href="#"><i class="glyphicon glyphicon-th-large"></i> load path in treemap <span class="label label-info">Essential</span></a></li>
                            <li class="small"><a href="#"><i class="glyphicon glyphicon-fire"></i> load path in heatmap <span class="label label-info">Pro</span></a></li>
                        </ul>
                    </div>
                    <div class="dropdown" style="display:inline-block;">
                        <button title="filter" class="btn btn-default dropdown-toggle btn-xs file-btns" type="button" data-toggle="dropdown"><i class="glyphicon glyphicon-search"></i>
                            <span class="caret"></span></button>
                        <ul class="dropdown-menu">
                            <li class="small"><a href="search.php?index=<?php echo $esIndex; ?>&amp;index2=<?php echo $esIndex2; ?>&amp;submitted=true&amp;p=1&amp;q=parent_path:<?php echo rawurlencode(escape_chars($parentpath)); ?>"><i class="glyphicon glyphicon-search"></i> search path (non-recursive)</a></li>
                            <li class="small"><a href="search.php?index=<?php echo $esIndex; ?>&amp;index2=<?php echo $esIndex2; ?>&amp;submitted=true&amp;p=1&amp;q=parent_path:(<?php echo rawurlencode(escape_chars($parentpath)) . ' OR ' . rawurlencode($parentpath_wildcard); ?>)"><i class="glyphicon glyphicon-search"></i> search path (recursive)</a></li>
                        </ul>
                    </div>
                    <br /><br />
                </div>
            </div>
            <div class="row">
                <div class="col-xs-6">
                    <ul class="list-group">
                        <li class="list-group-item">
                            <span class="pull-right">&nbsp;
                                <!-- show comparison file size -->
                                <?php if ($esIndex2 != "") { ?>
                                    <?php $fileinfo_index2 = get_index2_fileinfo($client, $esIndex2, $docsource['parent_path'], $docsource['name']);
                                    if ($docsource['size'] > 0 && $fileinfo_index2[0] > 0) {
                                        $filesize_change = number_format(changePercent($docsource['size'], $fileinfo_index2[0]), 1);
                                    } else if ($docsource['size'] > 0 && $fileinfo_index2[0] == 0) {
                                        $filesize_change = 100.0;
                                    }
                                    if ($filesize_change != 0) { ?>
                                        <small><?php echo formatBytes($fileinfo_index2[0]); ?>
                                            <span style="color:<?php echo $filesize_change > 0 ? "red" : "#29FE2F"; ?>;">(<?php echo $filesize_change > 0 ? '<i class="fa fa-caret-up"></i> +' : '<i class="fa fa-caret-down"></i>'; ?>
                                                <?php echo $filesize_change; ?>%)</span></small>
                                <?php }
                                } ?>
                                <!-- end show comparison file size -->
                            </span>
                            <span class="badge"><?php echo formatBytes($docsource['size']); ?></span>
                            Size
                        </li>
                        <li class="list-group-item">
                            <span class="pull-right">&nbsp;
                                <!-- show comparison file size -->
                                <?php if ($esIndex2 != "") { ?>
                                    <?php
                                    if ($docsource['size_du'] > 0 && $fileinfo_index2[1] > 0) {
                                        $filesizedu_change = number_format(changePercent($docsource['size_du'], $fileinfo_index2[1]), 1);
                                    } else if ($docsource['size_du'] > 0 && $fileinfo_index2[0] == 0) {
                                        $filesizedu_change = 100.0;
                                    }
                                    if ($filesizedu_change != 0) { ?>
                                        <small><?php echo formatBytes($fileinfo_index2[1]); ?>
                                            <span style="color:<?php echo $filesizedu_change > 0 ? "red" : "#29FE2F"; ?>;">(<?php echo $filesizedu_change > 0 ? '<i class="fa fa-caret-up"></i> +' : '<i class="fa fa-caret-down"></i>'; ?>
                                                <?php echo $filesizedu_change; ?>%)</span></small>
                                <?php }
                                } ?>
                                <!-- end show comparison file size -->
                            </span>
                            <span class="badge"><?php echo formatBytes($docsource['size_du']); ?></span>
                            Allocated
                        </li>
                        <?php if ($_REQUEST['doctype'] == 'directory') {
                            $items = $docsource['file_count'] + $docsource['dir_count'];
                        ?>
                            <li class="list-group-item">
                                <span class="pull-right">&nbsp;
                                    <!-- show comparison items -->
                                    <?php if ($esIndex2 != "") { ?>
                                        <?php
                                        if ($items > 0 && $fileinfo_index2[2] > 0) {
                                            $diritems_change = number_format(changePercent($items, $fileinfo_index2[2]), 1);
                                        } else if ($items > 0 && $fileinfo_index2[2] == 0) {
                                            $diritems_change = 100.0;
                                        }
                                        if ($diritems_change != 0) { ?>
                                            <small><?php echo number_format($fileinfo_index2[2]); ?>
                                                <span style="color:<?php echo $diritems_change > 0 ? "red" : "#29FE2F"; ?>;">(<?php echo $diritems_change > 0 ? '<i class="fa fa-caret-up"></i> +' : '<i class="fa fa-caret-down"></i>'; ?>
                                                    <?php echo $diritems_change; ?>%)</span></small>
                                    <?php }
                                    } ?>
                                    <!-- end show comparison items -->
                                </span>
                                <span class="badge"><?php echo number_format($items); ?></span>
                                Items
                            </li>
                            <li class="list-group-item">
                                <span class="pull-right">&nbsp;
                                    <!-- show comparison items -->
                                    <?php if ($esIndex2 != "") { ?>
                                        <?php
                                        if ($docsource['file_count'] > 0 && $fileinfo_index2[3] > 0) {
                                            $diritems_files_change = number_format(changePercent($docsource['file_count'], $fileinfo_index2[3]), 1);
                                        } else if ($docsource['file_count'] > 0 && $fileinfo_index2[3] == 0) {
                                            $diritems_files_change = 100.0;
                                        }
                                        if ($diritems_files_change != 0) { ?>
                                            <small><?php echo number_format($fileinfo_index2[3]); ?>
                                                <span style="color:<?php echo $diritems_files_change > 0 ? "red" : "#29FE2F"; ?>;">(<?php echo $diritems_files_change > 0 ? '<i class="fa fa-caret-up"></i> +' : '<i class="fa fa-caret-down"></i>'; ?>
                                                    <?php echo $diritems_files_change; ?>%)</span></small>
                                    <?php }
                                    } ?>
                                    <!-- end show comparison items -->
                                </span>
                                <span class="badge"><?php echo number_format($docsource['file_count']); ?></span>
                                Files
                            </li>
                            <li class="list-group-item">
                                <span class="pull-right">&nbsp;
                                    <!-- show comparison items -->
                                    <?php if ($esIndex2 != "") { ?>
                                        <?php
                                        if ($docsource['dir_count'] > 0 && $fileinfo_index2[4] > 0) {
                                            $diritems_subdirs_change = number_format(changePercent($docsource['dir_count'], $fileinfo_index2[4]), 1);
                                        } else if ($docsource['dir_count'] > 0 && $fileinfo_index2[4] == 0) {
                                            $diritems_subdirs_change = 100.0;
                                        }
                                        if ($diritems_subdirs_change != 0) { ?>
                                            <small><?php echo number_format($fileinfo_index2[4]); ?>
                                                <span style="color:<?php echo $diritems_subdirs_change > 0 ? "red" : "#29FE2F"; ?>;">(<?php echo $diritems_subdirs_change > 0 ? '<i class="fa fa-caret-up"></i> +' : '<i class="fa fa-caret-down"></i>'; ?>
                                                    <?php echo $diritems_subdirs_change; ?>%)</span></small>
                                    <?php }
                                    } ?>
                                    <!-- end show comparison items -->
                                </span>
                                <span class="badge"><?php echo number_format($docsource['dir_count']); ?></span>
                                Folders
                            </li>
                        <?php } ?>
                        <?php if ($_REQUEST['doctype'] == 'file') { ?>
                            <li class="list-group-item">
                                <span class="badge"><?php echo $docsource['extension']; ?></span>
                                <a href="search.php?submitted=true&amp;p=1&amp;q=extension:<?php echo $docsource['extension']; ?>&amp;doctype=<?php echo $_REQUEST['doctype']; ?>">Extension</a>
                            </li>
                        <?php } ?>
                        <li class="list-group-item">
                            <span class="badge"><?php echo $docsource['owner']; ?></span>
                            <a href="search.php?submitted=true&amp;p=1&amp;q=owner:<?php echo $docsource['owner']; ?>&amp;doctype=<?php echo $_REQUEST['doctype']; ?>">Owner</a>
                        </li>
                        <li class="list-group-item">
                            <span class="badge"><?php echo $docsource['group']; ?></span>
                            <a href="search.php?submitted=true&amp;p=1&amp;q=group:<?php echo $docsource['group']; ?>&amp;doctype=<?php echo $_REQUEST['doctype']; ?>">Group</a>
                        </li>
                        <li class="list-group-item">
                            <span class="badge"><?php echo $docsource['ino']; ?></span>
                            <a href="search.php?submitted=true&amp;p=1&amp;q=ino:<?php echo $docsource['ino']; ?>&amp;doctype=<?php echo $_REQUEST['doctype']; ?>">Inode</a>
                        </li>
                        <li class="list-group-item">
                            <span class="badge"><?php echo $docsource['nlink']; ?></span>
                            Hardlinks
                        </li>
                    </ul>
                    <?php if ($showcostpergb) { ?>
                        <ul class="list-group">
                            <li class="list-group-item">
                                <span class="badge">$ <?php echo number_format(round($docsource['costpergb'], 2), 2); ?></span>
                                Cost per GB
                            </li>
                        </ul>
                    <?php } ?>
                    <ul class="list-group">
                        <?php
                        if (count(Constants::EXTRA_FIELDS) > 0) {
                            foreach (Constants::EXTRA_FIELDS as $key => $value) {
                                if (is_array($docsource[$value])) { ?>
                                    <li class="list-group-item">
                                        <?php echo $value; ?>
                                        <?php foreach ($docsource[$value] as $k => $v) { ?>
                                            <span class="badge"><?php echo $k . ': ' . $v; ?></span><br />
                                        <?php } ?>
                                    </li>
                                <?php } else { ?>
                                    <li class="list-group-item">
                                        <span class="badge"><?php echo $docsource[$value]; ?></span>
                                        <?php echo $key; ?>
                                    </li>
                                <?php } ?>
                        <?php }
                        } ?>
                    </ul>
                </div>
                <div class="col-xs-6">
                    <ul class="list-group">
                        <li class="list-group-item">
                            <span class="badge"><?php echo utcTimeToLocal($docsource['mtime']); ?></span>
                            Date modified
                        </li>
                        <li class="list-group-item">
                            <span class="badge"><?php echo utcTimeToLocal($docsource['atime']); ?></span>
                            Last accessed
                        </li>
                        <li class="list-group-item">
                            <span class="badge"><?php echo utcTimeToLocal($docsource['ctime']); ?></span>
                            Last changed
                        </li>
                    </ul>
                    <ul class="list-group">
                        <li class="list-group-item">
                            <span class="badge"><?php echo $docindex; ?></span>
                            <a href="search.php?submitted=true&amp;p=1&amp;q=_index:<?php echo $docindex; ?>&amp;doctype=<?php echo $doctype; ?>">Index name</a>
                        </li>
                    </ul>
                </div>
            </div>
        </div>
    </div>
    <?php include 'modals.php' ?>
    <script language="javascript" src="js/jquery.min.js"></script>
    <script language="javascript" src="js/bootstrap.min.js"></script>
    <script language="javascript" src="js/diskover.js"></script>
</body>

</html>