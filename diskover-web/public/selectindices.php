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
require "../src/diskover/Auth.php";
require "../src/diskover/Diskover.php";

# default max index age
$maxage_default = "all";
if (isset($_GET['maxage'])) {
    $maxage_str = $_GET['maxage'];
} else {
    $maxage_str = $maxage_default;
}

// check if select indices form submitted and set cookies for indices and paths, etc
if (isset($_POST['index'])) {
    $indexselected = $_POST['index'];
    createCookie('index', $indexselected);

    clearPaths();

    // set usecache to false (flush chart cache)
    createCookie('usecache', 0);

    // delete existing sort cookies
    deleteCookie('sort');
    deleteCookie('sortorder');
    deleteCookie('sort2');
    deleteCookie('sortorder2');

    // create cookies for default search sort
    createCookie('sort', 'parent_path');
    createCookie('sortorder', 'asc');
    createCookie('sort2', 'name');
    createCookie('sortorder2', 'asc');

    // reload same page
    header("location: selectindices.php?index=" . $indexselected . "&saved=true");
    exit();
}
// check if delete indices form is submitted
elseif (isset($_POST['delindices'])) {
    foreach ($_POST['delindices_arr'] as $k => $i) {
        if (!in_array($i, explode(',', $esIndex))) {
            try {
                $response = $client->indices()->delete(array('index' => $i));
                removeIndex($i);
            } catch (Exception $e) {
                handleError('ES error: ' . $e->getMessage(), true);
            }
            
            $deleted = true;
        } else {
            $deleted = false;
        }
    }
    if ($deleted) {
        $del_message = "Selected indices removed!";
        $del_warning = false;
    } else {
        $del_message = "Some indices could not be removed since they are in use.";
        $del_warning = true;
    }
}

// check if force delete index button is pressed
if (isset($_GET['forcedelindex'])) {
    try {
        $response = $client->indices()->delete(array('index' => $_GET['forcedelindex']));
        removeIndex($_GET['forcedelindex']);
    } catch (Exception $e) {
        handleError('ES error: ' . $e->getMessage(), true);
    }
    $del_message = "Index removed!";
    $del_warning = false;
}

// check if new indices selected
if (isset($_GET['saved'])) {
    $save_message = 'Index selection saved!';
}


// get additional index info for index table and filter indices that are displayed

$disabled_indices = array();
$indices_filtered = array();

// update max index cookie
if (isset($_GET['maxindex'])) {
    createCookie('maxindex', $_GET['maxindex']);
}

