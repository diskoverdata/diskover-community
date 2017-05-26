<?php

require __DIR__ . '/../vendor/autoload.php';

use diskover\Constants;
use Elasticsearch\ClientBuilder;

error_reporting(E_ALL ^ E_NOTICE);
// Update files if any were submitted
if (count($_POST) > 0) {

    $esPort = getenv('APP_ES_PORT') ?: 9200;
    $hosts = [
        [
      'host' => Constants::ES_HOST,
	    'port' => $esPort,
      'user' => Constants::ES_USER,
	    'pass' => Constants::ES_PASS
        ]
    ];
    $client = ClientBuilder::create()           // Instantiate a new ClientBuilder
                        ->setHosts($hosts)      // Set the hosts
                        ->build();              // Build the client object

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

// Redirect user back to results page
header('Location: ' . $_SERVER['HTTP_REFERER']);
exit();

?>
