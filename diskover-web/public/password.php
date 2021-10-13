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

ob_start();
require '../vendor/autoload.php';

use diskover\Constants;
use diskover\Login;
use diskover\UserDatabase;

// Set logging level
error_reporting(E_ERROR | E_PARSE);

$initialPassword = isset($_GET['initial']);

$msg = '';
// If any POST hits this page, attempt to process.
if ($_SERVER['REQUEST_METHOD'] == 'POST') {
    session_start();

    $db = new UserDatabase();
    $db->connect();
    $result = $db->changePassword($initialPassword);

    if ($result === '') {
        // Successful password change, redirect to log in again.
        session_unset();
        session_destroy();

        header("location: login.php?changed");
        exit;
    } else {
        // Failed password change, inform user.
        $msg = '<i class="glyphicon glyphicon-ban-circle"></i> '.$result;
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
    <title>diskover &mdash; Password Change</title>
    <link rel="stylesheet" href="css/fontawesome-free/css/all.min.css" media="screen" />
    <link rel="stylesheet" href="css/bootswatch.min.css" media="screen" />
    <link rel="stylesheet" href="css/diskover.css" media="screen" />
    <link rel="icon" type="image/png" href="images/diskoverfavico.png" />
    <style>
        .login-logo {
            text-align: center;
            padding: 40px 0 0 0;
        }

        .login {
            width: 400px;
            background-color: #1C1E21;
            box-shadow: 0 0 9px 0 rgba(0, 0, 0, 0.3);
            margin: 100px auto;
        }

        .login h1 {
            text-align: center;
            color: #ffffff;
            font-size: 24px;
            padding: 0 0 5px 0;
        }

        .login h4 {
            text-align: center;
            color: #cccccc;
            font-size: 18px;
            padding: 0 0 20px 0;
            border-bottom: 1px solid #000000;
        }

        .login-error {
            text-align: center;
            font-size: 14px;
            margin-top: 10px;
        }

        .login form {
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            padding-top: 20px;
        }

        .login form label {
            display: flex;
            justify-content: center;
            align-items: center;
            width: 50px;
            height: 50px;
            background-color: #1C1E21;
            color: lightgray;
        }

        .login form input[type="password"] {
            width: 310px;
            height: 50px;
            border: 1px solid #000000;
            margin-bottom: 20px;
            padding: 0 15px;
            font-size: 16px;
        }

        .login form input[type="submit"] {
            width: 100%;
            padding: 15px;
            margin-top: 20px;
            border: 0;
            cursor: pointer;
            font-weight: bold;
            font-size: 16px;
            color: #ffffff !important;
            background-color: #3C4247 !important;
            transition: background-color 0.2s;
        }

        .login form input[type="submit"]:hover {
            background-color: #474D54 !important;
            transition: background-color 0.2s;
        }
    </style>
</head>

<body>
<div class="login">
    <div class="login-logo"><img src="images/diskover.png" alt="diskover" width="249" height="189" /></div>
    <h1>Password Change</h1>
    <h4>Welcome to Diskover!<br>Please set your initial password.</h4>
    <form method="post">
        <?php /* TODO: If they are not changing their default password, prompt for current password. */ ?>
        <label for="password">
            <i class="fas fa-lock"></i>
        </label>
        <input type="password" class="form-control" name="password" id="password" placeholder="Password" required>

        <label for="password2">
            <i class="fas fa-lock"></i>
        </label>
        <input type="password" class="form-control" name="password2" id="password2" placeholder="Retype Password" required>
        <input type="submit" value="Save Password" onclick="loadingShow()">
        <p class="login-error text-danger"><?php echo $msg; ?></p>
    </form>
    <div id="loading">
        <img id="loading-image" width="32" height="32" src="images/ajax-loader.gif" alt="Loading..." />
        <div id="loading-text">Loading... please wait...</div>
    </div>
</div>
</body>

<script type="text/javascript">
    var errormsg = '<?php echo $msg ?>';
    if (errormsg) {
        loadingHide();
    }

    function loadingShow() {
        if (document.getElementById('password').value !== '' && document.getElementById('password2').value !== '') {
            document.getElementById('loading').style.display = 'block';
        }
    }

    function loadingHide() {
        document.getElementById('loading').style.display = 'none';
    }
</script>

</html>
