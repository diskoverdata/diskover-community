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
use Elasticsearch\Common\Exceptions\Missing404Exception;
require "../src/diskover/Auth.php";
require "../src/diskover/Diskover.php";


// Get search results from Elasticsearch if the user searched for something
$results = [];
$total_size = 0;
$ids_onpage = [];
$ext_onpage = [];

if (!empty($_GET['submitted'])) {
    $searchParams = [];

    // search query that user enters in nav bar
    $searchquery = $_GET['q'];

    // if nothing entered in search, search for all file and directory
    if (empty($searchquery)) {
        $searchquery = "type:(file OR directory)";
    }

    // use wildcard search if predictive search enabled
    if (getCookie('wildcardsearch') == 1) {
        if (preg_match('/(\w+):/i', $searchquery) == false) {
            $searchquery = trim($searchquery, '\*');
            $searchquery = "*" . $searchquery . "*";
        }
    }

    // Save search query
    saveSearchQuery($searchquery);
    
    // get request string from predict_search
    $request = predict_search($searchquery);

    // check for path in search query and update paths in session and cookies
    // changes the path in the search results tree
    if (empty($_GET['path']) && strpos($request, 'parent_path:\/') !== false && 
        substr_count($request, 'parent_path:\/') === 1 &&
        preg_match('/(NOT [\(]{0,}parent_path:\\\\\/)|(\(NOT parent_path:\\\\\/)/', $request) !== 1) {
        // parse out actual path from es query string
        $pp = explode('parent_path:', $request)[1];
        $pp = preg_replace('/ (AND|OR) .*/i', '', $pp);
        $pp = str_replace('\\', '', $pp);
        $pp = ltrim($pp, '(');
        $path = rtrim($pp, '*)');
        setRootPath($path);
    }

    // curent page
    $p = $_GET['p'];

    // Setup search query
    $searchParams['index'] = $esIndex;

    // get any saved search filters
    $savedfilters = getCookieToArray("searchfilters");

    // doc type to search
    if (!empty($_GET['doctype'])) {
        $doctype = $_GET['doctype'];
    } elseif ($savedfilters && $savedfilters['doctype']) {
        $doctype = $savedfilters['doctype'];
        if ($doctype === "all") {
            $doctype = "(file OR directory)";
            $_GET['doctype'] = '';
        } else {
            $_GET['doctype'] = $doctype;
        }
    } else {
        $doctype = '(file OR directory)';
    }

    // Scroll parameter alive time
    $searchParams['scroll'] = "30s";

    // search size (number of results to return per page)
    if (isset($_GET['resultsize'])) {
        $searchParams['size'] = $_GET['resultsize'];
    } elseif (getCookie("resultsize") != "") {
        $searchParams['size'] = getCookie("resultsize");
    } else {
        $searchParams['size'] = $config->SEARCH_RESULTS;
    }

    // match all if search field empty
    if (empty($request)) {
            $searchParams['body'] = [
                'query' => [
                    'query_string' => [
                        'query' => 'type:' . $doctype
                    ]
                ]
            ];
        // match what's in the search field
    } else {
        // add doc type if not already in search request
        if (!empty($_GET['doctype']) && strpos($request, ' AND type:') === false) {
            $request .= ' AND type:' . $doctype;
        }
        $searchParams['body'] = [
            'query' => [
                'query_string' => [
                    'query' => $request,
                    'analyze_wildcard' => 'true',
                    'fields' => ['name^5', 'name.text', 'parent_path', 'parent_path.text', 'extension'],
                    'default_operator' => 'AND'
                ]
            ]
        ];
    }

    // check if we need to apply any filters to search
    $searchParams = filterSearchResults($searchParams);

    // Sort search results
    $searchParams = sortSearchResults($_GET, $searchParams);
    try {
        // Send search query to Elasticsearch and get scroll id and first page of results
        $queryResponse = $client->search($searchParams);
    } catch (Missing404Exception $e) {
        handleError("Selected indices are no longer available. Please select a different index.");
    } catch (Exception $e) {
        // reset sort order and reload page if error contains reason that we can not sort
        $error_arr = json_decode($e->getMessage(), true);
        $error_reason = $error_arr['error']['root_cause'][0]['reason'];
        if (strpos($error_reason, "No mapping found for") !== false) {
            resetSort('nomapping');
        } elseif (strpos($error_reason, "Text fields are not optimised") !== false) {
            resetSort('textfield');
        } else {
            handleError('ES error: ' . $e->getMessage(), false);
        }
    }

    // set total hits
    $total = $queryResponse['hits']['total']['value'];

    $i = 1;
    // Loop through all the pages of results
    while ($i <= ceil($total / $searchParams['size'])) {
        // check if we have the results for the page we are on
        if ($i == $p) {
            // Get results
            $results[$i] = $queryResponse['hits']['hits'];
            // Add to total filesize
            for ($x = 0; $x < count($results[$i]); $x++) {
                $total_size += (int)$results[$i][$x]['_source']['size'];
                // store the index, id and doctype in ids_onpage array
                $ids_onpage[$x]['index'] = $results[$i][$x]['_index'];
                $ids_onpage[$x]['id'] = $results[$i][$x]['_id'];
                $ids_onpage[$x]['type'] = $results[$i][$x]['_source']['type'];
                // store file extensions in ext_onpage array
                if ($results[$i][$x]['_source']['type'] == "file") {
                    if ($results[$i][$x]['_source']['extension'] == '') {
                        $ext = 'NULL';
                    } else {
                        $ext = $results[$i][$x]['_source']['extension'];
                    }
                    if (sizeof($ext_onpage) <= 25) {
                        $ext_size = $results[$i][$x]['_source']['size'];
                        if (in_array($ext, $ext_onpage) !== false) {
                            $ext_onpage[$ext] = [1, $ext_size];
                        } else {
                            if (!isset($ext_onpage[$ext])) {
                                $ext_onpage[$ext] = [0,0];
                            }
                            $ext_onpage[$ext][0] += 1;
                            $ext_onpage[$ext][1] += $ext_size;
                        }
                    }
                }
            }
            arsort($ext_onpage);
            // end loop
            break;
        }

        $scroll_id = $queryResponse['_scroll_id'];

        $queryResponse = $client->scroll([
            "body" => [
                "scroll_id" => $scroll_id,
                "scroll" => "30s"
            ]
        ]);

        $i += 1;
    }
}

