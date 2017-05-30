<?php

require __DIR__ . '/../vendor/autoload.php';
use diskover\Constants;
error_reporting(E_ALL ^ E_NOTICE);
require __DIR__ . "/../src/diskover/Diskover.php";

// Get search results from Elasticsearch if the user searched for something
$results = [];

if (empty($_REQUEST['q'])) {
        $_REQUEST['q']="";
}

if (!empty($_REQUEST['submitted'])) {
  // Connect to Elasticsearch
  $client = connectES();

  // Setup search query
  $searchParams['index'] = Constants::ES_INDEX; // which index to search
  $searchParams['type']  = Constants::ES_TYPE;  // which type within the index to search
  $searchParams['body']['query']['query_string']['query'] = $_REQUEST['q']; // what to search for
  $searchParams['size']  = 100; // limit results
  $p = $_REQUEST['p'];
  $searchParams['from'] = $p * $searchParams['size'] - $searchParams['size']; // start from for results

  if (empty($_REQUEST['q'])) {
    $searchParams['body'] = [ 'query' => [ 'match_all' => (object) [] ] ];
  }

  // Send search query to Elasticsearch and get results
  $queryResponse = $client->search($searchParams);
  $results = $queryResponse['hits']['hits'];
  $total = $queryResponse['hits']['total'];
}
?>
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta http-equiv="X-UA-Compatible" content="IE=edge" />
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>diskover &mdash; Simple Search</title>
  <link rel="stylesheet" href="/css/bootstrap.min.css" media="screen" />
  <link rel="stylesheet" href="/css/bootstrap-theme.min.css" media="screen" />
  <link rel="stylesheet" href="/css/diskover.css" media="screen" />
</head>
<body>
<?php include __DIR__ . "/nav.php"; ?>

<?php if (!isset($_REQUEST['submitted'])) { ?>

<div class="container-fluid">
  <div class="row">
    <div class="col-xs-2 col-xs-offset-5">
      <p class="text-center"><img src="/images/diskoversmall.png" style="margin-top:130px;" alt="diskover" width="62" height="47" /></p>
    </div>
  </div>
  <div class="row">
    <div class="col-xs-6 col-xs-offset-3">
      <p class="text-center"><h1 class="text-nowrap text-center">diskover &mdash; Simple Search</h1></p>
    </div>
  </div>
  <div class="row">
    <div class="col-xs-8 col-xs-offset-2">
      <p class="text-center">
      <form method="get" action="<?php echo $_SERVER['PHP_SELF']; ?>" class="form-inline text-center">
      <input name="q" value="<?php echo $_REQUEST['q']; ?>" type="text" placeholder="What are you looking for?" class="form-control input-lg" size="50" />
      <input type="hidden" name="submitted" value="true" />
      <input type="hidden" name="p" value="1" />
      <button type="submit" class="btn btn-primary btn-lg">Search</button>
      </form>
      </p>
    </div>
  </div>
  <div class="row">
    <div class="col-xs-8 col-xs-offset-2">
      <p class="text-center"><a href="https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-query-string-query.html#query-string-syntax" target="_blank">Query string syntax help</a>
      &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<a href="/advanced.php">Switch to advanced search</a></p>
    </div>
  </div>
</div>

<?php } ?>

<?php

if (isset($_REQUEST['submitted'])) {
  include __DIR__ . "/results.php";
}

?>
</div>
<script language="javascript" src="/js/jquery.min.js"></script>
<script language="javascript" src="/js/bootstrap.min.js"></script>
<script language="javascript" src="/js/diskover.js"></script>
</body>
</html>
