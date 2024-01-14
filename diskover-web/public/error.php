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
require '../src/diskover/config_inc.php';

if (isset($_COOKIE['error'])) {
    $error = $_COOKIE['error'];
} else {
    $error = 'An unknown error has occurred.';
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
    <title>diskover &mdash; Error</title>
    <link rel="stylesheet" href="css/fontawesome-free/css/all.min.css" media="screen" />
    <link rel="stylesheet" href="css/bootswatch.min.css" media="screen" />
    <link rel="stylesheet" href="css/diskover.css" media="screen" />
    <link rel="icon" type="image/png" href="images/diskoverfavico.png" />
    <style>
        .error-logo {
            text-align: center;
            padding: 40px 0 0 0;
        }

        .error {
            width: 500px;
            background-color: #2F3338;
            box-shadow: 0 0 9px 0 rgba(0, 0, 0, 0.3);
            margin: 100px auto;
        }

        .error h1 {
            text-align: center;
            color: #ffffff;
            font-size: 24px;
            padding: 0 0 20px 0;
            border-bottom: 1px solid #000000;
        }

        .error p {
            text-align: center;
            font-size: 14px;
            padding: 10px;
            overflow-wrap: break-word;
        }
    </style>
</head>

<body>
    <div class="error">
        <div class="error-logo"><img src="images/diskover.png" alt="diskover" width="249" height="189" /></div>
        <?php if (strpos($error, "No completed indices found") !== false) {
        echo '<h1>Welcome to Diskover-web Community Edition (ce)</h1>';
        echo '<p class="text-info"><i class="fas fa-info-circle"></i> '.$error.'</p>';
        } else {
        echo '<h1>Oops something went wrong <i class="far fa-frown"></i></h1>';
        echo '<p class="text-danger"><i class="fas fa-exclamation-circle"></i> '.$error.'</p>';
        }
        if (strpos($error, "Selected indices are no longer available") !== false ||
            strpos($error, "Selected indices have changed") !== false) {
        echo '<p><a href="selectindices.php?reloadindices">Select index</a></p>';
        } else {
        echo '<p><a href="index.php?reloadindices">Reload index page</a></p>';
        echo '<p><a href="settings.php">Settings</a></p>';
        }
        if ($config->LOGIN_REQUIRED) {
        echo '<p><a href="logout.php">Logout</a></p>';
        } ?>
    </div>
</body>

</html>