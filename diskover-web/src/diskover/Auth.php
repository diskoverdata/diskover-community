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
use diskover\Constants;
error_reporting(E_ALL ^ E_NOTICE);

if (Constants::LOGIN_REQUIRED) {
    if (!isset($_SESSION['loggedin'])) {
        // user not logged in, redirect to login page
        header("location: login.php");
        exit();
    }
    // set last activity again so session extends
    $_SESSION['last_activity'] = time();
}