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
require "../src/diskover/Auth.php";
require "../src/diskover/Diskover.php";
require "settings_helptext.php";

// get ES cluster stats
try
{
    $es_clusterstats = $client->cluster()->stats();
}
catch (Throwable $e)
{
}

use diskover\ConfigDatabase;
// Load database and get diskover config settings.
$db = new ConfigDatabase();
$db->connect();
$config_diskover = (object) $db->getConfigSettings('configdiskover');
$config_all = (object) $db->getAllConfigSettings();

?>

<!DOCTYPE html>
<html lang="en">

<head>
    <!-- Global site tag (gtag.js) - Google Analytics -->
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-DYSE689C04"></script>
    <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){dataLayer.push(arguments);}
    gtag('js', new Date());

    gtag('config', 'G-DYSE689C04');
    </script>
    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge" />
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>diskover &mdash; Settings</title>
    <link rel="stylesheet" href="css/fontawesome-free/css/all.min.css" media="screen" />
    <link rel="stylesheet" href="css/bootswatch.min.css" media="screen" />
    <link rel="stylesheet" href="css/diskover.css" media="screen" />
    <link rel="icon" type="image/png" href="images/diskoverfavico.png" />
    <style>
        pre {
            background-color: #202225 !important;
            color: #56B6C2 !important;
            border: 1px solid #000;
        }
    </style>
</head>

