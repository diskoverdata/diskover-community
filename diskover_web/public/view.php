<?php

require __DIR__ . '/../vendor/autoload.php';

use diskover\Constants;
use Elasticsearch\Common\Exceptions\Missing404Exception;
use Elasticsearch\ClientBuilder;

error_reporting(E_ALL ^ E_NOTICE);

$message = $_REQUEST['message'];

// Check if file ID was provided
if (empty($_REQUEST['id'])) {
    $message = 'No file requested! Please provide a file ID.';
} else {
   // Connect to local Elasticsearch node
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

    // Try to get file from Elasticsearch
    try {
        $file = $client->get([
            'id'    => $_REQUEST['id'],
            'index' => $_REQUEST['index'],
            'type'  => Constants::ES_TYPE
        ]);
        $file = $file['_source'];
    } catch (Missing404Exception $e) {
        $message = 'Requested file not found :(';
    }
}
?>
<html>
<head>
  <title>diskover &mdash; Search</title>
  <link rel="stylesheet" href="/css/bootstrap.min.css" />
</head>
<body>
<div class="container bg-danger" id="message">
<?php
if (!empty($message)) {
?>
<h1><?php echo $message; ?></h1>
<?php
}
?>
</div>

<div class="container">
  <h1><a href="/advanced.php?submitted=true&amp;p=1&amp;filename=<?php echo $file['filename']; ?>"><?php echo $file['filename']; ?></a></h1>
  <h4><?php echo $file['path_full']; ?></h4>
  <h5>Parent directory: <a href="/advanced.php?submitted=true&amp;p=1&amp;path_parent=<?php echo $file['path_parent']; ?>"><?php echo $file['path_parent']; ?></a></h5>
<div class="row">
  <div class="col-xs-5">
    <ul class="list-group">
      <li class="list-group-item">
        <span class="badge"><?php echo $file['filesize']; ?></span>
        Filesize (bytes)
      </li>
      <li class="list-group-item">
        <span class="badge"><a href="/advanced.php?submitted=true&amp;p=1&amp;extension=<?php echo $file['extension']; ?>"><?php echo $file['extension']; ?></a></span>
        Extension
      </li>
      <li class="list-group-item">
        <span class="badge"><a href="/advanced.php?submitted=true&amp;p=1&amp;owner=<?php echo $file['owner']; ?>"><?php echo $file['owner']; ?></a></span>
        Owner
      </li>
      <li class="list-group-item">
        <span class="badge"><a href="/advanced.php?submitted=true&amp;p=1&amp;group=<?php echo $file['group']; ?>"><?php echo $file['group']; ?></a></span>
        Group
      </li>
      <li class="list-group-item">
        <span class="badge"><a href="/advanced.php?submitted=true&amp;p=1&amp;inode=<?php echo $file['inode']; ?>"><?php echo $file['inode']; ?></a></span>
        Inode
      </li>
      <li class="list-group-item">
        <span class="badge"><?php echo $file['hardlinks']; ?></span>
        Hardlinks
      </li>
      <li class="list-group-item">
        <span class="badge"><a href="/advanced.php?submitted=true&amp;p=1&amp;filehash=<?php echo $file['filehash']; ?>"><?php echo $file['filehash']; ?></a></span>
        Filehash
      </li>
    </div>
    <div class="col-xs-5">
      <ul class="list-group">
    <li class="list-group-item">
      <span class="badge"><?php echo $file['last_modified']; ?></span>
      Last modified (utc)
    </li>
    <li class="list-group-item">
      <span class="badge"><?php echo $file['last_access']; ?></span>
      Last access (utc)
    </li>
    <li class="list-group-item">
      <span class="badge"><?php echo $file['last_change']; ?></span>
      Last change (utc)
    </li>
    </ul>
    </div>
    <div class="col-xs-5">
      <ul class="list-group">
        <li class="list-group-item">
          <span class="badge"><a href="/advanced.php?submitted=true&amp;p=1&amp;index=<?php echo $_REQUEST['index']; ?>"><?php echo $_REQUEST['index']; ?></a></span>
          Index Name
        </li>
        <li class="list-group-item">
          <span class="badge"><?php echo $file['indexing_date']; ?></span>
          Indexed on (utc)
        </li>
      </ul>
    </div>
    <div class="col-xs-5">
      <ul class="list-group">
        <li class="list-group-item">
          <span class="badge"><a href="/advanced.php?submitted=true&amp;p=1&amp;tag=<?php echo $file['tag']; ?>"><?php echo $file['tag']; ?></a></span>
          Tag
        </li>
      </ul>
    </div>
  </div>
  <div class="row">
    <p><a class="btn btn-primary btn-lg" onclick="window.history.back()">< </a></p>
  </div>
</div>
</body>
</html>
