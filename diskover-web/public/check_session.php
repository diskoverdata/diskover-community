<?php
/*
diskover-web
https://diskoverdata.com

Copyright 2017-2022 Diskover Data, Inc.
"Community" portion of Diskover made available under the Apache 2.0 License found here:
https://www.diskoverdata.com/apache-license/
 
All other content is subject to the Diskover Data, Inc. end user license agreement found at:
https://www.diskoverdata.com/eula-subscriptions/
  
Diskover Data products and features for all versions found here:
https://www.diskoverdata.com/solutions/

*/

ini_set('session.gc_maxlifetime', 604800);
ini_set("session.cookie_lifetime", 604800);
session_set_cookie_params(604800, "/");
session_start();
error_reporting(E_ALL ^ E_NOTICE);

// check if session timeout exceeded and if so, log user out by responding with logout to ajax post request in diskover.js
if (isset($_POST)) {
    if ($_SESSION['stayloggedin'] && time() - $_SESSION['last_activity'] > 604800) {
        echo "logout";
    } elseif (!$_SESSION['stayloggedin'] && time() - $_SESSION['last_activity'] > 28800) {
        echo "logout";
    } else {
        // update session to keep it active
        $_SESSION['loggedin'] = true;
        // respond with time since last activity
        echo time() - $_SESSION['last_activity'];
    }
}