$estime = number_format(microtime(true) - $_SERVER["REQUEST_TIME_FLOAT"], 4);

?>
<!DOCTYPE html>
<html lang="en">

<head>
    <!-- Global site tag (gtag.js) - Google Analytics -->
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-DYSE689C04"></script>
    <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){dataLayer.push(arguments);}
    gtag('js', new Date());

    gtag('config', 'G-DYSE689C04');
    </script>
    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge" />
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>diskover &mdash; Search</title>
    <link rel="stylesheet" href="css/fontawesome-free/css/all.min.css" media="screen" />
    <link rel="stylesheet" href="css/bootswatch.min.css" media="screen" />
    <link rel="stylesheet" href="css/diskover.css" media="screen" />
    <link rel="stylesheet" href="css/diskover-filetree-search.css" media="screen" />
    <link rel="stylesheet" href="css/jquery.resizableColumns.css" media="screen" />
    <link rel="icon" type="image/png" href="images/diskoverfavico.png" />
</head>

<body>
    <?php include "nav.php"; ?>
    <?php include "results.php"; ?>
    <?php include 'modals.php' ?>

    <script language="javascript" src="js/jquery.min.js"></script>
    <script language="javascript" src="js/bootstrap.min.js"></script>
    <script language="javascript" src="js/diskover.js"></script>
    <script language="javascript" src="js/d3.v3.min.js"></script>
    <script language="javascript" src="js/d3-queue.v3.min.js"></script>
    <script language="javascript" src="js/spin.min.js"></script>
    <script language="javascript" src="js/d3.tip.v0.6.3.js"></script>
    <script language="javascript" src="js/Chart.bundle.min.js"></script>
    <script language="javascript" src="js/treelist.js"></script>
    <script language="javascript" src="js/jquery.resizableColumns.min.js"></script>
    <script language="javascript" src="js/store.legacy.min.js"></script>
    <script language="javascript" src="js/search.js"></script>
    <script type='text/javascript'>
        // convert php fullpaths array into js array
        <?php
        $js_fullpaths = json_encode($fullpaths);
        echo "var js_fullpaths = " . $js_fullpaths . ";\n";
        ?>
        // log indexinfo time to console
        console.log('indexinfotime: <?php echo $indexinfotime; ?> ms');
    </script>
</body>

</html>