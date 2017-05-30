<?php

require __DIR__ . '/../vendor/autoload.php';
use diskover\Constants;
error_reporting(E_ALL ^ E_NOTICE);
require __DIR__ . "/../src/diskover/Diskover.php";

// Connect to Elasticsearch
$client = connectES();

// Get search results from Elasticsearch for tags
$results = [];
$tagCounts = ['untagged' => 0, 'delete' => 0, 'archive' => 0, 'keep' => 0];
$totalFilesize = ['untagged' => 0, 'delete' => 0, 'archive' => 0, 'keep' => 0];

// Setup search query for filesize tagCounts
$searchParams['index'] = Constants::ES_INDEX; // which index to search
$searchParams['type']  = Constants::ES_TYPE;  // which type within the index to search

// Calculate total filesizes for each tag
foreach ($tagCounts as $tag => $value) {
  $searchParams['body']['query']['match']['_all'] = $tag; // what to search for
  // Send search query to Elasticsearch and get tag tagCounts
  $queryResponse = $client->search($searchParams);
  $tagCounts[$tag] = $queryResponse['hits']['total'];
  for ($i=1; $i<=$tagCounts[$tag] / $searchParams['size'] + 1; $i++) {
    $searchParams['size']  = 100; // limit results
    $searchParams['from'] = $i * $searchParams['size'] - $searchParams['size']; // start from for results
    $queryResponse = $client->search($searchParams);
    $results[$tag] = $queryResponse['hits']['hits'];
    foreach ($results[$tag] as $result) {
      // Add filesize to total
      $totalFilesize[$tag] += $result['_source']['filesize'];
    }
  }
}

// Get search results from Elasticsearch for duplicate files
$dupesList = [];
$dupeCount = 0;

// Setup search query for dupes count
$searchParams['body'] = [
   'size' => 0,
   'aggs' => [
     'duplicateCount' => [
       'terms' => [
         'field' => 'filehash',
         'min_doc_count' => 2,
         'size' => 10,
       ],
    'aggs' => [
      'duplicateDocuments' => [
        'top_hits' => [
          'size' => 10
        ]
      ]
    ]
      ]
    ],
    'query' => [
      'query_string' => [
        'analyze_wildcard' => 'true',
        'query' => 'is_dupe:true'
      ]
    ]
];
$queryResponse = $client->search($searchParams);
$totalDupes = $queryResponse['hits']['total'];

$searchParams['size']  = 100; // limit results

// Calculate total filesizes of dupes
for ($i=1; $i<=$totalDupes / $searchParams['size'] + 1; $i++) {
  $searchParams['from'] = $i * $searchParams['size'] - $searchParams['size']; // start from for results
  $queryResponse = $client->search($searchParams);
  $results[$tag] = $queryResponse['hits']['hits'];
  foreach ($results[$tag] as $result) {
    // Add filesize to total
    $totalFilesizeDupes += $result['_source']['filesize'];
  }
}

?>
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta http-equiv="X-UA-Compatible" content="IE=edge" />
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>diskover &mdash; Dashboard</title>
  <link rel="stylesheet" href="/css/bootstrap.min.css" media="screen" />
  <link rel="stylesheet" href="/css/bootstrap-theme.min.css" media="screen" />
  <link rel="stylesheet" href="/css/diskover.css" media="screen" />
</head>
<body>
<?php include __DIR__ . "/nav.php"; ?>
<div class="container">
  <div class="row">
    <div class="col-xs-4">
      <img src="/images/diskover.png" class="img-responsive" style="margin-top:30px;" alt="diskover" width="249" height="189" />
    </div>
    <div class="col-xs-8">
      <div class="jumbotron">
        <h1><span class="glyphicon glyphicon-piggy-bank"></span> Space Savings</h1>
        <p>You could save <strong><?php echo formatBytes($totalFilesize['untagged']+$totalFilesize['delete']+$totalFilesize['archive']+$totalFilesize['keep']); ?></strong> of disk space if you delete or archive all your files.
          There are <strong><?php echo $totalDupes; ?></strong> duplicate files taking up <strong><?php echo formatBytes($totalFilesizeDupes); ?></strong> space.</p>
      </div>
    </div>
  </div>
