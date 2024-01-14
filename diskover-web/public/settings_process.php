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

// diskover-web community edition (ce) settings page forms processing

namespace diskover;

require '../vendor/autoload.php';
//require "../src/diskover/Auth.php";
//require "../src/diskover/Diskover.php";

use diskover\ConfigDatabase;

// Load database and get config settings.
$db = new ConfigDatabase();
$db->connect();

$errors = [];
$data = [];

if ($_POST['formname'] === 'elasticsearchform') {
    if (empty($_POST['ES_HOST'])) {
        $errors['ES_HOST'] = 'ES_HOST is required.';
    }
    
    if (empty($_POST['ES_PORT'])) {
        $errors['ES_PORT'] = 'ES_PORT is required.';
    }
    
    if (empty($_POST['ES_HTTPS'])) {
        $errors['ES_HTTPS'] = 'ES_HTTPS is required.';
    } elseif ($_POST['ES_HTTPS'] !== 'true' && $_POST['ES_HTTPS'] !== 'false') {
        $errors['ES_HTTPS'] = 'ES_HTTPS must be set to true or false.';
    }
    
    if (empty($_POST['ES_SSLVERIFICATION'])) {
        $errors['ES_SSLVERIFICATION'] = 'ES_SSLVERIFICATION is required.';
    } elseif ($_POST['ES_SSLVERIFICATION'] !== 'true' && $_POST['ES_SSLVERIFICATION'] !== 'false') {
        $errors['ES_SSLVERIFICATION'] = 'ES_SSLVERIFICATION must be set to true or false.';
    }
} elseif ($_POST['formname'] === 'otherform') {
    if (empty($_POST['TIMEZONE'])) {
        $errors['TIMEZONE'] = 'TIMEZONE is required.';
    }
    
    if (empty($_POST['LOGIN_REQUIRED'])) {
        $errors['LOGIN_REQUIRED'] = 'LOGIN_REQUIRED is required.';
    } elseif ($_POST['LOGIN_REQUIRED'] !== 'true' && $_POST['LOGIN_REQUIRED'] !== 'false') {
        $errors['LOGIN_REQUIRED'] = 'LOGIN_REQUIRED must be set to true or false.';
    }
    
    if (empty($_POST['SEARCH_RESULTS'])) {
        $errors['SEARCH_RESULTS'] = 'SEARCH_RESULTS is required.';
    }

    if (empty($_POST['SIZE_FIELD'])) {
        $errors['SIZE_FIELD'] = 'SIZE_FIELD is required.';
    } elseif ($_POST['SIZE_FIELD'] !== 'size' && $_POST['SIZE_FIELD'] !== 'size_du') {
        $errors['SIZE_FIELD'] = 'SIZE_FIELD must be set to size or size_du.';
    }

    if (empty($_POST['FILE_TYPES'])) {
        $errors['FILE_TYPES'] = 'FILE_TYPES is required.';
    }

    if (empty($_POST['MAX_INDEX'])) {
        $errors['MAX_INDEX'] = 'MAX_INDEX is required.';
    }

    if (empty($_POST['INDEXINFO_CACHETIME'])) {
        $errors['INDEXINFO_CACHETIME'] = 'INDEXINFO_CACHETIME is required.';
    }

    if (empty($_POST['NEWINDEX_CHECKTIME'])) {
        $errors['NEWINDEX_CHECKTIME'] = 'NEWINDEX_CHECKTIME is required.';
    }
}

if (!empty($errors)) {
    $data['success'] = false;
    $data['errors'] = $errors;
} else {
    // update sqlite db
    foreach ($_POST as $key => $value) {
        // skip hidden field formname
        if ($key === 'formname') continue;
        // handle form input arrays
        if ($key === 'FILE_TYPES' || $key === 'EXTRA_FIELDS') {
            $arr = array();
            foreach ($value as $k => $v) {
                if (empty($v)) continue;
                if (!($k & 1)) {
                    $arr[$v] = ($key === 'FILE_TYPES') ? explode(", ", $value[$k+1]) : $value[$k+1];
                }
            }
            $db->updateConfigSetting($key, $arr);
        } else {
            $db->updateConfigSetting($key, $value);
        }
    }
    $data['success'] = true;
    $data['message'] = 'Success!';
}

echo json_encode($data);