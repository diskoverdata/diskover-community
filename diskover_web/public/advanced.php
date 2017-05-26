<?php

require __DIR__ . '/../vendor/autoload.php';

use diskover\Constants;
use Elasticsearch\ClientBuilder;

// Get search results from Elasticsearch if the user searched for something
$results = [];
error_reporting(E_ALL ^ E_NOTICE);

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
    $searchParams['body'] = [];
    $searchParams['size']  = 100; // limit results
    $p = $_REQUEST['p'];
    $searchParams['from'] = $p * $searchParams['size'] - $searchParams['size']; // start from for results

    $filterClauses = [];

    if ($_REQUEST['filename']) {
      $filterClauses[] = [ 'term' => [ 'filename' => $_REQUEST['filename'] ] ];
    }

    if ($_REQUEST['path_parent']) {
      $filterClauses[] = [ 'term' => [ 'path_parent' => $_REQUEST['path_parent'] ] ];
    }

    if ($_REQUEST['tag']) {
      $filterClauses[] = [ 'term' => [ 'tag' => $_REQUEST['tag'] ] ];
    }

    if ($_REQUEST['inode']) {
      $filterClauses[] = [ 'term' => [ 'inode' => $_REQUEST['inode'] ] ];
    }

    if ($_REQUEST['last_mod_time_low'] || $_REQUEST['last_mod_time_high']) {
      $rangeFilter = [];
      if ($_REQUEST['last_mod_time_low']) {
        $rangeFilter['gte'] = (string) $_REQUEST['last_mod_time_low'];
      }
      if ($_REQUEST['last_mod_time_high']) {
        $rangeFilter['lte'] = (string) $_REQUEST['last_mod_time_high'];
      }
      $filterClauses[] = [ 'range' => [ 'last_modified' => $rangeFilter ] ];
    }

    if ($_REQUEST['last_acces_time_low'] || $_REQUEST['last_acces_time_high']) {
      $rangeFilter = [];
      if ($_REQUEST['last_acces_time_low']) {
        $rangeFilter['gte'] = (string) $_REQUEST['last_acces_time_low'];
      }
      if ($_REQUEST['last_acces_time_high']) {
        $rangeFilter['lte'] = (string) $_REQUEST['last_acces_time_high'];
      }
      $filterClauses[] = [ 'range' => [ 'last_access' => $rangeFilter ] ];
    }

    if ($_REQUEST['file_size_bytes_low'] || $_REQUEST['file_size_bytes_high']) {
      $rangeFilter = [];
      if ($_REQUEST['file_size_bytes_low']) {
        $rangeFilter['gte'] = (int) $_REQUEST['file_size_bytes_low'];
      }
      if ($_REQUEST['file_size_bytes_high']) {
        $rangeFilter['lte'] = (int) $_REQUEST['file_size_bytes_high'];
      }
      $filterClauses[] = [ 'range' => [ 'filesize' => $rangeFilter ] ];
    }

    if ($_REQUEST['hardlinks_low'] || $_REQUEST['hardlinks_high']) {
      $rangeFilter = [];
      if ($_REQUEST['hardlinks_low']) {
        $rangeFilter['gte'] = (int) $_REQUEST['hardlinks_low'];
      }
      if ($_REQUEST['hardlinks_high']) {
        $rangeFilter['lte'] = (int) $_REQUEST['hardlinks_high'];
      }
      $filterClauses[] = [ 'range' => [ 'hardlinks' => $rangeFilter ] ];
    }

    if ($_REQUEST['filehash']) {
      $filterClauses[] = [ 'term' => [ 'filehash' => $_REQUEST['filehash'] ] ];
    }

    if ($_REQUEST['extension']) {
      $filterClauses[] = [ 'term' => [ 'extension' => $_REQUEST['extension'] ] ];
    }

    if ($_REQUEST['owner']) {
      $filterClauses[] = [ 'term' => [ 'owner' => $_REQUEST['owner'] ] ];
    }

    if ($_REQUEST['group']) {
      $filterClauses[] = [ 'term' => [ 'group' => $_REQUEST['group'] ] ];
    }

    if ($_REQUEST['index']) {
      $filterClauses[] = [ 'term' => [ '_index' => $_REQUEST['index'] ] ];
    }

    // Build complete search request body
    if (count($filterClauses) == 1) {
      $searchParams['body'] = [ 'query' => $filterClauses[0] ];
    } elseif (count($filterClauses) > 0) {
      $searchParams['body'] = [ 'query' => [ 'bool' => [ 'filter' => $filterClauses ] ] ];
    } else {
      $searchParams['body'] = [ 'query' => [ 'match_all' => (object) [] ] ];
    }

//echo json_encode($searchParams['body'], JSON_PRETTY_PRINT); exit;

    // Send search query to Elasticsearch and get results
    $queryResponse = $client->search($searchParams);
    $results = $queryResponse['hits']['hits'];
    $total = $queryResponse['hits']['total'];
}
?>
<html>
<head>
  <title>diskover &mdash; Advanced Search</title>
  <link rel="stylesheet" href="/css/bootstrap.min.css" />
</head>
<body>
<div class="container">
<img src="/images/diskoversmall.png" style="margin-top:10px;margin-right:10px;"class="pull-left" alt="diskover" width="62" height="47" />
<h1>diskover &mdash; Advanced Search</h1>
<form id="search" method="get" action="<?php echo $_SERVER['PHP_SELF']; ?>" class="form-horizontal">
<input type="hidden" name="submitted" value="true" />
<input type="hidden" name="p" value="1" />