<body>
    <?php include "nav.php"; ?>

    <div class="container" id="mainwindow" style="margin-top:70px;">
        <h1 class="page-header"><i class="fas fa-user-cog"></i> Settings</h1>
        <ul class="nav nav-tabs">
            <li class="active"><a href="#webuser" data-toggle="tab">Web - User</a></li>
            <li><a href="#webother" data-toggle="tab">Web - Other</a></li>
            <li><a href="#diskover" data-toggle="tab">Diskover Scan</a></li>
            <li><a href="#elasticsearch" data-toggle="tab">Elasticsearch</a></li>
            <li><a href="#version" data-toggle="tab">Version</a></li>
        </ul>
        <div id="settingsTabContent" class="tab-content">
            <div class="tab-pane fade active in" id="webuser">
                <div class="row">
                    <div class="col-lg-12">
                        <div class="well">
                        <h4>Web - User Settings</h4>
                        <?php if ($config->LOGIN_REQUIRED) : ?>
                        <div class="well-sm">
                        <h4>Profile</h4>
                        <p><i class="glyphicon glyphicon-user"></i> Username: <?php echo $_SESSION['username']; ?></p>
                        <p><i class="glyphicon glyphicon-lock"></i> Password: <a href="password.php">Change Password</a></p>
                        </div>
                        <?php endif; ?>
                        <div class="well-sm">
                            <h4>New index notification</h4>
                            <input type="checkbox" name="notifynewindex" id="notifynewindex" onclick="setNotifyNewIndex()" <?php echo (getCookie('notifynewindex') == 1) ? 'checked' : ''; ?>> <label for="notifynewindex" class="control-label">Notify when newer index</label>
                            <p class="small"><i class="glyphicon glyphicon-info-sign"></i> As new indices get added, display a notification.</p>
                        </div>
                        <div class="well-sm">
                            <h4>Time display</h4>
                            <div class="form-check">
                                <input type="checkbox" class="form-check-input" id="timedisplay" onclick="setTimeDisplay()" <?php echo (getCookie('localtime') == 1) ? 'checked' : ''; ?>>
                                <label class="form-check-label" for="timedisplay">Show times in local timezone</label><br>
                                <span class="small"><i class="glyphicon glyphicon-info-sign"></i> Default is to show all times in UTC (times stored in index).</span>
                            </div>
                        </div>
                        <div class="well-sm">
                            <h4>File size display</h4>
                            <div class="form-check">
                                <input type="checkbox" class="form-check-input" id="sizedisplay" onclick="setFileSizeDisplay()">
                                <label class="form-check-label" for="sizedisplay">Use decimal system base-10 (1000) instead of binary system base-2 (1024)</label>
                            </div>
                            <div class="form-group form-inline">
                                <label>File size decimals</label>&nbsp;<input class="form-control input" style="background-color:#1C1E21;color:darkgray;" name="filesizedec" id="filesizedec" value="<?php if (getCookie('filesizedec') != '') {
                                                                                                                                                                                                            echo getCookie('filesizedec');
                                                                                                                                                                                                        } else {
                                                                                                                                                                                                            echo '1';
                                                                                                                                                                                                        } ?>" size="1">&nbsp;<button type="submit" id="changefilesizedecbutton" class="btn btn-primary" title="submit" onclick="setFileSizeDisplayDec()">Set </button>
                                <div class="form-check">
                                    <input type="checkbox" class="form-check-input" id="sizedu" onclick="setSizeField()">
                                    <label class="form-check-label" for="sizedu">Use size_du (allocated size) instead of size for charts and file tree sizes</label><br>
                                    <span class="small"><i class="glyphicon glyphicon-info-sign"></i> If the file systems being indexed contain hardlinks, check this to show allocated sizes.</span>
                                </div>
                            </div>
                        </div>
                        <div class="well-sm">
                            <h4>Search file tree</h4>
                            <div class="form-check">
                                <input type="checkbox" class="form-check-input" id="searchfiletreesort" onclick="setSearchFileTreeSort()">
                                <label class="form-check-label" for="searchfiletreesort">Sort search file tree by size instead of alphanumerically</label><br>
                                <span class="small"><i class="glyphicon glyphicon-info-sign"></i> Changing this setting may require reloading file tree data by clicking the Reload button.</span>
                                
                            </div>
                        </div>
                        <div class="well-sm">
                            <h4>Filter charts</h4>
                            <div class="form-check">
                                <input type="checkbox" class="form-check-input" id="filterchart" onclick="setFilterCharts()">
                                <label class="form-check-label" for="filterchart">Use filters on charts</label><br>
                                <span class="small"><i class="glyphicon glyphicon-info-sign"></i> Apply any filters to search results and dashboard charts. Changing this setting may require reloading file tree data by clicking the Reload button.</span>
                            </div>
                        </div>
                        <div class="well-sm">
                            <h4>Use predictive search</h4>
                            <div class="form-check">
                                <input type="checkbox" class="form-check-input" id="wildcardsearch" onclick="setWildcardSearch()">
                                <label class="form-check-label" for="wildcardsearch">Enable predictive search</label><br>
                                <span class="small"><i class="glyphicon glyphicon-info-sign"></i> Uses wildcard * when searching to find search characters in file names, paths, etc.</span>
                            </div>
                        </div>
                        <div class="well-sm">
                            <h4>Default search sort</h4>
                            <div class="form-check">
                                <input type="checkbox" class="form-check-input" id="sortdisplay" onclick="setSortDisplay()">
                                <label class="form-check-label" for="sortdisplay">Show unsorted search results (default is by parent_path and name)</label><br>
                                <span class="small"><i class="glyphicon glyphicon-info-sign"></i> When no sort/sort2 is set on search results table.</span>
                            </div>
                        </div>
                        <div class="well-sm">
                            <div class="form-group form-check">
                                <h4>Hide fields in search results</h4>
                                <input type="checkbox" class="form-check-input" id="hidefield_path" onclick="setHideFields('path');" <?php echo getCookie('hidefield_path') == "1" ? "checked" : ""; ?>>
                                <label class="form-check-label" for="hidefield_path">Path</label>
                                <input type="checkbox" class="form-check-input" id="hidefield_sizedu" onclick="setHideFields('sizedu');" <?php echo getCookie('hidefield_sizedu') == "1" ? "checked" : ""; ?>>
                                <label class="form-check-label" for="hidefield_sizedu">Allocated</label>
                                <input type="checkbox" class="form-check-input" id="hidefield_sizep" onclick="setHideFields('sizep');" <?php echo getCookie('hidefield_sizep') == "1" ? "checked" : ""; ?>>
                                <label class="form-check-label" for="hidefield_sizep">Size %</label>
                                <input type="checkbox" class="form-check-input" id="hidefield_modified" onclick="setHideFields('modified');" <?php echo getCookie('hidefield_modified') == "1" ? "checked" : ""; ?>>
                                <label class="form-check-label" for="hidefield_modified">Date Modified</label>
                                <input type="checkbox" class="form-check-input" id="hidefield_accessed" onclick="setHideFields('accessed');" <?php echo getCookie('hidefield_accessed') == "1" ? "checked" : ""; ?>>
                                <label class="form-check-label" for="hidefield_accessed">Last Accessed</label>
                                <input type="checkbox" class="form-check-input" id="hidefield_files" onclick="setHideFields('files');" <?php echo getCookie('hidefield_files') == "1" ? "checked" : ""; ?>>
                                <label class="form-check-label" for="hidefield_files">Files</label>
                                <input type="checkbox" class="form-check-input" id="hidefield_folders" onclick="setHideFields('folders');" <?php echo getCookie('hidefield_folders') == "1" ? "checked" : ""; ?>>
                                <label class="form-check-label" for="hidefield_folders">Folders</label>
                                <input type="checkbox" class="form-check-input" id="hidefield_owner" onclick="setHideFields('owner');" <?php echo getCookie('hidefield_owner') == "1" ? "checked" : ""; ?>>
                                <label class="form-check-label" for="hidefield_owner">Owner</label>
                                <input type="checkbox" class="form-check-input" id="hidefield_group" onclick="setHideFields('group');" <?php echo getCookie('hidefield_group') == "1" ? "checked" : ""; ?>>
                                <label class="form-check-label" for="hidefield_group">Group</label>
                                <input type="checkbox" class="form-check-input" id="hidefield_type" onclick="setHideFields('type');" <?php echo getCookie('hidefield_type') == "1" ? "checked" : ""; ?>>
                                <label class="form-check-label" for="hidefield_type">Type</label>
                                <input type="checkbox" class="form-check-input" id="hidefield_rating" onclick="setHideFields('rating');" <?php echo getCookie('hidefield_rating') == "1" ? "checked" : ""; ?>>
                                <label class="form-check-label" for="hidefield_rating">Rating</label>
                                <?php
                                foreach ($config->EXTRA_FIELDS as $k => $v) {
                                    $ef_hf = "hidefield_" . $v;
                                ?>
                                    <input type="checkbox" class="form-check-input" id="<?php echo $ef_hf ?>" onclick="setHideFields('<?php echo $v ?>')" <?php echo getCookie('' . $ef_hf . '') == "1" ? "checked" : ""; ?>>
                                    <label class="form-check-label" for="<?php echo $ef_hf ?>"><?php echo $k ?></label>
                                <?php } ?>
                                <br />
                                <span class="small"><i class="glyphicon glyphicon-info-sign"></i> Search results table columns. Not hidden on file/dir info page.</span>
                                <br><br>
                                <h4>Reset search results column sizes</h4>
                                <button type="submit" class="btn btn-primary" onclick=resetResultsTable()>Reset</button>
                            </div>
                        </div>
                        <div class="well-sm">
                            <h4>Clear diskover cache</h4>
                            <button type="submit" class="btn btn-warning" onclick=clearChartCache()>Clear</button>
                        </div>
                        <div class="well-sm">
                            <h4>Clear diskover cookies</h4>
                            <button type="submit" class="btn btn-warning" onclick=clearCookies()>Clear</button>
                        </div>
                    </div>
                </div>
                </div>
            </div>
            <div class="tab-pane fade" id="webother">
                <div class="row">
                    <div class="col-lg-12">
                        <div class="well">
                        <h4>Web - Other Settings</h4>
                        <form name="webotherform" id="webotherform">
                        <input type="hidden" name="formname" value="webotherform">
                        <?php
                        foreach ($config as $key => $value) {
                            // hide ES_, USER, PASS, DATABASE settings
                            if (preg_match("/^ES_|USER|PASS|DATABASE/", $key)) {
                                continue;
                            }
                            if (is_bool($value)) {
                                $value = json_encode($value);
                            }
                            if ($key === "PASS") {
                                $inputtype = 'type="password"';
                            } else {
                                $inputtype = '';
                            }
                            if ($key === 'FILE_TYPES') {
                                echo '<div class="well-sm">';
                                echo '<div class="form-group form-inline" id="' . $key . '-group">';
                                echo '<label>' . $key . '</label><br>';
                                foreach ($value as $k => $v) {
                                echo '<input class="form-control input" style="background-color:#1C1E21;color:darkgray;width:20%;" name="FILE_TYPES[]" id="file_types_' . $k . '_label" value="' . $k . '">
                                        <input class="form-control input" style="background-color:#1C1E21;color:darkgray;width:75%;" name="FILE_TYPES[]" id="file_types_' . $k . '_extensions" value="' . implode(', ', $v) . '">';
                                }
                                echo '<input class="form-control input" style="background-color:#1C1E21;color:darkgray;width:20%;" name="FILE_TYPES[]" value="" placeholder="Type label">
                                        <input class="form-control input" style="background-color:#1C1E21;color:darkgray;width:75%;" name="FILE_TYPES[]" value="" placeholder="File extensions"><br>';
                                if (array_key_exists($key, $helptext) && !empty($helptext[$key])) {
                                    echo '<span class="small"><i class="glyphicon glyphicon-info-sign"></i> ' . $helptext[$key] . '</span>';
                                }
                                echo '</div>';
                                echo "</div>";
                            } elseif ($key === 'EXTRA_FIELDS') {
                                    echo '<div class="well-sm">';
                                    echo '<div class="form-group form-inline" id="' . $key . '-group">';
                                    echo '<label>' . $key . '</label><br>';
                                    foreach ($value as $k => $v) {
                                    echo '<input class="form-control input" style="background-color:#1C1E21;color:darkgray;width:20%;" name="EXTRA_FIELDS[]" id="extra_fields_' . $k . '_label" value="' . $k . '">
                                            <input class="form-control input" style="background-color:#1C1E21;color:darkgray;width:75%;" name="EXTRA_FIELDS[]" id="extra_fields_' . $k . '_fieldname" value="' . $v . '">';
                                    }
                                    echo '<input class="form-control input" style="background-color:#1C1E21;color:darkgray;width:20%;" name="EXTRA_FIELDS[]" value="" placeholder="Field label">
                                            <input class="form-control input" style="background-color:#1C1E21;color:darkgray;width:75%;" name="EXTRA_FIELDS[]" value="" placeholder="ES field name"><br>';
                                    if (array_key_exists($key, $helptext) && !empty($helptext[$key])) {
                                        echo '<span class="small"><i class="glyphicon glyphicon-info-sign"></i> ' . $helptext[$key] . '</span>';
                                    }
                                    echo '</div>';
                                    echo "</div>";
                            } else {
                                echo '<div class="well-sm">';
                                echo '<div class="form-group form-inline" id="' . $key . '-group">
                                        <label style="width:250px;">' . $key . '</label>&nbsp;
                                        <input class="form-control input" style="background-color:#1C1E21;color:darkgray;width:650px;" name="' . $key . '" id="' . $key . '" value="' . $value . '" ' . $inputtype . '><br>';
                                if (array_key_exists($key, $helptext) && !empty($helptext[$key])) {
                                    echo '<span class="small"><i class="glyphicon glyphicon-info-sign"></i> ' . $helptext[$key] . '</span>';
                                }
                                echo "</div>";
                                echo "</div>";
                            }
                        }
                        ?>
                        <button type="submit" class="btn btn-primary" title="Save settings">Save</button><br>
                        <br>
                        </form>
                    </div>
                    </div>
                </div>
            </div>
            <div class="tab-pane fade" id="diskover">
                <div class="row">
                    <div class="col-lg-12">
                    <div class="well">
                        <h4>Diskover Scan Settings</h4>
                        <form name="diskoverform" id="diskoverform">
                        <input type="hidden" name="formname" value="diskoverform">
                        <?php
                        foreach ($config_diskover as $key => $value) {
                            // hide ES_ and DATABASE settings
                            if (preg_match("/^ES_|DATABASE/", $key)) {
                                continue;
                            }
                            if (is_bool($value)) {
                                $value = json_encode($value);
                            }
                            $value = (is_array($value)) ? implode(', ', $value) : $value;
                            echo '<div class="well-sm">';
                            echo '<div class="form-group form-inline" id="' . $key . '-group">
                                    <label style="width:250px;">' . $key . '</label>&nbsp;
                                    <input class="form-control input" style="background-color:#1C1E21;color:darkgray;width:650px;" name="' . $key . '" id="' . $key . '" value="' . $value . '" ' . $inputtype . '><br>';
                            if (array_key_exists($key, $helptext) && !empty($helptext[$key])) {
                                echo '<span class="small"><i class="glyphicon glyphicon-info-sign"></i> ' . $helptext[$key] . '</span>';
                            }
                            echo "</div>";
                            echo "</div>";
                        }
                        ?>
                        <button type="submit" class="btn btn-primary" title="Save settings">Save</button><br>
                        <br>
                        </form>
                    </div>
                </div>
                </div>
            </div>
            <div class="tab-pane fade" id="elasticsearch">
                <div class="row">
                    <div class="col-lg-12">
                    <div class="well">
                        <h4>Elasticsearch Info</h4>
                        Elasticsearch host: <?php echo $config->ES_HOST . ":" . $config->ES_PORT ?><br />
                        Response time: <?php echo $_SESSION['es_responsetime'] ?><br />
                        Connected to ES: <?php echo (isset($es_clusterstats)) ? '<span style="color:green">Yes</span>' : '<span style="color:red">No</span>'; ?><br />
                        <?php if (isset($es_clusterstats)) { ?>
                        <br />
                        Nodes Total: <?php echo $es_clusterstats['_nodes']['total'] ?><br />
                        Cluster Name: <?php echo $es_clusterstats['cluster_name'] ?><br />
                        Cluster UUID: <?php echo $es_clusterstats['cluster_uuid'] ?><br />
                        Status: <?php echo '<span style="color:'.$es_clusterstats['status'].'">'.$es_clusterstats['status'].'</span>' ?><br />
                        Indices Count: <?php echo $es_clusterstats['indices']['count'] ?><br />
                        Indices Shards Total: <?php echo $es_clusterstats['indices']['shards']['total'] ?><br />
                        Indices Shards Primaries: <?php echo $es_clusterstats['indices']['shards']['primaries'] ?><br />
                        Indices Shards Replication: <?php echo $es_clusterstats['indices']['shards']['replication'] ?><br />
                        Docs Count: <?php echo $es_clusterstats['indices']['docs']['count'] ?><br />
                        Storage Size Used: <?php echo formatBytes($es_clusterstats['indices']['store']['size_in_bytes']) ?><br />
                        Version: <?php echo $es_clusterstats['indices']['versions'][0]['version'] ?><br />
                        <?php } ?>
                    </div>
                    <div class="well">
                        <h4>Elasticsearch Settings</h4>
                        <form name="elasticsearchform" id="elasticsearchform">
                        <input type="hidden" name="formname" value="elasticsearchform">
                        <?php
                        foreach ($config_all as $key => $value) {
                            // hide non ES_ config settings
                            if (!preg_match("/^ES_/", $key)) continue;
                            if (is_bool($value)) {
                                $value = json_encode($value);
                            }
                            if ($key === "ES_PASS") {
                                $inputtype = 'type="password"';
                            } else {
                                $inputtype = '';
                            }
                            echo '<div class="well-sm">';
                            echo '<div class="form-group form-inline" id="' . $key . '-group">
                                    <label style="width:250px;">' . $key . '</label>&nbsp;
                                    <input class="form-control input" style="background-color:#1C1E21;color:darkgray;width:650px;" name="' . $key . '" id="' . $key . '" value="' . $value . '" ' . $inputtype . '><br>';
                            if (array_key_exists($key, $helptext) && !empty($helptext[$key])) {
                                echo '<span class="small"><i class="glyphicon glyphicon-info-sign"></i> ' . $helptext[$key] . '</span>';
                            }
                            echo "</div>";
                            echo "</div>";
                        }
                        ?>
                        <button type="submit" class="btn btn-primary" title="Save settings">Save</button><br>
                        <br>
                        </form>
                        <form name="elasticsearchtestform" id="elasticsearchtestform">
                        <input type="hidden" name="formname" value="elasticsearchtestform">
                        <button type="submit" class="btn btn-default" title="Test connection">Test</button><br>
                        <br>
                        </form>
                    </div>
                    </div>
                </div>
            </div>
            <div class="tab-pane fade" id="version">
                <div class="row">
                    <div class="col-lg-12">
                        <div class="well">
                            <h4>Version</h4>
                            Version: <?php echo "diskover-web v" . $VERSION; ?><br>
                            Check for <a href="https://github.com/diskoverdata/diskover-community/releases/" target="_blank">newer version</a> on GitHub <i class="fab fa-github-alt"></i>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script language="javascript" src="js/jquery.min.js"></script>
    <script language="javascript" src="js/bootstrap.min.js"></script>
    <script language="javascript" src="js/store.legacy.min.js"></script>
    <script language="javascript" src="js/diskover.js"></script>
    <script language="javascript" src="js/settings.js"></script>
</body>

</html>