// go through each index and determine which are done indexing
foreach ($es_index_info as $key => $val) {
    // continue if index creation time is older than max age
    if ($maxage_str != 'all') {
        $starttime = $all_index_info[$key]['start_at'];
        $maxage = gmdate("Y-m-d\TH:i:s", strtotime($maxage_str));
        if ($maxage > $starttime) {
            continue;
        }
    }

    // continue if index name does not match
    if (isset($_GET['namecontains']) && $_GET['namecontains'] != '') {
        if (strpos($key, $_GET['namecontains']) === false) {
            continue;
        }
    }

    $indices_filtered[] = $key;

    // determine if index is still being crawled
    // if still being indexed, grab the file/dir count and size of top path and totals and add the index to disabled_indices list

    // Set the path finished to true
    if (isset($all_index_info[$key]['end_at'])) {
        $all_index_info[$key]['finished'] = 1;
    } else {
        $all_index_info[$key]['end_at'] = null;

        $diff = abs(strtotime($all_index_info[$key]['start_at']) - strtotime(gmdate("Y-m-d\TH:i:s")));
        $all_index_info[$key]['crawl_time'] = $diff;

        $searchParams = [];
        $searchParams['index'] = $key;

        $escaped_path = escape_chars($all_index_info[$key]['path']);
        if ($escaped_path === '\/') {  // root
            $pp_query = 'parent_path:' . $escaped_path . '*';
        } else {
            $pp_query = 'parent_path:(' . $escaped_path . ' OR ' . $escaped_path . '\/*)';
        }

        $searchParams['body'] = [
            'size' => 0,
            'track_total_hits' => true,
            'aggs' => [
                'total_size' => [
                    'sum' => [
                        'field' => 'size'
                    ]
                ]
            ],
            'query' => [
                'query_string' => [
                    'query' => $pp_query . ' AND type:"file"'
                ]
            ]
        ];

        // catch any errors searching doc in indices which might be corrupt or deleted
        try {
            $queryResponse = $client->search($searchParams);
        } catch (Exception $e) {
            error_log('ES error: ' .$e->getMessage());
            $ifk = array_search($key, $indices_filtered);
            unset($indices_filtered[$ifk]);
            unset($all_index_info[$key]);
            continue;
        }

        // Get count of file docs
        $all_index_info[$key]['file_count'] = $queryResponse['hits']['total']['value'];
        // Get size of file docs
        $all_index_info[$key]['file_size'] = $queryResponse['aggregations']['total_size']['value'];

        $searchParams = [];
        $searchParams['index'] = $key;

        $searchParams['body'] = [
            'size' => 0,
            'track_total_hits' => true,
            'query' => [
                'query_string' => [
                    'query' => $pp_query . ' AND type:"directory"'
                ]
            ]
        ];

        $queryResponse = $client->search($searchParams);

        // Get total count of directory docs
        $all_index_info[$key]['dir_count'] = $queryResponse['hits']['total']['value'];

        // Set the path finished to false
        $all_index_info[$key]['finished'] = 0;

        // Add to index totals
        $all_index_info[$key]['totals']['filecount'] += $all_index_info[$key]['file_count'];
        $all_index_info[$key]['totals']['filesize'] += $all_index_info[$key]['file_size'];
        $all_index_info[$key]['totals']['dircount'] += $all_index_info[$key]['dir_count'];
        $all_index_info[$key]['totals']['crawltime'] += $all_index_info[$key]['crawl_time'];
    
        # add index to disabled_indices list
        $disabled_indices[] = $key;
    }
}

$estime = number_format(microtime(true) - $_SERVER["REQUEST_TIME_FLOAT"], 4);

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
    <title>diskover &mdash; Indices</title>
    <link rel="stylesheet" href="css/fontawesome-free/css/all.min.css" media="screen" />
    <link rel="stylesheet" href="css/bootswatch.min.css" media="screen" />
    <link rel="stylesheet" href="css/diskover.css" media="screen" />
    <link rel="stylesheet" href="css/dataTables.bootstrap.min.css" media="screen" />
    <link rel="icon" type="image/png" href="images/diskoverfavico.png" />
</head>

