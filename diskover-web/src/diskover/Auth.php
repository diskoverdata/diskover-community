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

ini_set('session.gc_maxlifetime', 604800);
ini_set("session.cookie_lifetime", 604800);
session_start();
require 'config_inc.php';

error_reporting(E_ALL ^ E_NOTICE);

if ($config->LOGIN_REQUIRED) {
    if (isset($_SESSION['loggedin'])) {
        // check if user is logged in and timeout not exceeded
        $sessionLength = $_SESSION['stayloggedin'] ? 60 * 60 * 24 * 7 : 60 * 60 * 8;
        if (time() - $_SESSION['last_activity'] < $sessionLength) {
            // set last activity again so session extends
            $_SESSION['last_activity'] = time();
        } else {
            // login timeout expired, log user out
            header('location: logout.php');
            exit;
        }
    } else {
        // user not logged in, redirect to login page
        session_unset();
        session_destroy();
        header('location: login.php');
        exit;
    }
}
