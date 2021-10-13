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
        <div class="row">
            <div class="col-lg-12">
                <?php if (Constants::LOGIN_REQUIRED) : ?>
                <div class="well">
                  <h4>Profile</h4>
                  <p><i class="glyphicon glyphicon-user"></i> Username: <?php echo $_SESSION['username']; ?></p>
                  <p><i class="glyphicon glyphicon-lock"></i> Password: <a href="/password.php">Change Password</a></p>
                </div>
                <?php endif; ?>
                <div class="well">
                    <h4>New index notification</h4>
                    <input type="checkbox" name="notifynewindex" id="notifynewindex" onclick="setNotifyNewIndex()" <?php echo (getCookie('notifynewindex') == 1) ? 'checked' : ''; ?>> <label for="notifynewindex" class="control-label">Notify when newer index</label>
                    <p class="small"><i class="glyphicon glyphicon-info-sign"></i> As new indices get added, display a notification.</p>
                </div>
                <div class="well">
                    <h4>Time display</h4>
                    <div class="form-check">
                        <input type="checkbox" class="form-check-input" id="timedisplay" onclick="setTimeDisplay()" <?php echo (getCookie('localtime') == 1) ? 'checked' : ''; ?>>
                        <label class="form-check-label" for="timedisplay">Show times in local timezone</label><br>
                        <span class="small"><i class="glyphicon glyphicon-info-sign"></i> Default is to show all times in UTC (times stored in index).</span>
                    </div>
                </div>
                <div class="well">
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
                        <label class="form-check-label" for="sizedu">Use size_du (allocated size) instead of size for charts and file tree sizes</label>
                    </div>
                </div>
                </div><div class="well">
                    <h4>Use predictive search</h4>
                    <div class="form-check">
                        <input type="checkbox" class="form-check-input" id="wildcardsearch" onclick="setWildcardSearch()">
                        <label class="form-check-label" for="wildcardsearch">Enable predictive search</label><br>
                        <span class="small"><i class="glyphicon glyphicon-info-sign"></i> Uses wildcard * when searching to find search characters in file names, paths, etc.</span>
                    </div>
                </div>
                <div class="well">
                    <h4>Default search sort</h4>
                    <div class="form-check">
                        <input type="checkbox" class="form-check-input" id="sortdisplay" onclick="setSortDisplay()">
                        <label class="form-check-label" for="sortdisplay">Show unsorted search results (default is by parent_path and name)</label><br>
                        <span class="small"><i class="glyphicon glyphicon-info-sign"></i> When no sort/sort2 is set on search results table.</span>
                    </div>
                </div>
                <div class="well">
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
                        foreach (Constants::EXTRA_FIELDS as $k => $v) {
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
                <div class="well">
                    <h4>Clear diskover cache</h4>
                    <button type="submit" class="btn btn-warning" onclick=clearChartCache()>Clear</button>
                </div>
                <div class="well">
                    <h4>Clear diskover cookies</h4>
                    <button type="submit" class="btn btn-warning" onclick=clearCookies()>Clear</button>
                </div>
                <div class="well">
                    <h4>Version</h4>
                    Version: <?php echo "diskover-web v" . $VERSION; ?><br>
                    Check for <a href="https://github.com/diskoverdata/diskover-community/releases/" target="_blank">newer version</a> on GitHub <i class="fab fa-github-alt"></i>
                </div>
                <div class="well">
                    <h4>Elasticsearch Info</h4>
                    Connected to: <?php echo Constants::ES_HOST . ":" . Constants::ES_PORT ?><br />
                    Response time: <?php echo $es_responsetime ?><br />
                </div>
                <div class="well">
                    <h4>Send anonymous usage data</h4>
                    <input type="checkbox" name="sendanondata" id="sendanondata" onclick="setSendAnonData()" <?php echo (getCookie('sendanondata') == 1) ? 'checked' : ''; ?>> <label for="sendanondata" class="control-label">Send anonymous data</label>
                    <p class="small"><i class="glyphicon glyphicon-info-sign"></i>Send anonymous usage data to Diskover Data to help improve diskover. No personal information is sent.</p>
                </div>
            </div>
        </div>
    </div>

    <script language="javascript" src="js/jquery.min.js"></script>
    <script language="javascript" src="js/bootstrap.min.js"></script>
    <script language="javascript" src="js/store.legacy.min.js"></script>
    <script language="javascript" src="js/diskover.js"></script>
    <script>
        // set file size display checkbox
        if (getCookie('filesizebase10') == 1) {
            document.getElementById('sizedisplay').checked = true;
        } else {
            document.getElementById('sizedisplay').checked = false;
        }
        // set size field checkbox
        if (getCookie('sizefield') == 'size_du') {
            document.getElementById('sizedu').checked = true;
        } else {
            document.getElementById('sizedu').checked = false;
        }
        /* set time display for local timezone or utc (default)
        set time display checkbox */
        if (getCookie('localtime') == 1) {
            document.getElementById('timedisplay').checked = true;
        } else {
            document.getElementById('timedisplay').checked = false;
        }
        // set unsorted checkbox
        if (getCookie('unsorted') == 1) {
            document.getElementById('sortdisplay').checked = true;
        } else {
            document.getElementById('sortdisplay').checked = false;
        }
        // set predictive wildcard search checkbox
        if (getCookie('wildcardsearch') == 1) {
            document.getElementById('wildcardsearch').checked = true;
        } else {
            document.getElementById('wildcardsearch').checked = false;
        }
    </script>
</body>

</html>