<body>
    <?php include "nav.php"; ?>

    <div class="container-fluid" id="mainwindow" style="margin-top:70px">
        <?php
        if (isset($save_message)) {
            echo '<div class="row"><div class="col-lg-6"><div class="alert alert-dismissible alert-success">
                <button type="button" class="close" data-dismiss="alert">&times;</button>
                <strong>' . $save_message . '</strong></div></div></div>';
        } elseif (isset($del_message)) {
            $class = ($del_warning) ? "alert-warning" : "alert-success";
            echo '<div class="row"><div class="col-lg-6"><div class="alert alert-dismissible ' . $class . '">
            <button type="button" class="close" data-dismiss="alert">&times;</button>
            <strong>' . $del_message . '</strong> <a href="selectindices.php?maxage=' . $maxage_str . '&namecontains=' . $_GET['namecontains'] . '&reloadindices" class="alert-link">Reload indices</a>. Reloading in 3 seconds.</div></div></div>
            <script type="text/javascript">
            setTimeout(function(){
                window.location.href = "selectindices.php?maxage=' . $maxage_str . '&namecontains=' . $_GET['namecontains'] . '&reloadindices";
            }, 3000);
            </script>';
        }
        ?>
        <h1 class="page-header">Indices</h1>
        <div class="row">
            <div class="col-lg-6">
                <div class="alert alert-dismissible alert-info">
                    <button type="button" class="close" data-dismiss="alert">&times;</button>
                    <i class="glyphicon glyphicon-info-sign"></i> Please select one index in the Index column and click the Save selection button.
                </div>
            </div>
            <div class="col-lg-6">
                <div class="alert alert-dismissible alert-info">
                    <button type="button" class="close" data-dismiss="alert">&times;</button>
                    <i class="fas fa-lightbulb"></i> PRO tip: Indices can ben deleted by selecting an index and clicking the Delete button.
                </div>
            </div>
        </div>
        <div class="row">
            <div class="col-lg-12">
            <div class="well well-sm">
                        <div class="row">
                        <form action="<?php echo htmlspecialchars($_SERVER["PHP_SELF"]); ?>" method="get" class="form-horizontal" name="form-indexctrl">
                            <input type="hidden" name="reloadindices" value="true">
                            <div class="col-lg-6">
                                <div class="form-group">
                                    <label for="maxindex" class="col-lg-3 control-label">Max indices to load:</label>
                                    <div class="col-lg-2">
                                        <input class="form-control input-sm" name="maxindex" id="maxindex" value="<?php echo (isset($_GET['maxindex'])) ? $_GET['maxindex'] : getCookie('maxindex'); ?>">
                                    </div>
                                    <div class="col-lg-1">
                                        <button type="submit" class="btn btn-primary btn-sm" onclick="setCookie('maxindex', $('#maxindex').val())">Save</button>
                                    </div>
                                    <div class="col-lg-6">
                                        <span class="small" style="padding-left:5px"><i class="fas fa-info-circle"></i> Total <?php echo $esclient->getTotalIndices(); ?> indices, indices are loaded in order by creation date</span>
                                    </div>
                                </div>
                            </div>
                            <div class="col-lg-6">
                                <label for="uselatestindices" class="control-label">Always use latest indices (auto select)</label>
                                <input type="checkbox" name="uselatestindices" disabled> <span class="label label-info">Essential</span>
                            </div>
                        </form>
                        </div>
                    </div>
                <div class="well well-sm">
                    <div class="row">
                        <form action="<?php echo htmlspecialchars($_SERVER["PHP_SELF"]); ?>" method="get" class="form-horizontal" name="form-indexfilter">
                            <div class="col-lg-4">
                                <div class="form-group">
                                    <label for="maxage" class="col-lg-6 control-label">Show indices newer than:</label>
                                    <div class="col-lg-6">
                                        <select class="form-control input-sm" name="maxage" id="maxage">
                                            <option value="all" <?php echo $maxage_str == 'all' ? 'selected="selected"' : ''; ?>>All</option>
                                            <option value="- 1 year" <?php echo $maxage_str == '- 1 year' ? 'selected="selected"' : ''; ?>>1 year</option>
                                            <option value="- 6 months" <?php echo $maxage_str == '- 6 months' ? 'selected="selected"' : ''; ?>>6 months</option>
                                            <option value="- 3 months" <?php echo $maxage_str == '- 3 months' ? 'selected="selected"' : ''; ?>>3 months</option>
                                            <option value="- 1 month" <?php echo $maxage_str == '- 1 month' ? 'selected="selected"' : ''; ?>>1 month</option>
                                            <option value="- 2 weeks" <?php echo $maxage_str == '- 2 weeks' ? 'selected="selected"' : ''; ?>>2 weeks</option>
                                            <option value="- 1 week" <?php echo $maxage_str == '- 1 week' ? 'selected="selected"' : ''; ?>>1 week</option>
                                            <option value="- 2 days" <?php echo $maxage_str == '- 2 days' ? 'selected="selected"' : ''; ?>>2 days</option>
                                            <option value="- 1 day" <?php echo $maxage_str == '- 1 day' ? 'selected="selected"' : ''; ?>>1 day</option>
                                        </select>
                                    </div>
                                </div>
                            </div>
                            <div class="col-lg-6">
                                <div class="form-group">
                                    <label for="namecontains" class="col-lg-5 control-label">Index name contains:</label>
                                    <div class="col-lg-7">
                                        <input class="form-control input-sm" name="namecontains" id="namecontains" autocomplete="off" value="<?php echo $_GET['namecontains']; ?>">
                                    </div>
                                </div>
                            </div>
                            <div class="col-lg-2">
                                <button type="submit" class="btn btn-primary btn-sm"><i class="fas fa-filter"></i> Go</button>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        </div>
        <?php if (empty($indices_filtered)) { ?>
            <div class="row">
                <div class="col-lg-6">
                    <div class="alert alert-dismissible alert-warning">
                        <button type="button" class="close" data-dismiss="alert">&times;</button>
                        <i class="glyphicon glyphicon-exclamation-sign"></i> No diskover indices found in Elasticsearch or index filters above are set and all indices are hidden. Try setting show indices to All or <a class="alert-link" href="selectindices.php?maxage=<?php echo $maxage_str ?>&namecontains=<?php echo $_GET['namecontains'] ?>&reloadindices">reload indices</a>.
                    </div>
                </div>
            </div>
        <?php } else { ?>
            <div class="row">
                <div class="col-lg-12">
                    <div class="form-group">
                        <button type="button" class="btn btn-primary" id="savebutton" onclick="checkSelectedIndex()"><i class="glyphicon glyphicon-saved"></i> Save selection</button>
                        <button title="reload indices and refresh list" type="button" class="btn btn-default pull-right" id="reloadindices" onclick="window.location.replace('selectindices.php?maxage=<?php echo $maxage_str ?>&namecontains=<?php echo $_GET['namecontains'] ?>&reloadindices')"><i class="fas fa-sync-alt"></i> Reload indices</button>
                    </div>
                </div>
            </div>
            <div class="row">
                <div class="col-lg-12">
                    <p class="pull-right"><?php echo count($indices_filtered) . " indices found"; ?> (last updated <?php echo $indexinfo_updatetime->format('m/d/Y, h:i:s A T'); ?> <a href="selectindices.php?maxage=<?php echo $maxage_str ?>&namecontains=<?php echo $_GET['namecontains'] ?>&reloadindices">update</a>)</p>
                    <form action="<?php echo htmlspecialchars($_SERVER["PHP_SELF"]); ?>" method="post" name="form-selectindex" id="form-selectindex">
                        <table class="table table-striped table-hover table-condensed" id="indices-table" data-order='[[ 4, "desc" ]]' style="width:100%">
                            <thead>
                                <tr>
                                    <th>Index</th>
                                    <th>Index Name</th>
                                    <th>Top Path</th>
                                    <th>Start Time</th>
                                    <th>Finish Time</th>
                                    <th>Crawl Time</th>
                                    <th>Files</th>
                                    <th>Folders</th>
                                    <th>Inodes/sec</th>
                                    <th>File Size</th>
                                    <th>Index Size</th>
                                </tr>
                            </thead>
                            <tbody>
                                <?php
                                if (!empty($indices_filtered)) {
                                    $index = getCookie('index');
                                    foreach ($indices_filtered as $key => $val) {
                                        $indexval = $all_index_info[$val];
                                        $newest = ($val == $latest_completed_index) ? "<i title=\"newest\" style=\"color:#FFF\" class=\"glyphicon glyphicon-calendar\"></i>" : "";
                                        $checked = ($val == $index) ? 'checked' : '';
                                        $disabled = (in_array($val, $disabled_indices)) ? true : false;
                                        $startat = utcTimeToLocal($indexval['start_at']);
                                        $endat = (is_null($indexval['end_at'])) ? "<span style=\"color:white\"><i class=\"fas fa-sync-alt\"></i> indexing...</span>" : utcTimeToLocal($indexval['end_at']);
                                        $filecount = number_format($indexval['file_count']);
                                        $dircount = number_format($indexval['dir_count']);
                                        $crawltime = (is_null($indexval['crawl_time'])) ?: secondsToTime($indexval['crawl_time']);
                                        $inodessec = number_format(($indexval['file_count'] + $indexval['dir_count']) / $indexval['crawl_time'], 1);
                                        $filesize = formatBytes($indexval['file_size']);
                                        $indexsize = formatBytes($indexval['totals']['indexsize']);
                                        echo "<tr>
                                        <td>";
                                        if (!$disabled) {
                                            echo "<input onclick=\"toggleHiddenInput(this)\" type=\"radio\" name=\"index\" id=\"index_" . $val . "\" class=\"indexcheck\" value=\"" . $val . "\" $checked></td>";
                                        } else {
                                            echo "<a href=\"#\" title=\"force delete\" onclick=\"checkForceIndexDel('" . $val . "')\" class=\"btn btn-xs btn-primary\"><i class=\"far fa-trash-alt\"></i>";
                                        }
                                        echo "<td>" . $val . " " . $newest . "</td>
                                        <td>" . $indexval['path'] . "</td>
                                        <td class=\"text-muted\">" . $startat. "</td>
                                        <td class=\"text-muted\">" . $endat . "</td>
                                        <td class=\"text-muted\">" . $crawltime . "</td>
                                        <td class=\"text-muted\">" . $filecount . "</td>
                                        <td class=\"text-muted\">" . $dircount . "</td>
                                        <td class=\"text-muted\">" . $inodessec. "</td>
                                        <td class=\"text-muted\">" . $filesize . "</td>
                                        <td class=\"text-muted\">" . $indexsize . "</td>
                                        </tr>";
                                    }
                                }
                                ?>
                            </tbody>
                            <tfoot>
                                <tr>
                                    <th>Index</th>
                                    <th>Index Name</th>
                                    <th>Top Path</th>
                                    <th>Start Time</th>
                                    <th>Finish Time</th>
                                    <th>Crawl Time</th>
                                    <th>Files</th>
                                    <th>Folders</th>
                                    <th>Inodes/sec</th>
                                    <th>File Size</th>
                                    <th>Index Size</th>
                                </tr>
                            </tfoot>
                        </table>
                    </form>
                    <p class="pull-right"><?php echo count($indices_filtered) . " indices found"; ?> (last updated <?php echo $indexinfo_updatetime->format('m/d/Y, h:i:s A T'); ?> <a href="selectindices.php?maxage=<?php echo $maxage_str ?>&namecontains=<?php echo $_GET['namecontains'] ?>&reloadindices">update</a>)</p>
                </div>
            </div>
            <div class="row">
                <div class="col-lg-12">
                    <div class="form-group">
                        <button type="button" class="btn btn-primary" id="savebutton2" onclick="checkSelectedIndex()"><i class="glyphicon glyphicon-saved"></i> Save selection</button>
                    </div>
                </div>
            </div>
            <div class="row">
                <div class="col-lg-6">
                    <form name="form-deleteindex" action="<?php echo htmlspecialchars($_SERVER["PHP_SELF"]); ?>" method="post" id="form-deleteindex">
                        <input type="hidden" name="delindices" id="delindices" value="">
                        <button type="button" class="btn btn-primary" id="deletebutton" onclick="checkIndexDel()"><i class="far fa-trash-alt"></i> Delete</button>
                    </form>
                </div>
            </div>
        <?php } ?>
    </div>

    <?php include 'modals.php' ?>

    <script language="javascript" src="js/jquery.min.js"></script>
    <script language="javascript" src="js/bootstrap.min.js"></script>
    <script language="javascript" src="js/diskover.js"></script>
    <script language="javascript" src="js/jquery.dataTables.min.js"></script>
    <script language="javascript" src="js/dataTables.bootstrap.min.js"></script>
    <script language="javascript" src="js/file-size.js"></script>
    <script language="javascript" src="js/time-elapsed-dhms.js"></script>
    <script type="text/javascript">
        $(document).ready(function() {
            addHidden();
            checkSelected();

            // make data table
            $("#indices-table").DataTable({
                "stateSave": true,
                "lengthMenu": [10, 25, 50, 75, 100],
                "pageLength": 25,
                "columnDefs": [{
                        "type": "file-size",
                        targets: [9, 10]
                    },
                    {
                        "type": "time-elapsed-dhms",
                        targets: [5]
                    },
                    {
                        "orderable": false,
                        targets: [0]
                    }
                ]
            });
        });
    </script>
</body>

</html>