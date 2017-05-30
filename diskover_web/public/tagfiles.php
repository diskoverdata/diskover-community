<?php

require __DIR__ . '/../vendor/autoload.php';
use diskover\Constants;
error_reporting(E_ALL ^ E_NOTICE);
require __DIR__ . "/../src/diskover/Diskover.php";

// Update files if any were submitted
if (count($_POST) > 0) {
  // Connect to Elasticsearch
  $client = connectES();

  // Update the files in Elasticsearch
  foreach ($_POST['ids'] as $id => $value) {
    $index = $_POST[$id];
    $params = array();
    $params['id'] = $id;
    $params['index'] = $index;
    $params['type'] = Constants::ES_TYPE;
    $result = $client->get($params);
    $result['_source']['tag'] = $value; // update existing field with new value

    $params['body']['doc'] = $result['_source'];
    $result = $client->update($params);
  }
}

?>
<html>
<body onload="window.history.back()">
</body>
</html>
