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

require '../vendor/autoload.php';
require "../src/diskover/Diskover.php";


// Get search results from Elasticsearch if the user searched for something
$results = [];

// enable search submit
echo '<script type="text/javascript">
enableSearchSubmit();
</script>';

if (isset($_GET)) {
    // use wildcard search if predictive search enabled
    if (getCookie('wildcardsearch') == 1) {
        if (preg_match('/(\w+):/i', $_REQUEST['q']) == false) {
            $_REQUEST['q'] = trim($_REQUEST['q'], '\*');
            $_REQUEST['q'] = "*" . $_REQUEST['q'] . "*";
        }
    }

    // get request string from predict_search
    $request = predict_search($_REQUEST['q']);

    // Setup search query
    $searchParams['index'] = $_REQUEST['index'];
    $doctype = ($_REQUEST['doctype']) ? $_REQUEST['doctype'] : '(file OR directory)';

    // search size (number of results to return
    $searchParams['size'] = 10;

    // match all if search field empty
    if (empty($_REQUEST['q'])) {
        $searchParams['body'] = [
            '_source' => ['name', 'parent_path', 'type'],
            'query' => [
                'query_string' => [
                    'query' => 'type:(file OR directory)'
                ]
            ]
        ];
    // match what's in the search field
    } else {
        $searchParams['body'] = [
            '_source' => ['name', 'parent_path', 'type'],
            'query' => [
                'query_string' => [
                    'query' => $request,
                    'fields' => ['name^5', 'name.text', 'parent_path', 'parent_path.text', 'extension'],
                    'default_operator' => 'AND',
                    'analyze_wildcard' => 'true'
                ]
            ]
        ];
    }

    // check if we need to apply any filters to search
    $searchParams = filterSearchResults($searchParams);

    // Sort search results
    $searchParams = sortSearchResults($_REQUEST, $searchParams);

    try {
        // Send search query to Elasticsearch and get scroll id and first page of results
        $queryResponse = $client->search($searchParams);
    } catch (Exception $e) {
        //echo 'Message: ' .$e->getMessage();
    }

    // set total hits
    $total = $queryResponse['hits']['total']['value'];
    if(!$total) $total = 0;
    elseif($total == 10000) $total = '10000+';
    $results = $queryResponse['hits']['hits'];

    $files = [];
    // format for output
    if (!empty($results) && count($results)>0) {
        foreach($results as $arr) {
            $files[] = [ $arr['_source']['type'], $arr['_source']['name'], $arr['_source']['parent_path'] ];
        }
    }

} else {
    die("no get data");
}

echo '<div class="pull-right" style="margin-left:10px"><button title="close" type="button" class="btn btn-default btn-sm" onclick="javascript:hideSearchBox(); return false;"><span style="font-size:14px;">&nbsp;<i class="far fa-window-close" style="color:lightgray"></i>&nbsp;</span></button></div>';
echo '<span style="color:darkgray;font-size:12px;line-height:1.2em;display:block;">es query: ' . $request . '</span>';
echo '<span class="pull-right" style="font-size:12px;color:#ccc;"><strong>' . $total . ' items found</strong></span><br />';

if (isset($files) && count($files) === 0) {
    echo '<span class="text-warning"><strong><i class="glyphicon glyphicon-eye-close"></i> No results found!</strong> Try adding a wildcard * or ? or enabling predictive search on settings page.</span>';
} else {
    foreach($files as $key => $value) {
        if ($value[0] == 'file') {
            echo '<a href="search.php?submitted=true&p=1&q=parent_path:' . rawurlencode(escape_chars($value[2])) .' AND name:' . rawurlencode(escape_chars($value[1])) . '"><i class="fas fa-file" style="color:#6E7681;display:inline-block;line-height:2.1em;margin:0 auto;margin-right:3px"></i> <span style="color:white">' . $value[1] . '</span></a>&nbsp;&nbsp;<span class="searchpath"><a href="search.php?submitted=true&p=1&q=parent_path:' . rawurlencode(escape_chars($value[2])) . '&path=' . rawurlencode($value[2]) .'"><i class="fas fa-folder" style="color:#6E7681;display:inline-block;line-height:2.1em;margin:0 auto;margin-right:1px;margin-left:3px"></i> ' . $value[2] . '</a></span><br />';
        } else {  // directory
            $parentpath = "";
            if ($value[2] === '/') {
                $parentpath = rawurlencode(escape_chars($value[2] . $value[1]));
            } else {
                $parentpath = rawurlencode(escape_chars($value[2] . '/' . $value[1]));
            }
            echo '<a href="search.php?submitted=true&p=1&q=parent_path:' . $parentpath . '&path=' . rawurlencode($value[2] . '/' . $value[1]) . '"><i class="fas fa-folder" style="color:#6E7681;display:inline-block;line-height:2.1em;margin:0 auto;margin-right:3px"></i> <span style="color:white">' . $value[1] . '</span></a>&nbsp;&nbsp;<span class="searchpath"><a href="search.php?submitted=true&p=1&q=parent_path:' . rawurlencode(escape_chars($value[2])) . '&path=' . rawurlencode($value[2]) . '"><i class="fas fa-folder" style="color:#6E7681;display:inline-block;line-height:2.1em;margin:0 auto;margin-right:1px;margin-left:3px"></i> ' . $value[2] . '</a></span><br />';
        }
    }
}
?>
