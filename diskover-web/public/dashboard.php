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
require "d3_inc.php";

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

    <div class="container-fluid" id="loading_spinner" style="margin-top:70px; text-align:center;"><span style="margin-right:10px"><img width="32" height="32" src="images/ajax-loader.gif" /></span> Loading Dashboard</div>
    <div class="container-fluid" id="mainwindow" style="margin-top:70px"></div>
    <div class="container-fluid">
        <div class="row">
            <div class="col-lg-6"><a href="#" class="btn btn-sm btn-default reload-results" title="Reload chart data"><i class="glyphicon glyphicon-refresh"></i> Reload</a></div>
        </div>
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