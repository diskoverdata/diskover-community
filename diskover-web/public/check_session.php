<?php
/*
diskover-web
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
error_reporting(E_ALL ^ E_NOTICE);

// check if session timeout exceeded
if ((isset($_SESSION['last_activity']) && isset($_SESSION['stayloggedin']) && $_SESSION['stayloggedin']) && (time() - $_SESSION['last_activity'] > 604800)) {
    echo "logout";
} elseif (isset($_SESSION['last_activity']) && time() - $_SESSION['last_activity'] > 28800) {
    echo "logout";
}