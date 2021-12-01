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
                        $fullpathhref = "search.php?index=" . $esIndex . "&submitted=true&p=1&q=parent_path:" . rawurlencode(escape_chars($fullpath)) . "&path=" . rawurlencode($fullpath);
                    } else {
                        $fullpathhref = "search.php?index=" . $esIndex . "&submitted=true&p=1&q=parent_path:" . rawurlencode(escape_chars($parentpath)) . " AND name:&quot;" . rawurlencode($filename) . "&quot;&path=" . rawurlencode($parentpath);
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
                                <li class="small"><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=parent_path:<?php echo rawurlencode(escape_chars($fullpath)); ?>"><i class="glyphicon glyphicon-search"></i> search path (non-recursive)</a></li>
                                <li class="small"><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=parent_path:(<?php echo rawurlencode(escape_chars($fullpath)) . ' OR ' . rawurlencode($fullpath_wildcard); ?>)"><i class="glyphicon glyphicon-search"></i> search path (recursive)</a></li>
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
                            <li class="small"><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=parent_path:<?php echo rawurlencode(escape_chars($parentpath)); ?>"><i class="glyphicon glyphicon-search"></i> search path (non-recursive)</a></li>
                            <li class="small"><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=parent_path:(<?php echo rawurlencode(escape_chars($parentpath)) . ' OR ' . rawurlencode($parentpath_wildcard); ?>)"><i class="glyphicon glyphicon-search"></i> search path (recursive)</a></li>
                        </ul>
                    </div>
                    <br /><br />
                </div>
            </div>
            <div class="row">
                <div class="col-xs-6">
                    <ul class="list-group">
                        <li class="list-group-item">
                            <span class="badge"><?php echo formatBytes($docsource['size']); ?></span>
                            Size
                        </li>
                        <li class="list-group-item">
                            <span class="badge"><?php echo formatBytes($docsource['size_du']); ?></span>
                            Allocated
                        </li>
                        <?php if ($_REQUEST['doctype'] == 'directory') {
                            $items = $docsource['file_count'] + $docsource['dir_count'];
                        ?>
                            <li class="list-group-item">
                                <span class="badge"><?php echo number_format($items); ?></span>
                                Items
                            </li>
                            <li class="list-group-item">
                                <span class="badge"><?php echo number_format($docsource['file_count']); ?></span>
                                Files
                            </li>
                            <li class="list-group-item">
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
                    <ul class="list-group">
                        <?php
                        if (count(Constants::EXTRA_FIELDS) > 0) {
                            foreach (Constants::EXTRA_FIELDS as $key => $value) {
                                if (is_array($docsource[$value])) { ?>
                                    <li class="list-group-item">
                                        <?php echo $key; ?>
                                        <?php foreach ($docsource[$value] as $k => $v) {
                                            if (is_array($v)) {
                                                foreach ($v as $v_key => $v_val) {
                                                    if (is_bool($v_val)) {
                                                        $v_val = ($v_val) ? 'true' : 'false';
                                                    } ?>
                                                    <span class="badge"><?php echo $v_key . ': ' . $v_val; ?></span><br />
                                                <?php }
                                            } else {
                                                if (is_bool($v)) {
                                                    $v = ($v) ? 'true' : 'false';
                                                } ?>
                                                <span class="badge"><?php echo $k . ': ' . $v; ?></span><br />
                                        <?php }
                                        } ?>
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