<div class="container">
  <div class="form-group">
    <div class="row">
      <div class="col-xs-5">
        <label for="filename">Filename is...</label>
        <input name="filename" value="<?php echo $_REQUEST['filename']; ?>" placeholder="somefile.m4a" class="form-control" />
      </div>
      <div class="col-xs-3">
        <label for="filehash">Filehash is...</label>
        <input name="filehash" value="<?php echo $_REQUEST['filehash']; ?>" placeholder="md5 hash" class="form-control"/>
      </div>
      <div class="col-xs-2">
        <label for="inode">Inode is...</label>
        <input name="inode" value="<?php echo $_REQUEST['inode']; ?>" placeholder="inode num" class="form-control"/>
      </div>
    </div>
  </div>
  <div class="form-group">
    <div class="row">
      <div class="col-xs-10">
        <label for="path_parent">Directory is...  </label>
        <input name="path_parent" value="<?php echo $_REQUEST['path_parent']; ?>" placeholder="/Users/shirosai/Music" class="form-control"/>
      </div>
    </div>
  </div>
  <div class="form-group">
    <div class="row">
      <div class="col-xs-2">
        <label for="file_size_bytes_low">File size is between...</label>
        <input name="file_size_bytes_low" value="<?php echo $_REQUEST['file_size_bytes_low']; ?>" type="number" placeholder="bytes" class="form-control"/>
        <label for="file_size_bytes_high">and</label>
        <input name="file_size_bytes_high" value="<?php echo $_REQUEST['file_size_bytes_high']; ?>" type="number" placeholder="bytes" class="form-control"/>
      </div>
      <div class="col-xs-2">
        <label for="hardlinks_low">Hardlinks is between...</label>
        <input name="hardlinks_low" value="<?php echo $_REQUEST['hardlinks_low']; ?>" type="number" placeholder="2" class="form-control"/>
        <label for="hardlinks_high">and</label>
        <input name="hardlinks_high" value="<?php echo $_REQUEST['hardlinks_high']; ?>" type="number" placeholder="10" class="form-control"/>
      </div>
      <div class="col-xs-3">
        <label for="last_mod_time_low">Last modified time is between...</label>
        <input name="last_mod_time_low" value="<?php echo $_REQUEST['last_mod_time_low']; ?>" type="string" placeholder="2015-03-06T00:00:00" class="form-control"/>
        <label for="last_mod_time_high">and</label>
        <input name="last_mod_time_high" value="<?php echo $_REQUEST['last_mod_time_high']; ?>" type="string" placeholder="2017-03-06T00:00:00" class="form-control"/>
      </div>
      <div class="col-xs-3">
        <label for="last_acces_time_low">Last access time is between...</label>
        <input name="last_acces_time_low" value="<?php echo $_REQUEST['last_acces_time_low']; ?>" type="string" placeholder="2015-03-06T00:00:00" class="form-control"/>
        <label for="last_acces_time_high">and</label>
        <input name="last_acces_time_high" value="<?php echo $_REQUEST['last_acces_time_high']; ?>" type="string" placeholder="2017-03-06T00:00:00" class="form-control"/>
      </div>
    </div>
  </div>
  <div class="form-group">
    <div class="row">
      <div class="col-xs-2">
        <label for="owner">Owner is...  </label>
        <input name="owner" value="<?php echo $_REQUEST['owner']; ?>" placeholder="shirosai" class="form-control"/>
      </div>
      <div class="col-xs-2">
        <label for="group">Group is...  </label>
        <input name="group" value="<?php echo $_REQUEST['group']; ?>" placeholder="staff" class="form-control"/>
      </div>
      <div class="col-xs-2">
        <label for="extension">Extension is...</label>
        <input name="extension" value="<?php echo $_REQUEST['extension']; ?>" type="string" placeholder="zip" class="form-control"/>
      </div>
      <div class="col-xs-2">
        <label for="tag">Tag is...</label>
        <select class="form-control" name="tag">
          <option value="<?php echo $_REQUEST['tag']; ?>" selected><?php echo $_REQUEST['tag']; ?></option>
          <option value="untagged">untagged</option>
          <option value="delete">delete</option>
          <option value="archive">archive</option>
          <option value="keep">keep</option>
        </select>
      </div>
      <div class="col-xs-2">
        <label for="index">Index is...</label>
        <input name="index" value="<?php echo $_REQUEST['index']; ?>" type="string" placeholder="diskover-2017.05.24" class="form-control"/>
      </div>
    </div>
  </div>
  <div class="form-group">
    <div class="row">
      <div class="col-xs-10">
        <label for="tags">Show request JSON?</label>
        <input type="checkbox" name="debug" value="true"<?php echo ($_REQUEST['debug'] ? " checked" : ""); ?> />
      </div>
    </div>
  </div>
  </div>
  <button type="reset" class="btn btn-default">Clear</button>
  <button type="submit" class="btn btn-primary">Search</button>
  <span>&nbsp;<a href="/simple.php">Switch to simple search</a></span>
</form>
<?php

if (isset($_REQUEST['submitted'])) {
  include __DIR__ . "/results.php";

  // Print out request JSON if debug flag is set
  if ($_REQUEST['debug']) {
?>
<h3>Request JSON</h3>
<pre>
<?php echo json_encode($searchParams['body'], JSON_PRETTY_PRINT); ?>
</pre>
<?php
  }
}

?>
</div>
<script language="javascript" src="/js/jquery.min.js"></script>
<script language="javascript" src="/js/bootstrap.min.js"></script>
<script language="javascript" src="/js/diskover.js"></script>
</body>
</html>
