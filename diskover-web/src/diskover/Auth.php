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

session_start();
use diskover\Constants;
error_reporting(E_ALL ^ E_NOTICE);

if (Constants::LOGIN_REQUIRED) {
    // check if user is logged in and timeout not exceeded
    if ($_SESSION['loggedin'] && $_SESSION['stayloggedin'] && microtime(true) - $_SESSION['timeout'] < 60 * 60 * 24 * 7) {
        // reset timeout
        $_SESSION['timeout'] = microtime(true);
    } elseif ($_SESSION['loggedin'] && microtime(true) - $_SESSION['timeout'] < 60 * 60 * 8) {
        // reset timeout
        $_SESSION['timeout'] = microtime(true);
    } else {
        // user not logged in, redirect to login page
        session_unset();
        session_destroy();
        header("location: login.php");
        exit();
    }
}