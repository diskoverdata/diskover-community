<?php

require __DIR__ . '/../vendor/autoload.php';

use diskover\Constants;
use Elasticsearch\ClientBuilder;


// Get search results from Elasticsearch if the user searched for something
$results = [];

if (empty($_REQUEST['q'])) {
        $_REQUEST['q']="";
}

if (!empty($_REQUEST['submitted'])) {



    // Connect to Elasticsearch node
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


    // Setup search query
    $searchParams['index'] = Constants::ES_INDEX; // which index to search
    $searchParams['type']  = Constants::ES_TYPE;  // which type within the index to search
    $searchParams['body']['query']['match']['_all'] = $_REQUEST['q']; // what to search for
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
<html>
<head>
  <title>diskover &mdash; Simple Search</title>
  <link rel="stylesheet" href="/css/bootstrap.min.css" />
</head>
<body>
<div class="container">
  <img src="/images/diskoversmall.png" style="margin-top:10px;margin-right:10px;"class="pull-left" alt="diskover" width="62" height="47" />
  <h1>diskover &mdash; Simple Search</h1>
<form method="get" action="<?php echo $_SERVER['PHP_SELF']; ?>" class="form-inline">
  <input name="q" value="<?php echo $_REQUEST['q']; ?>" type="text" placeholder="What are you looking for?" class="form-control input-lg" size="40" />
  <input type="hidden" name="submitted" value="true" />
  <input type="hidden" name="p" value="1" />
  <button type="submit" class="btn btn-primary btn-lg">Search</button>
  <span>&nbsp;<a href="/advanced.php">Switch to advanced search</a></span>
</form>
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
