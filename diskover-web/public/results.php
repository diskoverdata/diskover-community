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
require '../src/diskover/config_inc.php';

error_reporting(E_ALL ^ E_NOTICE);


// get top path's last indexed time
$dt = new DateTime($index_starttimes[$esIndex][$_SESSION['rootpath']], new DateTimeZone('UTC'));
$dt->setTimezone(new DateTimeZone($timezone));
$toppath_name = ($_SESSION['rootpath'] == '/') ? '/' : basename($_SESSION['rootpath']);
$last_index_time = "Last indexed " . $toppath_name . " at " . $dt->format('m/d/Y, h:i:s A T');

// display results
//print_r($_SERVER);
echo '<script type="text/javascript">
    var loadtree = true;
    </script>';
// es search query
$searchquery = $searchParams['body']['query']['query_string']['query'];
$searchquery_notype = str_replace(" AND type:(file OR directory)", "", $searchquery);
$searchquery_noext = preg_replace("/extension:\w+ AND /", "", $searchquery_notype);
// hide search tree
$hidetree = getCookie('hidesearchtree');
// hide directory charts
$hidecharts = getCookie('hidesearchcharts');
?>
<div class="container-fluid" id="mainwindow" style="margin-top:70px">
    <div class="row">
        <div class="col-lg-2 <?php echo ($hidetree == 0 || empty($hidetree)) ? 'tree-button-wrapper' : 'tree-button-wrapper-sm' ?>" id="tree-button-wrapper">
            <div id="tree-button-container" style="display:<?php echo ($hidetree == 0 || empty($hidetree)) ? 'block' : 'none' ?>">
                <a href="#" class="btn btn-default btn-sm" title="Top path" onclick="goToTreeTop()"><i class="glyphicon glyphicon-home"></i> Top</a>
                <a href="#" class="btn btn-default btn-sm" title="Up" onclick="goToTreeUp()"><i class="glyphicon glyphicon-circle-arrow-up"></i> Up</a>
                <a href="#" class="btn btn-default btn-sm" title="Back" onclick="goToTreeBack()"><i class="glyphicon glyphicon-arrow-left"></i></a>
                <a href="#" class="btn btn-default btn-sm" title="Forward" onclick="goToTreeForward()"><i class="glyphicon glyphicon-arrow-right"></i></a>
                <br><a href="#" class="btn btn-default btn-sm" title="Show/hide file tree" onclick="hideTree()"><i class="far fa-eye-slash"></i> Tree</a>
                <a href="#" class="btn btn-sm btn-default" title="Show/hide directory charts" onclick="hideCharts()"><i class="far fa-eye-slash"></i> Charts</a>
                <a href="#" class="btn btn-sm btn-default reload-results" title="Reload tree and chart data"><i class="glyphicon glyphicon-refresh"></i> Reload</a>
            </div>
            <div id="tree-button-container-sm" style="display:<?php echo ($hidetree == 0 || empty($hidetree)) ? 'none' : 'block' ?>">
                <a href="#" class="btn btn-default btn-sm" title="Top path" onclick="goToTreeTop()"><i class="glyphicon glyphicon-home"></i></a>
                <a href="#" class="btn btn-default btn-sm" title="Up" onclick="goToTreeUp()"><i class="glyphicon glyphicon-circle-arrow-up"></i></a>
                <a href="#" class="btn btn-default btn-sm" title="Back" onclick="goToTreeBack()"><i class="glyphicon glyphicon-arrow-left"></i></a>
                <a href="#" class="btn btn-default btn-sm" title="Forward" onclick="goToTreeForward()"><i class="glyphicon glyphicon-arrow-right"></i></a>
                <br><a href="#" class="btn btn-default btn-sm" title="Show/hide file tree" onclick="hideTree()"><i class="far fa-eye-slash"></i></a>
                <a href="#" class="btn btn-sm btn-default" title="Show/hide directory charts" onclick="hideCharts()"><i class="far fa-eye-slash"></i></a>
                <a href="#" class="btn btn-sm btn-default reload-results" title="Reload tree and chart data"><i class="glyphicon glyphicon-refresh"></i></a>
            </div>
        </div>
    </div>
    <div class="row">
        <?php
        if ($hidetree == 0 || empty($hidetree)) { ?>
            <div class="col-lg-2 tree-wrapper" id="tree-wrapper">
                <!-- storage drive icons start -->
                <div id="tree-container-toppaths" class="tree-container-toppaths">
                    <?php
                    $toppath = $_SESSION['rootpath'];
                    $pathlabel = ($toppath == '/') ? $toppath : basename($toppath);
                    $dt = new DateTime($index_starttimes[$esIndex][$toppath], new DateTimeZone('UTC'));
                    $dt->setTimezone(new DateTimeZone($timezone));
                    $index_time = $dt->format('m/d/Y, h:i:s A T');
                    $title = $toppath . " | index " . $esIndex . " | last indexed " . $index_time;
                    # get disk space info
                    $space_total = $index_spaceinfo[$esIndex][$toppath]['total'];
                    $space_available = $index_spaceinfo[$esIndex][$toppath]['available'];
                    $space_used = $index_spaceinfo[$esIndex][$toppath]['used'];
                    $available_percent = round($space_available / $space_total * 100);
                    $used_percent = 100 - $available_percent;
                    # color bar based on used percent
                    if ($used_percent >= 80 && $used_percent < 90) {
                        $barcolor = "#C9D66F";
                    } elseif ($used_percent >= 90) {
                        $barcolor = "#8A313D";
                    } else {
                        $barcolor = "#468147";
                    }
                    $title_space = "Space used: " . formatBytes($space_used) . " (" . $used_percent . " %) | available: " . formatBytes($space_available) . " | total: " . formatBytes($space_total);
                    echo "<span title=\"" . $title . "\" class=\"searchtree-toppath\" style=\"opacity:1; width:60%; float:left; display:block; font-weight:bold\"><a href=\"search.php?index=" . $esIndex . "&q=parent_path:" . rawurlencode(escape_chars($toppath)) . "&submitted=true&p=1&path=" . rawurlencode($toppath) . "\"><i class=\"far fa-hdd\" style=\"margin-right:5px; font-weight:bold\"></i> " . $pathlabel . "</a></span>
                    <div title=\"" . $title_space . "\" class=\"progress\" style=\"width:75px; float:right; background-color:#121416; display:block; margin:0 auto; height:6px;top:9px;position:relative\">
                        <div class=\"progress-bar\" style=\"opacity:1; background-color:" . $barcolor . "; width:" . $used_percent . "%\"></div>
                    </div><div style=\"height:13px\"></div>";
                    ?>
                </div>
                <!-- storage drive icons end -->
                <div id="tree-container" class="tree-container"></div>
            </div>
            <div class="col-lg-10 search-results-wrapper" id="search-results-wrapper">
            <?php } else { ?>
                <div class="col-lg-2 tree-wrapper" id="tree-wrapper" style="display:none;">
                    <div id="tree-container" class="tree-container"></div>
                </div>
                <div class="col-lg-12 search-results-wrapper-lg" id="search-results-wrapper">
                <?php } ?>
                <?php
                // check for search results and if there are no results, display no results message 
                if (!empty($results[$p]) && count($results[$p]) > 0) { ?>
                    <!-- search results info -->
                    <div class="alert alert-dismissible alert-success" id="results-info">
                        <button type="button" class="close" data-dismiss="alert">&times;</button>
                        <?php
                        $rs = $searchParams['size'];
                        $cp = $_GET['p'];
                        $ei = $rs * $cp;
                        $si = $ei - $rs + 1;
                        ?>
                        <i class="glyphicon glyphicon-search"></i> Showing <strong><?php echo $si; ?></strong> to <strong><?php echo $ei; ?></strong> of <?php echo number_format($total); ?> items found in <?php echo $estime ?> seconds.
                        <span>Results size: <?php echo formatBytes($total_size); ?> <span class="small">(this page)</span>.</span>
                        <span>Search query: <i><strong><?php echo $searchParams['body']['query']['query_string']['query'] ?></strong></i></span>
                    </div>
                    <!-- end search results info -->
                    <!-- path breadcrumb -->
                    <div id="path-breadcrumb-wrapper">
                        <!-- split path links start -->
                        <ul class="breadcrumb">
                            <?php
                            $splitpath = explode('/', $path);
                            $x = substr_count($_SESSION['rootpath'], '/');
                            $splitpath = array_slice($splitpath, $x);
                            $pathfull = dirname($_SESSION['rootpath']);
                            if ($pathfull == '/') $pathfull = '';
                            $n = 0;
                            foreach ($splitpath as $pathitem) {
                                $pathfull .= '/' . $pathitem;
                                $active = ($n == 0) ? 'style="font-weight:bolder"' : '';
                                $ico = ($n == 0) ? '<i class="far fa-hdd"></i>' : '<i class="far fa-folder"></i>';
                                echo '<li ' . $active . '><a title="' . $pathfull . '" href="search.php?index=' . $esIndex, '&amp;index2=' . $esIndex2 . '&amp;q=parent_path:' . rawurlencode(escape_chars($pathfull)) . '&amp;submitted=true&amp;p=1&amp;path=' . rawurlencode($pathfull) . '">' . $ico . ' ' . $pathitem . '</a></li>';
                                $n += 1;
                            }
                            ?>
                        </ul>
                        <!-- split path links end -->
                    </div>
                    <!-- end path breadcrumb -->
                    <!-- directory charts -->
                    <div class="panel panel-default" id="searchCharts-container" style="display:<?php echo ($hidecharts == 0 || empty($hidecharts)) ? 'block' : 'none' ?>">
                        <div class="panel-heading">
                            <div id="dirdetails" style="font-size:13px"></div>
                        </div>
                        <div class="panel-body">
                            <div style="margin:0 auto; width:100%; height:125px; margin-bottom:10px; border:1px solid #121416; padding:5px" id="mtime-Chart-container">
                                <canvas id="mtime-barChart"></canvas>
                            </div>
                            <div style="margin:0 auto; width:100%;">
                                <div style="margin:0 auto; width:100%; height:220px; margin-bottom:10px; border:1px solid #121416; padding:5px" class="text-center" id="topDirs-Chart-container">
                                    <div style="margin:0 auto; width:40%; height:200px; display:inline-block" class="text-center">
                                        <canvas id="topDirsBySize-barChart"></canvas>
                                    </div>
                                    <div style="margin:0 auto; width:55%; height:200px; display:inline-block" class="text-center">
                                        <canvas id="topDirsByCount-pieChart"></canvas>
                                    </div>
                                </div>
                                <div style="margin:0 auto; width:100%; height:220px; border:1px solid #121416; padding:5px" class="text-center" id="topFileTypes-Chart-container">
                                    <div style="margin:0 auto; width:40%; height:200px; display:inline-block">
                                        <canvas id="topFileTypesBySize-barChart"></canvas>
                                    </div>
                                    <div style="margin:0 auto; width:55%; height:200px; display:inline-block">
                                        <canvas id="topFileTypesByCount-pieChart"></canvas>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    <!-- end directory charts -->
                    <div class="panel panel-default" style="margin-bottom: 5px">
                        <div class="panel-body">
                            <div class="btn-group" style="display:inline-block;">
                                <button class="btn btn-default" title="select all" id="button-selectall" onclick="selectAll(); toggleTagButton(); toggleFileActionButton(); updateSelectedList()"><i class="far fa-check-square"></i>&nbsp;Select All</button>
                            </div>
                            <div class="btn-group" style="display:inline-block;">
                                <button class="btn btn-default" title="unselect all" id="button-unselectall" onclick="unSelectAll(); toggleTagButton(); toggleFileActionButton(); updateSelectedList()"><i class="far fa-square"></i>&nbsp;Unselect All</button>
                            </div>
                            <!-- tag dropdown -->
                            <div class="btn-group" style="display:inline-block;">
                                <input type="hidden" name="checkedids" id="checkedids" value="">
                                <input type="hidden" name="checkedindices" id="checkedindices" value="">
                                <input type="hidden" name="multitag" id="multitag" value="">
                                <input type="hidden" name="multitag_newtagtext" id="multitag_newtagtext" value="">
                                <button title="tag" id="tagbutton" class="btn btn-default dropdown-toggle" type="button" data-toggle="dropdown" disabled="disabled"><i class="glyphicon glyphicon-tag"></i> Tag <span class="label label-info">Pro</span>
                                    <span class="caret"></span></button>
                                <ul class="dropdown-menu multi-level" role="menu">
                                    <li><a href="#">Pro version required</a></li>
                                </ul>
                            </div>
                            <!-- end tag dropdown -->
                            <!-- export button -->
                            <div class="btn-group" style="display:inline-block;">
                                <a href="#" class="btn btn-default dropdown-toggle" data-toggle="dropdown" aria-expanded="false" title="export search results">
                                    <i class="glyphicon glyphicon-export"></i> Export
                                    <span class="caret"></span>
                                </a>
                                <ul class="dropdown-menu">
                                    <li><a href="#">Files this page (json) <span class="label label-info">Essential</span></a></li>
                                    <li><a href="#">Files all pages (json) <span class="label label-info">Essential</span></a></li>
                                    <li><a href="#">Files this page (csv) <span class="label label-info">Essential</span></a></li>
                                    <li><a href="#">Files all pages (csv) <span class="label label-info">Essential</span></a></li>
                                    <li class="divider"></li>
                                    <li><a href="#">Directories this page (json) <span class="label label-info">Essential</span></a></li>
                                    <li><a href="#">Directories all pages (json) <span class="label label-info">Essential</span></a></li>
                                    <li><a href="#">Directories this page (csv) <span class="label label-info">Essential</span></a></li>
                                    <li><a href="#">Directories all pages (csv) <span class="label label-info">Essential</span></a></li>
                                    <li class="divider"></li>
                                    <li><a href="javascript:copyPathsToClipboard(true)">Copy all paths this page</a></li>
                                    <li><a href="javascript:copyPathsToClipboard(false)">Copy all file names this page</a></li>
                                    <li><a href="javascript:copySelectedPathsToClipboard(true)">Copy selected paths this page</a></li>
                                    <li><a href="javascript:copySelectedPathsToClipboard(false)">Copy selected file names this page</a></li>
                                </ul>
                            </div>
                            <!-- end export button -->
                            <!-- share button -->
                            <div class="btn-group" style="display:inline-block;">
                                <a href="#" class="btn btn-default dropdown-toggle" data-toggle="dropdown" aria-expanded="false" title="share">
                                    <i class="fas fa-share-square"></i> Share
                                    <span class="caret"></span>
                                </a>
                                <ul class="dropdown-menu">
                                    <li><a href="#">Search results url <span class="label label-info">Essential</span></a></li>
                                    <li><a href="#">Search query <span class="label label-info">Essential</span></a></li>
                                </ul>
                            </div>
                            <!-- end share button -->
                            <!-- file action button -->
                            <div class="btn-group" style="display:inline-block;">
                                <button title="file action" id="fileactionbutton" class="btn btn-default dropdown-toggle" type="button" data-toggle="dropdown" disabled="disabled"><i class="fas fa-cogs"></i> File Action <span class="label label-info">Pro</span>
                                    <span class="caret"></span></button>
                                <ul class="dropdown-menu">
                                    <li><a href="#">Pro version required</a></li>
                                </ul>
                            </div>
                            <!-- end file action button -->
                            <!-- index update time -->
                            <div class="small pull-right" style="padding-top:10px"><i class="fas fa-clock"></i> <?php echo $last_index_time ?></div>
                            <!-- end index update time -->
                        </div>
                    </div>
                    <!-- extension buttons -->
                    <?php
                    if ($_GET['doctype'] !== "directory") { ?>
                        <div class="panel panel-default">
                            <div class="panel-body">
                                <div class="btn-group" style="display:inline-block;">
                                    <ul class="pager" style="margin: 0px auto">
                                        <label>Extension</label>
                                        <li><a title="All file types" href="search.php?submitted=true&p=1&q=<?php echo rawurlencode($searchquery_noext) ?>&doctype=file">All</a></li>
                                        <?php foreach ($ext_onpage as $ext => $ext_arr) {
                                            $ext_count = $ext_arr[0];
                                            $ext_size = $ext_arr[1];
                                            if ($ext_count > 1) {
                                                $ext_label = $ext . ' <span style="color:cadetblue;font-weight:bold;">' . $ext_count . '</span>';
                                            } else {
                                                $ext_label = $ext;
                                            }
                                        ?>
                                            <li><a title="<?php echo $ext_count . " items, " . formatBytes($ext_size) . " total this page"; ?>" href="search.php?submitted=true&p=1&q=extension:<?php echo ($ext == "NULL") ? "%22%22" : $ext; ?> AND <?php echo rawurlencode($searchquery_notype) ?>&doctype=file"><?php echo $ext_label; ?></a></li>
                                        <?php } ?>
                                    </ul>
                                </div>
                            </div>
                        </div>
                    <?php } ?>
                    <!-- end extension buttons -->
                    <div class="row">
                        <!-- num of results -->
                        <div class="col-lg-8">
                            <form class="form-inline" style="display:inline-block;" method="get" action="<?php echo htmlspecialchars($_SERVER["PHP_SELF"]); ?>" id="resultsperpage">
                                <?php
                                foreach ($_GET as $name => $value) {
                                    $name = htmlspecialchars($name);
                                    $value = htmlspecialchars($value);
                                    echo '<input type="hidden" name="' . $name . '" value="' . $value . '">';
                                }
                                ?>
                                <div class="form-group">
                                    Show
                                    <select class="form-control input-sm" name="resultsize" id="resultsize">
                                        <option <?php echo $searchParams['size'] == 10 ? "selected" : ""; ?>>10</option>
                                        <option <?php echo $searchParams['size'] == 25 ? "selected" : ""; ?>>25</option>
                                        <option <?php echo $searchParams['size'] == 50 ? "selected" : ""; ?>>50</option>
                                        <option <?php echo $searchParams['size'] == 100 ? "selected" : ""; ?>>100</option>
                                        <option <?php echo $searchParams['size'] == 200 ? "selected" : ""; ?>>200</option>
                                        <option <?php echo $searchParams['size'] == 300 ? "selected" : ""; ?>>300</option>
                                        <option <?php echo $searchParams['size'] == 500 ? "selected" : ""; ?>>500</option>
                                        <option <?php echo $searchParams['size'] == 1000 ? "selected" : ""; ?>>1000</option>
                                    </select>
                                    items
                                </div>
                            </form>
                        </div>
                        <!-- end num of results -->
                        <!-- search within results -->
                        <div class="col-lg-4 text-right">
                            <div class="counter" style="display:inline-block;"></div>
                            <div class="form-group" style="display:inline-block;">
                                <input type="text" id="searchwithin" class="search form-control input-sm" placeholder="Search within results">
                            </div>
                            <span class="small text-primary" style="display:inline-block"><i class="fas fa-info-circle"></i> This page only</span>
                        </div>
                        <!-- end search within results -->
                    </div>
                    <div class="row">
                        <div class="col-lg-12 text-right">
                            <ul class="pagination" style="margin: 0;">
                                <?php
                                $limit = $searchParams['size'];
                                $i = $p * $limit - $limit;
                                parse_str($_SERVER["QUERY_STRING"], $querystring);
                                $links = 7;
                                $page = $querystring['p'];
                                $last = ceil($total / $limit);
                                $start = (($page - $links) > 0) ? $page - $links : 1;
                                $end = (($page + $links) < $last) ? $page + $links : $last;
                                $qsfp = $qslp = $qsp = $qsn = $querystring;
                                $qsfp['p'] = 1;
                                $qslp['p'] = $last;
                                if ($qsp['p'] > 1) {
                                    $qsp['p'] -= 1;
                                }
                                if ($qsn['p'] < $last) {
                                    $qsn['p'] += 1;
                                }
                                $qsfp = http_build_query($qsfp);
                                $qslp = http_build_query($qslp);
                                $qsn = http_build_query($qsn);
                                $qsp = http_build_query($qsp);
                                $firstpageurl = $_SERVER['PHP_SELF'] . "?" . $qsfp;
                                $lastpageurl = $_SERVER['PHP_SELF'] . "?" . $qslp;
                                $prevpageurl = $_SERVER['PHP_SELF'] . "?" . $qsp;
                                $nextpageurl = $_SERVER['PHP_SELF'] . "?" . $qsn;
                                ?>
                                <?php if ($start > 1) {
                                    echo '<li><a href="' . $firstpageurl . '">1</a></li>';
                                } ?>
                                <?php if ($page == 1) {
                                    echo '<li class="disabled"><a href="#">';
                                } else {
                                    echo '<li><a href="' . $prevpageurl . '">';
                                } ?>&laquo;</a></li>
                                <?php
                                for ($i = $start; $i <= $end; $i++) {
                                    $qs = $querystring;
                                    $qs['p'] = $i;
                                    $qs1 = http_build_query($qs);
                                    $url = $_SERVER['PHP_SELF'] . "?" . $qs1;
                                ?>
                                    <li<?php if ($page == $i) {
                                            echo ' class="active"';
                                        } ?>><a href="<?php echo $url; ?>"><?php echo $i; ?></a></li>
                                    <?php } ?>
                                    <?php if ($page >= $last) {
                                        echo '<li class="disabled"><a href="#">';
                                    } else {
                                        echo '<li><a href="' . $nextpageurl . '">';
                                    } ?>&raquo;</a></li>
                                    <?php if ($end < $last) {
                                        echo '<li><a href="' . $lastpageurl . '">' . $last . '</a></li>';
                                    } ?>
                                    <?php
                                    $i = $p * $limit - $limit;
                                    ?>
                            </ul>
                        </div>
                    </div>
                    <div style="padding:4px">
                        <span class="small"><i class="fas fa-sort-up" style="position:relative; top:3px; color:gray"></i> unsorted <i class="fas fa-sort-up sortarrow-asc-active" style="position:relative; top:3px"></i> sort <i class="fas fa-sort-up sortarrow2-asc-active" style="position:relative; top:3px"></i> sort2</span>
                    </div>
                    <?php $numofcol = 13; // default num of table columns 
                    $hiddencol = [];
                    ?>
                    <table class="table results table-bordered table-striped table-hover table-condensed" id="results">
                        <thead>
                            <tr>
                                <th data-resizable-column-id="#" class="text-nowrap"></th>
                                <th data-resizable-column-id="name" class="text-nowrap">Name <?php echo sortURL('name'); ?></th>
                                <?php if (getCookie('hidefield_path') != "1") { ?><th data-resizable-column-id="path" class="text-nowrap">Path <?php echo sortURL('parent_path'); ?></th>
                                <?php } else {
                                    $hiddencol[] = 'path';
                                } ?>
                                <th data-resizable-column-id="size" class="text-nowrap">Size <?php echo sortURL('size'); ?></th>
                                <?php if (getCookie('hidefield_sizedu') != "1") { ?><th data-resizable-column-id="sizedu" class="text-nowrap">Allocated <?php echo sortURL('size_du'); ?></th>
                                <?php } else {
                                    $hiddencol[] = 'sizedu';
                                } ?>
                                <?php if (getCookie('hidefield_sizep') != "1") { ?><th data-resizable-column-id="sizep"  width="7%">% <span style="color:darkgray;font-size: 11px;"><i title="Percentage of total file size this page" class="glyphicon glyphicon-question-sign"></i></span></th>
                                <?php } else {
                                    $hiddencol[] = 'sizep';
                                } ?>
                                <?php if (getCookie('hidefield_modified') != "1") { ?><th data-resizable-column-id="modified" class="text-nowrap">Date Modified <?php echo sortURL('mtime'); ?></th>
                                <?php } else {
                                    $hiddencol[] = 'modified';
                                } ?>
                                <?php if (getCookie('hidefield_accessed') != "1") { ?><th data-resizable-column-id="accessed" class="text-nowrap">Last Accessed <?php echo sortURL('atime'); ?></th>
                                <?php } else {
                                    $hiddencol[] = 'accessed';
                                } ?>
                                <?php if ($_GET['doctype'] == 'directory' || $_GET['doctype'] == '') { ?>
                                    <?php if (getCookie('hidefield_files') != "1") { ?><th data-resizable-column-id="files" class="text-nowrap">Files <?php echo sortURL('file_count'); ?></th>
                                    <?php } else {
                                        $hiddencol[] = 'files';
                                    } ?>
                                    <?php if (getCookie('hidefield_folders') != "1") { ?><th data-resizable-column-id="folders" class="text-nowrap">Folders <?php echo sortURL('dir_count'); ?></th>
                                    <?php } else {
                                        $hiddencol[] = 'folders';
                                    } ?>
                                <?php $numofcol += 2;
                                } ?>
                                <?php if (getCookie('hidefield_owner') != "1") { ?><th data-resizable-column-id="owner" class="text-nowrap">Owner <?php echo sortURL('owner'); ?></th>
                                <?php } else {
                                    $hiddencol[] = 'owner';
                                } ?>
                                <?php if (getCookie('hidefield_group') != "1") { ?><th data-resizable-column-id="group" class="text-nowrap">Group <?php echo sortURL('group'); ?></th>
                                <?php } else {
                                    $hiddencol[] = 'group';
                                } ?>
                                <?php if (getCookie('hidefield_type') != "1") { ?><th data-resizable-column-id="type" class="text-nowrap">Type <?php echo sortURL('type'); ?></th>
                                <?php } else {
                                    $hiddencol[] = 'type';
                                } ?>
                                <?php if (getCookie('hidefield_rating') != "1") { ?><th data-resizable-column-id="rating" class="text-nowrap">Rating <span style="color:darkgray;font-size: 11px;"><i title="Rating is based on last modified time, older is higher rating" class="glyphicon glyphicon-question-sign"></i></span></th>
                                <?php } else {
                                    $hiddencol[] = 'rating';
                                } ?>
                                <?php
                                if (count($config->EXTRA_FIELDS) > 0) {
                                    foreach ($config->EXTRA_FIELDS as $key => $value) { ?>
                                        <?php if (getCookie('hidefield_' . $value . '') != "1") { ?><th data-resizable-column-id="<?php echo $value ?>" class="text-nowrap"><?php echo $key ?> <?php echo sortURL($value); ?></th>
                                        <?php
                                        } else {
                                            $hiddencol[] = $value;
                                        } ?>
                                <?php $numofcol += 1;
                                    }
                                } ?>
                            </tr>
                            <tr class="info no-result">
                                <?php $numofcol -= count($hiddencol); ?>
                                <td colspan="<?php echo $numofcol; ?>"><span style="color:black;"><strong><i class="glyphicon glyphicon-info-sign"></i> No results on this page</strong></td>
                            </tr>
                        </thead>
                        <tbody id="results-tbody">
                            <?php
                            $fullpaths = array();
                            foreach ($results[$p] as $result) {
                                $file = $result['_source'];

                                // calculate rating
                                $file_rating = calcFileRating($file);

                                $i += 1;
                            ?>
                                <tr>
                                    <td>
                                        <input type="checkbox" onchange="toggleTagButton(); toggleFileActionButton(); updateSelectedList();" name="filecheck[]" class="tagcheck" value="<?php echo $result['_id'] . "," . $result['_index'] . "," . $file['parent_path'] . '/' . $file['name'] ?>" data-chkbox-shiftsel="type1">
                                    </td>
                                    <td class="path">
                                        <?php
                                        // set fullpath, parentpath and filename vars and check for root /
                                        $parentpath = $file['parent_path'];
                                        $parentpath_wildcard = escape_chars($parentpath) . '\/*';
                                        if ($parentpath === "/") {
                                            if ($file['name'] === "") { // root /
                                                $filename = '/';
                                                $fullpath = '/';
                                                $fullpath_wildcard = '\/*';
                                            } else {
                                                $filename = $file['name'];
                                                $fullpath = '/' . $filename;
                                                $fullpath_wildcard = escape_chars($fullpath) . '\/*';
                                                $parentpath_wildcard = '\/*';
                                            }
                                        } else {
                                            $fullpath = $parentpath . '/' . $file['name'];
                                            $filename = $file['name'];
                                            $fullpath_wildcard = escape_chars($fullpath) . '\/*';
                                        }
                                        $fullpaths[] = $fullpath;
                                        ?>
                                        <?php if ($file['type'] == 'directory') { ?>
                                            <a href="search.php?index=<?php echo $esIndex; ?>&amp;q=parent_path:<?php echo rawurlencode(escape_chars($fullpath)); ?>&amp;submitted=true&amp;p=1&amp;path=<?php echo rawurlencode($fullpath); ?>">
                                                <i class="fas fa-folder" style="color:#E9AC47;padding-right:3px;"></i>&nbsp;<?php echo $filename; ?></a> 
                                        <?php } else { ?>
                                            <a href="view.php?id=<?php echo $result['_id'] . '&amp;docindex=' . $result['_index'] . '&amp;doctype=' . $file['type']; ?>"><i class="fas fa-file-alt" style="color:#738291;padding-right:3px;"></i>&nbsp;<?php echo $filename; ?>
                                            <?php } ?>
                                            <?php if ($file['type'] == 'directory') { ?>
                                                <!-- directory view info button -->
                                                <div style="display:block; float:right"><a href="view.php?id=<?php echo $result['_id'] . '&amp;docindex=' . $result['_index'] . '&amp;doctype=' . $file['type']; ?>"><button class="btn btn-default btn-xs" type="button" style="color:gray;font-size:11px;margin-left:3px;"><i title="directory info" class="glyphicon glyphicon-info-sign"></i></button></a>
                                                <?php } else { ?>
                                                    <div style="display:block; float:right">
                                                    <?php } ?>
                                                    <!-- copy path button -->
                                                    <a href="#"><button onclick="copyToClipboardText('<?php echo $fullpath; ?>'); return false;" class="btn btn-default btn-xs" type="button" style="color:gray;font-size:11px;"><i title="copy path" class="glyphicon glyphicon-copy"></i></button></a>
                                                </div>
                                    </td>
                                    <?php if (!in_array('path', $hiddencol)) { ?>
                                        <td class="path">
                                            <!-- path buttons -->
                                            <div class="dropdown pathdropdown pull-right" style="display:inline-block;">
                                                <button title="more" class="btn btn-default dropdown-toggle btn-xs file-btns" type="button" data-toggle="dropdown"><i class="fas fa-ellipsis-v"></i>
                                                    <span class="caret"></span></button>
                                                <ul class="dropdown-menu">
                                                    <li class="small"><a href="#"><i class="glyphicon glyphicon-tree-conifer"></i> load path in file tree <span class="label label-info">Essential</span></a></li>
                                                    <li class="small"><a href="#"><i class="glyphicon glyphicon-th-large"></i> load path in treemap <span class="label label-info">Essential</span></a></li>
                                                    <li class="small"><a href="#"><i class="glyphicon glyphicon-fire"></i> load path in heatmap <span class="label label-info">Pro</span></a></li>
                                                    <li class="divider"></li>
                                                    <li class="small"><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=parent_path:<?php echo rawurlencode(escape_chars($parentpath)); ?>"><i class="fas fa-search"></i> search path (non-recursive)</a></li>
                                                    <li class="small"><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=parent_path:(<?php echo rawurlencode(escape_chars($parentpath)) . ' OR ' . rawurlencode($parentpath_wildcard); ?>)"><i class="fas fa-search"></i> search path (recursive)</a></li>
                                                </ul>
                                            </div>
                                            <!-- end path buttons -->
                                            <a class="pathdark" href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=parent_path:<?php echo rawurlencode(escape_chars($parentpath)); ?>&amp;path=<?php echo rawurlencode($parentpath); ?>"><?php echo $file['parent_path']; ?></a>
                                        </td>
                                    <?php } ?>
                                    <th><?php echo formatBytes($file['size']); ?>
                                    </td>
                                    <?php if (!in_array('sizedu', $hiddencol)) { ?><th> <?php echo formatBytes($file['size_du']); ?>
                                        </td><?php } ?>
                                    <?php if (!in_array('sizep', $hiddencol)) { ?><td>
                                            <?php $width = ($total_size > 0) ? $file['size'] / $total_size * 100 : 0; ?>
                                            <?php if ($width > 0) { ?>
                                                <div class="progress" style="margin:0 auto;height:8px;top:6px;position:relative">
                                                    <div title="<?php echo number_format($width, 2); ?>%" class="progress-bar progress-bar-info" style="width: <?php echo number_format($width, 2); ?>%"></div>
                                                </div>
                                            <?php } ?>
                                        </td><?php } ?>
                                    <?php if (!in_array('modified', $hiddencol)) { ?><th><?php echo utcTimeToLocal($file['mtime']); ?></td><?php } ?>
                                    <?php if (!in_array('accessed', $hiddencol)) { ?><th><?php echo utcTimeToLocal($file['atime']); ?></td><?php } ?>
                                    <?php if ($_GET['doctype'] == 'directory' || $_GET['doctype'] == '') { ?>
                                        <?php if (!in_array('files', $hiddencol)) { ?>
                                            <th>
                                                <?php if ($file['type'] == 'directory') {
                                                    echo number_format($file['file_count']); ?>
                                                    <!-- show comparison file count -->
                                                    <?php if ($esIndex2 != "") { ?>
                                                        <?php
                                                        $filecount_change = 0;
                                                        if ($file['file_count'] > 0 && $fileinfo_index2[3] > 0) {
                                                            $filecount_change = number_format(changePercent($file['file_count'], $fileinfo_index2[3]), 1);
                                                        } else if ($file['file_count'] > 0 && $fileinfo_index2[3] == 0) {
                                                            $filecount_change = 100.0;
                                                        }
                                                        if ($filecount_change != 0) { ?>
                                                            <br><small><?php echo number_format($fileinfo_index2[3]); ?>
                                                                <br><span style="color:<?php echo $filecount_change > 0 ? "red" : "#29FE2F"; ?>;">(<?php echo $filecount_change > 0 ? '<i class="fa fa-caret-up"></i> +' : '<i class="fa fa-caret-down"></i>'; ?>
                                                                    <?php echo $filecount_change; ?>%)</span></small>
                                                    <?php }
                                                    } ?>
                                                    <!-- end show comparison file count -->
                                                <?php } ?>
                                            </td>
                                        <?php } ?>
                                        <?php if (!in_array('folders', $hiddencol)) { ?>
                                            <th>
                                                <?php if ($file['type'] == 'directory') {
                                                    echo number_format($file['dir_count']); ?>
                                                    <!-- show comparison file count -->
                                                    <?php if ($esIndex2 != "") { ?>
                                                        <?php
                                                        $dircount_change = 0;
                                                        if ($file['dir_count'] > 0 && $fileinfo_index2[4] > 0) {
                                                            $dircount_change = number_format(changePercent($file['dir_count'], $fileinfo_index2[4]), 1);
                                                        } else if ($file['dir_count'] > 0 && $fileinfo_index2[4] == 0) {
                                                            $dircount_change = 100.0;
                                                        }
                                                        if ($dircount_change != 0) { ?>
                                                            <br><small><?php echo number_format($fileinfo_index2[4]); ?>
                                                                <br><span style="color:<?php echo $dircount_change > 0 ? "red" : "#29FE2F"; ?>;">(<?php echo $dircount_change > 0 ? '<i class="fa fa-caret-up"></i> +' : '<i class="fa fa-caret-down"></i>'; ?>
                                                                    <?php echo $dircount_change; ?>%)</span></small>
                                                    <?php }
                                                    } ?>
                                                    <!-- end show comparison file count -->
                                                <?php } ?>
                                            </td>
                                        <?php } ?>
                                    <?php } ?>
                                    <?php if (!in_array('owner', $hiddencol)) { ?><td><?php echo $file['owner']; ?></td><?php } ?>
                                    <?php if (!in_array('group', $hiddencol)) { ?><td><?php echo $file['group']; ?></td><?php } ?>
                                    <!-- type -->
                                    <?php if (!in_array('type', $hiddencol)) { ?>
                                        <td width="75">
                                            <span class="text-primary"><?php echo ucfirst($file['type']) ?></span>
                                        </td>
                                    <?php } ?>
                                    <!-- end type -->
                                    <?php if (!in_array('rating', $hiddencol)) { ?><td class="rating"><i class="fas fa-eraser" style="color:palevioletred; opacity:<?php echo $file_rating; ?>"></i></td><?php } ?>
                                    <!-- extra fields -->
                                    <?php
                                    if (count($config->EXTRA_FIELDS) > 0) {
                                        foreach ($config->EXTRA_FIELDS as $key => $value) {
                                            if (!in_array($value, $hiddencol)) { ?>
                                                <td>
                                                    <?php if (is_array($file[$value])) {
                                                        $ef_string = "";
                                                        foreach ($file[$value] as $k => $v) {
                                                            if (is_array($v)) {
                                                                foreach ($v as $v_key => $v_val) {
                                                                    if (is_array($v_val)) {
                                                                        foreach ($v_val as $v2_key => $v2_val) {
                                                                            if (is_bool($v2_val)) {
                                                                                $v2_val = ($v2_val) ? 'true' : 'false';
                                                                            }
                                                                            $ef_string .= $value . '.' . $k . '.' . $v2_key . ': ' . $v2_val . ', ';
                                                                        }
                                                                    } else {
                                                                        if (is_bool($v_val)) {
                                                                            $v_val = ($v_val) ? 'true' : 'false';
                                                                        }
                                                                        $ef_string .= $value . '.' . $k . '.' . $v_key . ': ' . $v_val . ', ';
                                                                    }
                                                                }
                                                            } else {
                                                                if (is_bool($v)) {
                                                                    $v = ($v) ? 'true' : 'false';
                                                                }
                                                                $ef_string .= $value . '.' . $k . ': ' . $v . ', ';
                                                            }
                                                        }
                                                        echo (strlen($ef_string) > 100) ? substr($ef_string, 0, 100) . ' ...' : $ef_string;
                                                    } elseif ($value == 'ctime') {  # ctime field
                                                        echo utcTimeToLocal($file[$value]);
                                                    } elseif (is_bool($file[$value])) {  # bool field
                                                        echo $file[$value] ? 'true' : 'false';
                                                    } else {
                                                        echo (strlen($file[$value]) > 100) ? substr($file[$value], 0, 100) . ' ...' : $file[$value];
                                                    } ?>
                                                </td>
                                    <?php }
                                        }
                                    } ?>
                                    <!-- end extra fields -->
                                </tr>
                            <?php
                            } // END foreach loop over results
                            ?>
                        </tbody>
                        <tfoot>
                            <tr>
                                <th></th>
                                <th>Name <?php echo sortURL('name'); ?></th>
                                <?php if (getCookie('hidefield_path') != "1") { ?><th class="text-nowrap">Path <?php echo sortURL('parent_path'); ?></th>
                                <?php } ?>
                                <th>Size <?php echo sortURL('size'); ?></th>
                                <?php if (getCookie('hidefield_sizedu') != "1") { ?><th class="text-nowrap">Allocated <?php echo sortURL('size_du'); ?></th>
                                <?php } ?>
                                <?php if (getCookie('hidefield_sizep') != "1") { ?><th class="text-nowrap" width="7%">% <span style="color:darkgray;font-size: 11px;"><i title="Percentage of total file size this page" class="glyphicon glyphicon-question-sign"></i></span></th>
                                <?php } ?>
                                <?php if (getCookie('hidefield_modified') != "1") { ?><th class="text-nowrap">Date Modified <?php echo sortURL('mtime'); ?></th>
                                <?php } ?>
                                <?php if (getCookie('hidefield_accessed') != "1") { ?><th class="text-nowrap">Last Accessed <?php echo sortURL('atime'); ?></th>
                                <?php } ?>
                                <?php if ($_GET['doctype'] == 'directory' || $_GET['doctype'] == '') { ?>
                                    <?php if (getCookie('hidefield_files') != "1") { ?><th class="text-nowrap">Files <?php echo sortURL('file_count'); ?></th>
                                    <?php } ?>
                                    <?php if (getCookie('hidefield_folders') != "1") { ?><th class="text-nowrap">Folders <?php echo sortURL('dir_count'); ?></th>
                                    <?php } ?>
                                <?php
                                } ?>
                                <?php if (getCookie('hidefield_owner') != "1") { ?><th class="text-nowrap">Owner <?php echo sortURL('owner'); ?></th>
                                <?php } ?>
                                <?php if (getCookie('hidefield_group') != "1") { ?><th class="text-nowrap">Group <?php echo sortURL('group'); ?></th>
                                <?php } ?>
                                <?php if (getCookie('hidefield_type') != "1") { ?><th class="text-nowrap">Type <?php echo sortURL('type'); ?></th>
                                <?php } ?>
                                <?php if (getCookie('hidefield_rating') != "1") { ?><th class="text-nowrap">Rating <span style="color:darkgray;font-size: 11px;"><i title="Rating is based on last modified time, older is higher rating" class="glyphicon glyphicon-question-sign"></i></span></th>
                                <?php } ?>
                                <?php
                                if (count($config->EXTRA_FIELDS) > 0) {
                                    foreach ($config->EXTRA_FIELDS as $key => $value) { ?>
                                        <?php if (getCookie('hidefield_' . $value . '') != "1") { ?><th class="text-nowrap"><?php echo $key ?> <?php echo sortURL($value); ?></th>
                                        <?php } ?>
                                <?php
                                    }
                                } ?>
                            </tr>
                        </tfoot>
                    </table>
                    <div class="text-right">
                        <button onclick="$('html, body').animate({ scrollTop: 0 }, 'fast');" type="button" class="btn btn-default" title="go to top"><i class="glyphicon glyphicon-triangle-top"></i> To top</button>
                    </div>
                    <div class="text-right" style="margin-top:10px">
                        <ul class="pagination" style="margin: 0;">
                            <?php
                            parse_str($_SERVER["QUERY_STRING"], $querystring);
                            $links = 7;
                            $page = $querystring['p'];
                            $last = ceil($total / $limit);
                            $start = (($page - $links) > 0) ? $page - $links : 1;
                            $end = (($page + $links) < $last) ? $page + $links : $last;
                            $qsfp = $qslp = $qsp = $qsn = $querystring;
                            $qsfp['p'] = 1;
                            $qslp['p'] = $last;
                            if ($qsp['p'] > 1) {
                                $qsp['p'] -= 1;
                            }
                            if ($qsn['p'] < $last) {
                                $qsn['p'] += 1;
                            }
                            $qsfp = http_build_query($qsfp);
                            $qslp = http_build_query($qslp);
                            $qsn = http_build_query($qsn);
                            $qsp = http_build_query($qsp);
                            $firstpageurl = $_SERVER['PHP_SELF'] . "?" . $qsfp;
                            $lastpageurl = $_SERVER['PHP_SELF'] . "?" . $qslp;
                            $prevpageurl = $_SERVER['PHP_SELF'] . "?" . $qsp;
                            $nextpageurl = $_SERVER['PHP_SELF'] . "?" . $qsn;
                            ?>
                            <?php if ($start > 1) {
                                echo '<li><a href="' . $firstpageurl . '">1</a></li>';
                            } ?>
                            <?php if ($page == 1) {
                                echo '<li class="disabled"><a href="#">';
                            } else {
                                echo '<li><a href="' . $prevpageurl . '">';
                            } ?>&laquo;</a></li>
                            <?php
                            for ($i = $start; $i <= $end; $i++) {
                                $qs = $querystring;
                                $qs['p'] = $i;
                                $qs1 = http_build_query($qs);
                                $url = $_SERVER['PHP_SELF'] . "?" . $qs1;
                            ?>
                                <li<?php if ($page == $i) {
                                        echo ' class="active"';
                                    } ?>><a href="<?php echo $url; ?>"><?php echo $i; ?></a></li>
                                <?php } ?>
                                <?php if ($page >= $last) {
                                    echo '<li class="disabled"><a href="#">';
                                } else {
                                    echo '<li><a href="' . $nextpageurl . '">';
                                } ?>&raquo;</a></li>
                                <?php if ($end < $last) {
                                    echo '<li><a href="' . $lastpageurl . '">' . $last . '</a></li>';
                                } ?>
                        </ul>
                    </div>
                <?php } else { ?>
                    <div class="container-fluid" style="margin:10px; padding:10px">
                        <div class="row">
                            <div class="alert alert-dismissible alert-info col-xs-8">
                                <button type="button" class="close" data-dismiss="alert">&times;</button>
                                <i class="glyphicon glyphicon-exclamation-sign"></i> <strong>Sorry, no items found.</strong><br>Change a few things up and try searching again or search for <a class="alert-link" href="search.php?index=<?php echo $esIndex ?>&submitted=true&p=1&q=&path=">anything.</a><br>
                                See <a class="alert-link" href="help.php">help</a> for search examples or try to <a class="alert-link" href="#" onclick="saveSearchFilters('clearall')">remove any search filters</a> or <a class="alert-link" href="#" onclick="resetSort()">reset sort order</a>. <a class="alert-link" href="#" onclick="window.history.back(); return false;">Go back</a><br>
                            </div>
                        </div>
                        <div class="row">
                            <div class="panel panel-default">
                                <div class="panel-body">
                                    <span>Search query: <strong><em><?php echo $searchParams['body']['query']['query_string']['query'] ?></em></strong></span>
                                </div>
                            </div>
                        </div>
                    </div>
                <?php } ?>
                <hr>
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
            </div>
    </div>
</div>