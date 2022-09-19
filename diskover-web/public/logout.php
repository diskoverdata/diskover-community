<?php
/*
diskover-web community edition (ce)
https://github.com/diskoverdata/diskover-community/
https://diskoverdata.com

Copyright 2017-2022 Diskover Data, Inc.
"Community" portion of Diskover made available under the Apache 2.0 License found here:
https://www.diskoverdata.com/apache-license/

All other content is subject to the Diskover Data, Inc. end user license agreement found at:
https://www.diskoverdata.com/eula-subscriptions/

Diskover Data products and features for all versions found here:
https://www.diskoverdata.com/solutions/

*/

session_start();
// Remove any session vars
session_unset();
session_destroy();
// Delete any path cookies
setcookie('path');
setcookie('prevpath');
setcookie('rootpath');
setcookie('parentpath');
setcookie('toppath');
setcookie('error');
// Redirect to the login page:
header("location: login.php");
exit;
