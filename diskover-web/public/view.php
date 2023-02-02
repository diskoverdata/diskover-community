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

require '../vendor/autoload.php';
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
                    //'type' => '_doc',
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
                        $fullpathhref = "search.php?index=" . $esIndex . "&submitted=true&p=1&q=parent_path:" . rawurlencode(escape_chars($parentpath)) . " AND name:&quot;" . rawurlencode(escape_chars($filename)) . "&quot;&path=" . rawurlencode($parentpath);
                    }
                    ?>
                    <h2 class="path"><?php echo ($doctype == 'file') ? '<i class="fas fa-file-alt" style="color:#738291;"></i>' : '<i class="fas fa-folder" style="color:#E9AC47;"></i>'; ?> <span id="filename"><a href="<?php echo $fullpathhref; ?>" target="_blank"><?php echo $filename; ?></a></span></h2>
                    <div style="padding-bottom:10px"><a href="#" class="btn btn-default btn-xs file-btns" onclick="copyToClipboard('#filename')"><i class="glyphicon glyphicon-copy"></i> Copy file name</a></div>
                    <h5 class="path">Full path: <span id="fullpath"><a href="<?php echo $fullpathhref; ?>" target="_blank"><?php echo $fullpath; ?></a></span></h5> <a href="#" class="btn btn-default btn-xs file-btns" onclick="copyToClipboard('#fullpath')"><i class="glyphicon glyphicon-copy"></i> Copy path</a>
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
                                <li class="small"><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=parent_path:<?php echo rawurlencode(escape_chars($fullpath)); ?>" target="_blank"><i class="glyphicon glyphicon-search"></i> search path (non-recursive)</a></li>
                                <li class="small"><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=parent_path:(<?php echo rawurlencode(escape_chars($fullpath)) . ' OR ' . rawurlencode($fullpath_wildcard); ?>)" target="_blank"><i class="glyphicon glyphicon-search"></i> search path (recursive)</a></li>
                            </ul>
                        </div>
                        <br />
                    <?php } ?>
                    <h5 class="path"><i class="fas fa-folder" style="color:#E9AC47;"></i> <span style="color:gray">Parent path: <span id="parentpath"><a href="search.php?submitted=true&p=1&q=parent_path:<?php echo rawurlencode(escape_chars($parentpath)); ?>&path=<?php echo rawurlencode($parentpath); ?>" target="_blank"><?php echo $parentpath; ?></a></span> </span></h5> <a href="#" class="btn btn-default btn-xs file-btns" onclick="copyToClipboard('#parentpath')"><i class="glyphicon glyphicon-copy"></i> Copy path</a>
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
                            <li class="small"><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=parent_path:<?php echo rawurlencode(escape_chars($parentpath)); ?>" target="_blank"><i class="glyphicon glyphicon-search"></i> search path (non-recursive)</a></li>
                            <li class="small"><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=parent_path:(<?php echo rawurlencode(escape_chars($parentpath)) . ' OR ' . rawurlencode($parentpath_wildcard); ?>)" target="_blank"><i class="glyphicon glyphicon-search"></i> search path (recursive)</a></li>
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
                                <a href="search.php?submitted=true&amp;p=1&amp;q=extension:<?php echo $docsource['extension']; ?>&amp;doctype=<?php echo $_REQUEST['doctype']; ?>" target="_blank">Extension</a>
                            </li>
                        <?php } ?>
                        <li class="list-group-item">
                            <span class="badge"><?php echo $docsource['owner']; ?></span>
                            <a href="search.php?submitted=true&amp;p=1&amp;q=owner:<?php echo $docsource['owner']; ?>&amp;doctype=<?php echo $_REQUEST['doctype']; ?>" target="_blank">Owner</a>
                        </li>
                        <li class="list-group-item">
                            <span class="badge"><?php echo $docsource['group']; ?></span>
                            <a href="search.php?submitted=true&amp;p=1&amp;q=group:<?php echo $docsource['group']; ?>&amp;doctype=<?php echo $_REQUEST['doctype']; ?>" target="_blank">Group</a>
                        </li>
                        <li class="list-group-item">
                            <span class="badge"><?php echo $docsource['ino']; ?></span>
                            <a href="search.php?submitted=true&amp;p=1&amp;q=ino:<?php echo $docsource['ino']; ?>&amp;doctype=<?php echo $_REQUEST['doctype']; ?>" target="_blank">Inode</a>
                        </li>
                        <li class="list-group-item">
                            <span class="badge"><?php echo $docsource['nlink']; ?></span>
                            Hardlinks
                        </li>
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
                            <a href="search.php?submitted=true&amp;p=1&amp;q=_index:<?php echo $docindex; ?>" target="_blank">Index name</a>
                        </li>
                    </ul>
                    <ul class="list-group">
                        <li class="list-group-item">
                            <span class="badge"><?php echo $docid; ?></span>
                            <a href="search.php?submitted=true&amp;p=1&amp;q=_id:<?php echo $docid; ?>" target="_blank">Doc id</a>
                        </li>
                    </ul>
                </div>
            </div>
            <?php if (count($config->EXTRA_FIELDS) > 0) { ?>
            <div class="row">
                <div class="col-xs-12">
                    <h4>Extra fields</h4>
                    <ul class="list-group">
                        <?php foreach ($config->EXTRA_FIELDS as $key => $value) {
                                // check if field empty
                                if (empty($docsource[$value])) {
                                    echo '<li class="list-group-item">';
                                    echo '<p class="list-group-item-text">No ' . $key . ' in doc</p>';
                                    echo '</li>';
                                    continue;
                                }
                                // check if object field type
                                if (is_array($docsource[$value])) { ?>
                                    <li class="list-group-item">
                                        <h5 class="list-group-item-heading"><?php echo $key; ?></h5>
                                        <?php foreach ($docsource[$value] as $k => $v) {
                                            if (is_array($v)) {
                                                foreach ($v as $v_key => $v_val) {
                                                    if (is_array($v_val)) {
                                                        foreach ($v_val as $v2_key => $v2_val) {
                                                            if (is_bool($v2_val)) {
                                                                $v2_val = ($v2_val) ? 'true' : 'false';
                                                            } ?>
                                                            <p class="list-group-item-text extrafields"><a href="search.php?submitted=true&amp;p=1&amp;q=<?php echo $value . '.' . $k . '.' . $v2_key . ': &quot;' . $v2_val; ?>&quot;&amp;doctype=<?php echo $_REQUEST['doctype']; ?>" target="_blank"><?php echo $value . '.' . $k . '.' . $v2_key . ': <strong>' . $v2_val . '</strong>'; ?></a></p>
                                                    <?php }
                                                    } else {
                                                        if (is_bool($v_val)) {
                                                            $v_val = ($v_val) ? 'true' : 'false';
                                                        } ?>
                                                        <p class="list-group-item-text extrafields"><a href="search.php?submitted=true&amp;p=1&amp;q=<?php echo $value . '.' . $k . '.' . $v_key . ': &quot;' . $v_val; ?>&quot;&amp;doctype=<?php echo $_REQUEST['doctype']; ?>" target="_blank"><?php echo $value . '.' . $k . '.' . $v_key . ': <strong>' . $v_val . '</strong>'; ?></a></p>
                                                <?php } }
                                            } else {
                                                if (is_bool($v)) {
                                                    $v = ($v) ? 'true' : 'false';
                                                } 
                                                $ef_string = $value . '.' . $k . ': <strong>' . $v . '</strong>';
                                                ?>
                                                <p class="list-group-item-text extrafields"><a href="search.php?submitted=true&amp;p=1&amp;q=<?php echo $value . '.' . $k . ': &quot;' . $v; ?>&quot;&amp;doctype=<?php echo $_REQUEST['doctype']; ?>" target="_blank"><?php echo $ef_string; ?></a></p>
                                        <?php }
                                        } ?>
                                    </li>
                                <?php } else { 
                                    # bool field
                                    if (is_bool($docsource[$value])) {
                                        $docsource[$value] = ($docsource[$value]) ? 'true' : 'false';
                                    }
                                    ?>
                                    <li class="list-group-item">
                                        <h5 class="list-group-item-heading"><?php echo $key; ?></h5>
                                        <p class="list-group-item-text extrafields"><a href="search.php?submitted=true&amp;p=1&amp;q=<?php echo $value .':&quot;' . $docsource[$value]; ?>&quot;&amp;doctype=<?php echo $_REQUEST['doctype']; ?>"><?php echo $value . ': <strong>' . $docsource[$value] . '</strong>'; ?></a></p>
                                    </li>
                        <?php } } ?>
                    </ul>
                </div>
            </div>
            <?php } ?>
        </div>
    </div>
    <?php include 'modals.php' ?>
    <script language="javascript" src="js/jquery.min.js"></script>
    <script language="javascript" src="js/bootstrap.min.js"></script>
    <script language="javascript" src="js/diskover.js"></script>
</body>

</html>