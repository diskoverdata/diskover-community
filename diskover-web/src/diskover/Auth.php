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
use diskover\UserDatabase;

error_reporting(E_ALL ^ E_NOTICE);

if (Constants::LOGIN_REQUIRED) {
    // check if user is logged in and timeout not exceeded
    $sessionLength = $_SESSION['stayloggedin'] ? 60 * 60 * 24 * 7 : 60 * 60 * 8;
    if ($_SESSION['loggedin'] && microtime(true) - $_SESSION['timeout'] < $sessionLength) {
        // reset timeout
        $_SESSION['timeout'] = microtime(true);

        // check if initial password needs to be changed.
        $username = $_SESSION['username'];

        // Load database and find user.
        $db = new UserDatabase();
        $db->connect();
        $user = $db->findUser($username);
        if ($user->validatePassword(Constants::PASS)) {
            // Default password is valid, redirect to change.
            header('location: password.php?initial');
            exit;
        }
    } else {
        // user not logged in, redirect to login page
        session_unset();
        session_destroy();
        header('location: login.php');
        exit();
    }
    // set last activity again so session extends
    $_SESSION['last_activity'] = time();
}
