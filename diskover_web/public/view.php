<?php

require __DIR__ . '/../vendor/autoload.php';
use diskover\Constants;
use Elasticsearch\Common\Exceptions\Missing404Exception;
error_reporting(E_ALL ^ E_NOTICE);
require __DIR__ . "/../src/diskover/Diskover.php";

$message = $_REQUEST['message'];

// Check if file ID was provided
if (empty($_REQUEST['id'])) {
    $message = 'No file requested! Please provide a file ID.';
} else {
    // Connect to Elasticsearch
    $client = connectES();

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
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta http-equiv="X-UA-Compatible" content="IE=edge" />
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>diskover &mdash; File View</title>
  <link rel="stylesheet" href="/css/bootstrap.min.css" media="screen" />
  <link rel="stylesheet" href="/css/diskover.css" media="screen" />
</head>
<body>
  <?php include __DIR__ . "/nav.php"; ?>
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
  <div class="row">
    <div class="col-xs-12">
      <h1><a href="/advanced.php?submitted=true&amp;p=1&amp;filename=<?php echo $file['filename']; ?>"><?php echo $file['filename']; ?></a></h1>
      <h4><?php echo $file['path_full']; ?></h4>
      <h5>Parent directory: <a href="/advanced.php?submitted=true&amp;p=1&amp;path_parent=<?php echo $file['path_parent']; ?>"><?php echo $file['path_parent']; ?></a></h5>
    </div>
  </div>
  <div class="row">
    <div class="col-xs-5">
      <ul class="list-group">
        <li class="list-group-item">
          <span class="badge"><?php echo $file['filesize']; ?></span>
          Filesize (bytes)
        </li>
        <li class="list-group-item">
          <span class="badge"><?php echo $file['extension']; ?></span>
          <a href="/advanced.php?submitted=true&amp;p=1&amp;extension=<?php echo $file['extension']; ?>">Extension</a>
        </li>
        <li class="list-group-item">
          <span class="badge"><?php echo $file['owner']; ?></span>
          <a href="/advanced.php?submitted=true&amp;p=1&amp;owner=<?php echo $file['owner']; ?>">Owner</a>
        </li>
        <li class="list-group-item">
          <span class="badge"><?php echo $file['group']; ?></span>
          <a href="/advanced.php?submitted=true&amp;p=1&amp;group=<?php echo $file['group']; ?>">Group</a>
        </li>
        <li class="list-group-item">
          <span class="badge"><?php echo $file['inode']; ?></span>
          <a href="/advanced.php?submitted=true&amp;p=1&amp;inode=<?php echo $file['inode']; ?>">Inode</a>
        </li>
        <li class="list-group-item">
          <span class="badge"><?php echo $file['hardlinks']; ?></span>
          Hardlinks
        </li>
        <li class="list-group-item">
          <span class="badge"><?php echo $file['filehash']; ?></span>
          <a href="/advanced.php?submitted=true&amp;p=1&amp;filehash=<?php echo $file['filehash']; ?>">Filehash</a>
        </li>
        <li class="list-group-item">
          <span class="badge"><?php echo $file['is_dupe']; ?></span>
          <a href="/advanced.php?submitted=true&amp;p=1&amp;is_dupe=<?php echo $file['is_dupe']; ?>">Is dupe</a>
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
            <span class="badge"><?php echo $_REQUEST['index']; ?></span>
            <a href="/advanced.php?submitted=true&amp;p=1&amp;index=<?php echo $_REQUEST['index']; ?>">Index name</a>
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
            <span class="badge"><?php echo $file['tag']; ?></span>
            <a href="/advanced.php?submitted=true&amp;p=1&amp;tag=<?php echo $file['tag']; ?>">Tag</a>
          </li>
        </ul>
      </div>
    </div>
  <div class="row">
    <div class="col-xs-2">
      <p><a class="btn btn-primary btn-lg" onclick="window.history.back()">< </a></p>
    </div>
  </div>
</div>
<script language="javascript" src="/js/jquery.min.js"></script>
<script language="javascript" src="/js/bootstrap.min.js"></script>
<script language="javascript" src="/js/diskover.js"></script>
</body>
</html>
