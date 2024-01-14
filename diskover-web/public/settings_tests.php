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

// diskover-web community edition (ce) settings page forms tests

require '../vendor/autoload.php';
require "../src/diskover/Diskover.php";

$errors = [];
$data = [];

// test ES connection
try {
    $config->ES_HOST = $_POST['ES_HOST'];
    $config->ES_PORT = $_POST['ES_PORT'];
    $config->ES_USER = $_POST['ES_USER'];
    $config->ES_PASS = $_POST['ES_PASS'];
    $config->ES_HTTPS = filter_var($_POST['ES_HTTPS'], FILTER_VALIDATE_BOOLEAN);
    $config->ES_SSLVERIFICATION = filter_var($_POST['ES_SSLVERIFICATION'], FILTER_VALIDATE_BOOLEAN);

    $esclient = new ESClient;
    $client = $esclient->createClient();
    $res = $client->ping();
}
catch(Exception $e) {
    $errors[] = 'Elasticsearch connection error: ' . $e->getMessage();
}


if (!empty($errors)) {
    $data['success'] = false;
    $data['errors'] = $errors;
} else {
    $data['success'] = true;
    $data['message'] = 'Success!';
}

echo json_encode($data);