<div class="alert alert-dismissible alert-success">
  <button type="button" class="close" data-dismiss="alert">&times;</button>
  <strong>Welcome to diskover's tag manager.</strong> This application will help you <a href="/simple.php" class="alert-link">search and tag files</a> in your diskover indices in Elasticsearch.
</div>
<?php
if ($totalFilesize['untagged'] == 0 AND $totalFilesize['delete'] == 0 AND $totalFilesize['archive'] == 0 AND $totalFilesize['keep'] == 0) {
?>
<div class="alert alert-dismissible alert-danger">
  <button type="button" class="close" data-dismiss="alert">&times;</button>
  <h4><span class="glyphicon glyphicon-alert"></span> No diskover indices found! :(</h4>
  <p>It looks like you haven't crawled any files yet. Crawl some files and come back.</p>
</div>
<?php
}
?>

<?php
if ($totalDupes > 0) {
?>
<div class="alert alert-dismissible alert-danger">
  <button type="button" class="close" data-dismiss="alert">&times;</button>
  <h4><span class="glyphicon glyphicon-duplicate"></span> Duplicate files!</h4>
  <p>It looks like you have <a href="/advanced.php?submitted=true&amp;p=1&amp;is_dupe=true" class="alert-link">duplicate files</a>, tag the copies for deletion to save space.</p>
</div>
<?php
}
?>
<?php
if ($tagCounts['untagged'] > 0) {
?>
<div class="alert alert-dismissible alert-warning">
  <button type="button" class="close" data-dismiss="alert">&times;</button>
  <h4><span class="glyphicon glyphicon-tags"></span> Untagged files!</h4>
  <p>It looks like you have <a href="/advanced.php?submitted=true&amp;p=1&amp;tag=untagged" class="alert-link">untagged files</a>, time to start tagging and free up some space :)</p>
</div>
<?php
}
?>
<?php
if ($tagCounts['untagged'] == 0 AND $totalFilesize['delete'] > 0 AND $totalFilesize['archive'] > 0 AND $totalFilesize['keep'] > 0 ) {
?>
<div class="alert alert-dismissible alert-info">
  <button type="button" class="close" data-dismiss="alert">&times;</button>
  <span class="glyphicon glyphicon-thumbs-up"></span> <strong>Well done!</strong> It looks like all files have been tagged.
</div>
<?php
}
?>
<div class="row">
  <div class="col-xs-6">
    <h3><span class="glyphicon glyphicon-tag"></span> Tag Counts</h3>
    <ul class="nav nav-pills">
      <li><a href="/advanced.php?submitted=true&amp;p=1&amp;tag=untagged">untagged <span class="badge"><?php echo $tagCounts['untagged']; ?></span></a></li>
      <li><a href="/advanced.php?submitted=true&amp;p=1&amp;tag=delete">delete <span class="badge"><?php echo $tagCounts['delete']; ?></span></a></li>
      <li><a href="/advanced.php?submitted=true&amp;p=1&amp;tag=archive">archive <span class="badge"><?php echo $tagCounts['archive']; ?></span></a></li>
      <li><a href="/advanced.php?submitted=true&amp;p=1&amp;tag=keep">keep <span class="badge"><?php echo $tagCounts['keep']; ?></span></a></li>
    </ul>
  </div>
  <div class="col-xs-6">
    <h3><span class="glyphicon glyphicon-hdd"></span> Total File Sizes</h3>
    <ul class="list-group">
      <li class="list-group-item">
        <span class="badge"><?php echo formatBytes($totalFilesize['untagged']); ?></span>
        untagged
      </li>
      <li class="list-group-item">
        <span class="badge"><?php echo formatBytes($totalFilesize['delete']); ?></span>
        delete
      </li>
      <li class="list-group-item">
        <span class="badge"><?php echo formatBytes($totalFilesize['archive']); ?></span>
        archive
      </li>
      <li class="list-group-item">
        <span class="badge"><?php echo formatBytes($totalFilesize['keep']); ?></span>
        keep
      </li>
    </ul>
  </div>
</div>
</div>
<script language="javascript" src="/js/jquery.min.js"></script>
<script language="javascript" src="/js/bootstrap.min.js"></script>
<script language="javascript" src="/js/diskover.js"></script>
</body>
</html>
