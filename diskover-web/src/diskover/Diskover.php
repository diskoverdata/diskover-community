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

session_start();
use Elasticsearch\ClientBuilder;
use Elasticsearch\Common\Exceptions\Missing404Exception;
error_reporting(E_ALL & ~E_WARNING & ~E_NOTICE & ~E_DEPRECATED);
require 'version.php';
require 'config_inc.php';


/* Start Globals */

$esIndex = $path = $toppath = $es_index_info = $all_index_info = $completed_indices = 
    $latest_completed_index = $fields = $indexinfo_updatetime = $index_starttimes = $es_responsetime = 
    $filter = $time = $timefield = $use_count = $show_files = $maxdepth = $sizefield = null;

// file type groups
$fileGroups_extensions = $config->FILE_TYPES;

// create ES client connection
try 
{
    $esclient = new ESClient;
    $client = $esclient->createClient();
}
catch (Exception $e) 
{
}

// Set d3 vars
setd3Vars();

// Pages to not redirect to select indices
$selectindex_noredirect = array('selectindices.php', 'settings.php', 'help.php');

// timezone
// check for env var TZ
$timezone = getenv('TZ') ?: $config->TIMEZONE;

/* End Globals */


// get/set index info
if (strpos($_SERVER['REQUEST_URI'], 'd3_data') === false && 
    strpos($_SERVER['REQUEST_URI'], 'searchkeypress.php') === false &&
    strpos($_SERVER['REQUEST_URI'], 'settings.php') === false &&
    strpos($_SERVER['REQUEST_URI'], 'settings_tests.php') === false) {
    indexInfo();
}


class ESClient
{
    public $client;

    function createClient()
    {
        // Sets clients property

        // Create ES client connection
        // check for any env vars to override config
        $hosts = array();
        $hosts[] = array(
            'host' => getenv('ES_HOST') ?: $GLOBALS['config']->ES_HOST, 'port' => getenv('ES_PORT') ?: $GLOBALS['config']->ES_PORT,
            'user' => getenv('ES_USER') ?: $GLOBALS['config']->ES_USER, 'pass' => getenv('ES_PASS') ?: $GLOBALS['config']->ES_PASS,
            'scheme' => (strtolower(getenv('ES_HTTPS')) === "true" || $GLOBALS['config']->ES_HTTPS) ? 'https' : 'http'
        );
        if (strtolower(getenv('ES_SSLVERIFICATION')) === "false" || !$GLOBALS['config']->ES_SSLVERIFICATION) {
            $client = ClientBuilder::create()->setHosts($hosts)->setSSLVerification(false)->build();
        } else {
            $client = ClientBuilder::create()->setHosts($hosts)->build();
        }
        $this->client = $client;
        return $this->client;
    }

    function getIndicesInfoCurl()
    {
        // Get index info using curl

        // fields to not display
        $field_exclusions = [
            'path',
            'total',
            'used',
            'free',
            'free_percent',
            'available',
            'available_percent',
            'start_at',
            'end_at',
            'crawl_time',
            'diskover_ver'
        ];

        $indices_curl_info = curl_es('/diskover-*?pretty');
        $indices_curl_info_data = array();
        // get the data we care about
        foreach ($indices_curl_info as $key => $val) {
            $fields = array();
            foreach ($val['mappings']['properties'] as $fieldname => $fieldtype) {
                if (!in_array($fieldname, $field_exclusions)) {
                    $fields[] = $fieldname;
                }
                // check for multi-field add add additional sub-fields fieldname.subfield
                if (array_key_exists('properties', $val['mappings']['properties'][$fieldname])) {
                    foreach ($val['mappings']['properties'][$fieldname]['properties'] as $k => $v) {
                        $field = $fieldname . '.' . $k;
                        if (!in_array($field, $field_exclusions)) {
                            $fields[] = $field;
                        }
                    }
                }
            }
            $indices_curl_info_data[$key] = [
                'uuid' => $val['settings']['index']['uuid'],
                'creation_date' => $val['settings']['index']['creation_date'],
                'fields' => $fields
            ];
        }
        return $indices_curl_info_data;
    }

    function getIndicesInfoCat()
    {
        $indices_cat_info_data = array();
        
        // Set maxindex
        $maxindex = getCookie('maxindex');
        if ($maxindex == '' || $maxindex < $GLOBALS['config']->MAX_INDEX) {
            $maxindex = $GLOBALS['config']->MAX_INDEX;
            createCookie('maxindex', $maxindex);
        }

        // Get all diskover indices from ES using cat and sort by creation date
        $params = array(
            'index' => 'diskover-*',
            's' => 'creation.date'
        );
        $indices_cat_info = $this->client->cat()->indices($params);
        // reverse the array since cat indices has the newest at the end
        $indices_cat_info = array_reverse($indices_cat_info);
        $_SESSION['total_indices'] = sizeof($indices_cat_info);
        // slice array to only limited number of index
        $indices_cat_info_limited = array_slice($indices_cat_info, 0, $maxindex);
        foreach ($indices_cat_info_limited as $i) {
            $indices_cat_info_data[$i['index']] = [
                'docs_count' => $i['docs.count'],
                'store_size' => $i['store.size']
            ];
        }
        return $indices_cat_info_data;
    }

    function refreshIndices()
    {
        // Refresh diskover indices
        $this->client->indices()->refresh(array('index' => 'diskover-*'));
    }

    function getIndexInfo()
    {
        // get index info from ES
        // only get new index info every 10 seconds
        if (isset($_GET['reloadindices']) || !isset($_SESSION['es_index_info_time']) || 
        time() - $_SESSION['es_index_info_time'] > $GLOBALS['config']->NEWINDEX_CHECKTIME) {
            if (isset($_GET['refreshindices'])) {
                $this->refreshIndices();
            }
            $indices_info_curl = $this->getIndicesInfoCurl();
            $indices_info_cat = $this->getIndicesInfoCat();
            $es_index_info = array();
            foreach ($indices_info_cat as $index => $val) {
                $val2 = $indices_info_curl[$index];
                $es_index_info[$index] = $val + $val2;
            }
            $_SESSION['es_index_info'] = $es_index_info;
            $_SESSION['es_index_info_time'] = time();
        } else {
            $es_index_info = $_SESSION['es_index_info'];
        }
        return $es_index_info;
    }

    function getTotalIndices()
    {
        // Return total number of indices
        return $_SESSION['total_indices'];
    }   
}


function indexInfo()
{
    global $esclient, $client, $timezone, $esIndex, $es_index_info, $all_index_info, $completed_indices, 
    $latest_completed_index, $fields, $indexinfo_updatetime, $index_starttimes, $index_spaceinfo, $selectindex_noredirect,
    $indexinfotime;

    $indexinfo_start = microtime(true);

    $es_index_info = $esclient->getIndexInfo();

    // Set latest index info if force reload or index session info time expired
    if (isset($_GET['reloadindices']) || isset($_POST['reloadindices']) || !isset($_SESSION['indexinfo']) ||
    (isset($_SESSION['indexinfo']) && microtime(true) - $_SESSION['indexinfo']['update_time_ms'] > $GLOBALS['config']->INDEXINFO_CACHETIME)) {

        $disabled_indices = array();
        $completed_indices = array();
        $latest_completed_index = null;
        $index_toppath = array();
        $index_starttimes = array();
        $all_index_info = array();
        $fields = array();
        $index_spaceinfo = array();

        if (!isset($_SESSION['indices_uuids'])) {
            $_SESSION['indices_uuids'] = array();
        }

        if (!isset($_SESSION['indices_doccount'])) {
            $_SESSION['indices_doccount'] = array();
        }

        foreach ($es_index_info as $key => $val) {
            // index uuid
            $uuid = $val['uuid'];

            // skip index which we already have index uuid and doc count has not changed
            if (array_key_exists($uuid, $_SESSION['indices_uuids']) &&
                $_SESSION['indices_doccount'][$key] == $val['docs_count']) {
                continue;
            } else {
                $_SESSION['indices_uuids'][$uuid] = $key;
                $_SESSION['indices_doccount'][$key] = $val['docs_count'];
                unset($_SESSION['toppath']);
            }

            $searchParams['body'] = [
                [
                    'index' => $key
                ],
                [
                    'size' => 2,
                    'query' => [
                        'query_string' => [
                            'query' => 'type:indexinfo'
                        ]
                    ],
                    'sort' => ['start_at' => 'asc']
                ],
                [
                    'index' => $key
                ],
                [
                    'size' => 1,
                    'query' => [
                        'query_string' => [
                            'query' => 'type:spaceinfo'
                        ]
                    ]
                ]
            ];

            // do multi-search and handle any errors
            try {
                $queryResponse = $client->msearch($searchParams);
            } catch (Missing404Exception $e) {
                handleError('ES error (missing 404 exception index not found): ' . $e->getMessage(), false, false, false);
                removeIndex($key, $uuid);
                continue;
            } catch (Exception $e) {
                handleError('ES error (unhandled exception): ' . $e->getMessage(), false, false, false);
                removeIndex($key, $uuid);
                continue;
            }

            // if no indexinfo docs, remove it from indices array
            if (sizeof($queryResponse['responses'][0]['hits']['hits']) == 0) {
                removeIndex($key, $uuid);
                continue;
            }

            $startcount = 0;
            $endcount = 0;
            foreach ($queryResponse['responses'][0]['hits']['hits'] as $hit) {
                $source = $hit['_source'];
                // add to index_starttimes list
                if (array_key_exists('start_at', $source)) {
                    $index_starttimes[$key][$source['path']] = $source['start_at'];
                    $startcount += 1;
                }
                if (array_key_exists('end_at', $source)) {
                    $endcount += 1;
                }
                // add to index_toppath list
                if (array_key_exists($key, $index_toppath) && !in_array($source['path'], $index_toppath[$key])) {
                    $index_toppath[$key][] = $source['path'];
                } else {
                    $index_toppath[$key] = array($source['path']);
                }
                // add to all_index_info list
                $all_index_info[$key] = [
                    'path' => $source['path'],
                    'start_at' => array_key_exists('start_at', $source) ? $source['start_at'] : $all_index_info[$key]['start_at'],
                    'end_at' => $source['end_at'],
                    'crawl_time' => $source['crawl_time'],
                    'file_count' => $source['file_count'],
                    'dir_count' => $source['dir_count'],
                    'file_size' => $source['file_size']
                ];
                $all_index_info[$key]['totals'] = [
                    'filecount' => $all_index_info[$key]['totals']['filecount'] + $source['file_count'],
                    'filesize' => $all_index_info[$key]['totals']['filesize'] + $source['file_size'],
                    'dircount' => $all_index_info[$key]['totals']['dircount'] + $source['dir_count'],
                    'crawltime' => $all_index_info[$key]['totals']['crawltime'] + $source['crawl_time']
                ];
            }

            // add to disabled_indices list if still being indexed (end_at docs less than start_at docs)
            if ($endcount < $startcount) {
                $disabled_indices[] = $key;
            }

            // Get size of index
            // convert to bytes
            $indexsize = $val['store_size'];
            if (strpos($indexsize, 'tb')) {
                $indexsize = str_replace('tb', '', $indexsize);
                $indexsize = $indexsize * 1024 * 1024 * 1024 * 1024;
            } elseif (strpos($indexsize, 'gb')) {
                $indexsize = str_replace('gb', '', $indexsize);
                $indexsize = $indexsize * 1024 * 1024 * 1024;
            } elseif (strpos($indexsize, 'mb')) {
                $indexsize = str_replace('mb', '', $indexsize);
                $indexsize = $indexsize * 1024 * 1024;
            } elseif (strpos($indexsize, 'kb')) {
                $indexsize = str_replace('kb', '', $indexsize);
                $indexsize = $indexsize * 1024;
            } else {
                $indexsize = str_replace('b', '', $indexsize);
            }
            $all_index_info[$key]['totals']['indexsize'] = $indexsize;

            // get disk space for index
            foreach ($queryResponse['responses'][1]['hits']['hits'] as $hit) {
                $index_spaceinfo[$key][$hit['_source']['path']] = $hit['_source'];
            }

            // add all fields from index mappings to fields_all
            foreach ($val['fields'] as $field) {
                if (!in_array($field, $fields)) {
                    $fields[] = $field;
                }
            }
        }

        // get all latest completed indices based on index's top paths
        foreach ($all_index_info as $key => $val) {
            if (!in_array($key, $disabled_indices)) {
                if (is_null($latest_completed_index)) {
                    $latest_completed_index = $key;
                }
                $completed_indices[] = $key;
            }
        }

        // add any addtional fields which are not found in mappings
        if (!isset($_SESSION['indexinfo']['fields'])) {
            $fields[] = 'name.text';
            $fields[] = 'parent_path.text';
        }
        // sort fields
        asort($fields);

        // merge existing session index info with new index info
        if (isset($_SESSION['indexinfo'])) {
            $all_index_info = array_merge($_SESSION['indexinfo']['all_index_info'], $all_index_info);
            $completed_indices = array_merge($_SESSION['indexinfo']['completed_indices'], $completed_indices);
            // remove any duplicate indices
            $completed_indices = array_unique($completed_indices);
            $latest_completed_index = (!is_null($latest_completed_index)) ? $latest_completed_index : $_SESSION['indexinfo']['latest_completed_index'];
            $fields = array_merge($_SESSION['indexinfo']['fields'], $fields);
            // remove any duplicate fields
            $fields = array_unique($fields);
            $index_starttimes = array_merge($_SESSION['indexinfo']['starttimes'], $index_starttimes);
            $index_spaceinfo = array_merge($_SESSION['indexinfo']['spaceinfo'], $index_spaceinfo);
        }

        $_SESSION['indexinfo'] = array(
            'update_time_ms' => microtime(true),
            'all_index_info' => $all_index_info,
            'completed_indices' => $completed_indices,
            'latest_completed_index' => $latest_completed_index,
            'fields' => $fields,
            'starttimes' => $index_starttimes,
            'spaceinfo' => $index_spaceinfo
        );
        $indexinfo_updatetime = $_SESSION['indexinfo']['update_time'] = new DateTime("now", new DateTimeZone($timezone));
    } else {
        $all_index_info = $_SESSION['indexinfo']['all_index_info'];
        $completed_indices = $_SESSION['indexinfo']['completed_indices'];
        $latest_completed_index = $_SESSION['indexinfo']['latest_completed_index'];
        $fields = $_SESSION['indexinfo']['fields'];
        $index_starttimes = $_SESSION['indexinfo']['starttimes'];
        $indexinfo_updatetime = $_SESSION['indexinfo']['update_time'];
        $index_spaceinfo = $_SESSION['indexinfo']['spaceinfo'];
    }

    $indexinfotime = (microtime(true) - $indexinfo_start) * 1000;

    $esIndex_cookie = getCookie('index');

    // check for index in url
    if (isset($_GET['index']) && $_GET['index'] != "") {
        $esIndex = $_GET['index'];
        createCookie('index', $esIndex);
    } else {
        $esIndex = $esIndex_cookie;
        // redirect to select indices page if esIndex is empty
        if (empty($esIndex) && !in_array(basename($_SERVER['PHP_SELF']), $selectindex_noredirect)) {
            header("location:selectindices.php?noindex");
            exit();
        }
    }

    // check if user changed index in url params and delete path cookies/session vars and reload the page
    if ($esIndex_cookie != "" && $esIndex_cookie != $esIndex) {
        deleteCookie('index');
        clearPaths();
        // set usecache to false (flush chart/file tree cache)
        createCookie('usecache', 0);
        $query = $_GET;
        $query['index'] = $esIndex;
        $query['q'] = "";
        $query['path'] = "";
        $query_result = http_build_query($query);
        $url = $_SERVER['PHP_SELF'] . "?" . $query_result;
        // reload page
        header("location:" . $url);
        exit();
    }

    notifyNewIndex();

    checkIndices();

    setPaths();
}


// handle errors
function handleError($e, $redirect = true, $ajax = false, $throwexception = false) {
    if (strpos($_SERVER['REQUEST_URI'], 'settings.php') || 
        strpos($_SERVER['REQUEST_URI'], 'settings_tests.php')) {
        return;
    }
    // Log error
    error_log(" Error: " . $e . " ");
    if ($ajax) {
        header('HTTP/1.1 500 Internal Server Error');
        header('Content-Type: application/json; charset=UTF-8');
        die(json_encode(array('message' => 'Error: ' . $e)));
    }
    if ($redirect) {
        // set error cookie to expire 1 hour
        setCookie('error', $e, time()+3600, "/");
        // redirect to error page
        if (strpos($_SERVER['REQUEST_URI'], 'tasks/') !== false) {
            header('Location: ../error.php');
        } else {
            header('Location: error.php');
        }
        exit();   
    }
    if ($throwexception) {
        // throw exception
        throw new Exception($e);
    }
}


// set analytics vars
function setd3Vars() {
    global $filter, $time, $timefield, $use_count, $show_files, $maxdepth, $sizefield;

    $filter = 1;
    $time = 0; // time field filter
    $timefield = 'mtime'; // time field to use
    // get use_count
    $use_count = 0;
    // get show_files
    $show_files = 0;
    $maxdepth = 2;
    // don't check if same as size_field in config, setting to override this on settings page
    $sizefield = getCookie('sizefield'); // size field to use
    if ($sizefield === "") {
        $sizefield = $GLOBALS['config']->SIZE_FIELD;
        createCookie('sizefield', $sizefield);
    }
}


// Sets imporant path and path related variables
function setPaths()
{
    global $esIndex, $path, $toppath;

    $path = (isset($_GET['path'])) ? $_GET['path'] : getCookie('path');

    // check if no path grab from session and then if still can't find grab from ES
    if (empty($path)) {
        $path = $_SESSION['rootpath'];
        if (empty($path)) {
            // grab path from es
            $path = get_es_path($esIndex, 1);
            $_SESSION['rootpath'] = $path;
            createCookie('rootpath', $path);
            createCookie('parentpath', getParentDir($path));
        }
    }
    // remove any trailing slash (unless root)
    if ($path !== "/") {
        $path = rtrim($path, '/');
    }
    
    $toppath = $_SESSION['toppath'];
    if (empty($toppath)) {
        // grab path from es
        $p = get_es_path($esIndex, 1);
        if ($p !== "/") {
            $p = rtrim($p, '/');
        }
        $toppath = $p;
        // set top paths session var
        $_SESSION['toppath'] = $toppath;
    }

    setRootPath($path);
}


// finds and sets root path session/cookies from path
function setRootPath($p) {
    global $path;
    
    $rootpath = getRootPath($p);
    if (!is_null($rootpath)) {
        $_SESSION['rootpath'] = $rootpath;
        createCookie('rootpath', $rootpath);
        createCookie('path', $p);
        createCookie('parentpath', getParentDir($p));
        $path = $p;
    }
}


function getRootPath($p)
{
    if ($p == $_SESSION['toppath']) return $p;
    $p = getDirName($p);
    if ($p == '/') return $p;
    if ($p != '' && $p != '.') {
        return getRootPath($p);
    }
    return null;
}


// return parent directory path and handle Windows backslash
function getDirName($path)
{
    $p = dirname($path);
    if ($p == '/' || $p == '\\') {
        return '/';
    }
    return $p;
}


// remove index from globals and session vars
function removeIndex($index, $uuid = null)
{
    global $all_index_info, $completed_indices;

    if (is_null($uuid)) {
        $uuid = array_search($index, $_SESSION['indices_uuids']);
    }
    unset($_SESSION['indices_uuids'][$uuid]);
    unset($_SESSION['indices_doccount'][$index]);
    unset($_SESSION['indexinfo']['all_index_info'][$index]);
    if (!is_null($_SESSION['indexinfo']['completed_indices']) && 
        $k = array_search($index, $_SESSION['indexinfo']['completed_indices'])) {
        unset($_SESSION['indexinfo']['completed_indices'][$k]);
    }
    if (!is_null($completed_indices) && $k = array_search($index, $completed_indices)) {
        unset($completed_indices[$k]);
    }
    if (!is_null($all_index_info) && $k = array_search($index, $all_index_info)) {
        unset($all_index_info[$k]);
    }
}


// check if selected index still exist and hasn't been re-indexed
// re-indexed will have a new uuid number
function checkIndices()
{
    global $client, $esIndex, $completed_indices, $es_index_info;

    $indices_missing = $indices_changed = false;

    foreach ($_SESSION['indices_uuids'] as $uuid => $index) {
        if ($index === $esIndex) {
            try {
                $exists = $client->indices()->exists(array('index' => $index));
            } catch (Exception $e) {
                handleError('ES error: ' . $e->getMessage(), false, false, false);
            }
            if (!$exists) {
                removeIndex($index, $uuid);
                handleError('Index ' . $index . ' does not exist', false, false, false);
                $indices_missing = true;
            }
            // check uuid hasn't changed (from re-index)
            elseif ($uuid !== $es_index_info[$index]['uuid']) {
                removeIndex($index, $uuid);
                handleError('Index ' . $index . ' uuid changed', false, false, false);
                $indices_changed = true;
            }
        }
    }

    // remove inddex info from session if there are no completed indices and display error to user
    if (empty($completed_indices)) {
        unset($_SESSION['indexinfo']);
        unset($_SESSION['indices_uuids']);
        unset($_SESSION['indices_doccount']);
        $errmsg = "No completed indices found in Elasticsearch. Run a crawl and after it finishes reload select indices page.";
        handleError($errmsg);
    }

    // if any indices missing or changed, display error to user
    if ($indices_missing || $indices_changed) {
        deleteCookie('index');
        clearPaths();
        createCookie('usecache', 0);
        if ($indices_missing) {
            $errmsg = "Selected indices are no longer available. Please select a different index.";
        } else {
            $errmsg = "Selected indices have changed. Please select a different index.";
        }
        handleError($errmsg);
    }
}


// renove path cookies and session vars
function clearPaths() {
    deleteCookie('path');
    deleteCookie('rootpath');
    deleteCookie('parentpath');
    unset($_SESSION['rootpath']);
    unset($_SESSION['toppath']);
}


// Notify if there is a new index
function notifyNewIndex()
{
    global $latest_completed_index;

    // check if we should notify that there is a newer index
    if ((getCookie('uselatestindices') == "" || getCookie('uselatestindices') == 0) &&
        getCookie('notifynewindex') == 1 && in_array($latest_completed_index, explode(',', getCookie('index'))) === false
    ) {
        if (getCookie('newindexnotification_hide') !== $latest_completed_index) {
            createCookie('newindexnotification', 1);
        } else {
            createCookie('newindexnotification', 0);
        }
    } else {
        createCookie('newindexnotification', 0);
    }
}


function get_es_path($index, $numofpaths)
{
    /* try to get a top level path from ES index
    if there are multiple paths, return them all, 
    don't return if the path is still being indexed */
    global $client;

    $searchParams['body'] = [];

    // Setup search query
    $searchParams['index'] = $index;

    $searchParams['body'] = [
        'size' => $numofpaths,
        'query' => [
            'match' => ['type' => 'indexinfo']
        ]
    ];

    // Send search query to Elasticsearch and get results
    try {
        $queryResponse = $client->search($searchParams);
    } catch (Missing404Exception $e) {
        deleteCookie('index');
        clearPaths();
        handleError("Selected indices are no longer available. Please select a different index.");
    } catch (Exception $e) {
        handleError('ES error: ' . $e->getMessage(), true);
    }

    $results = $queryResponse['hits']['hits'];

    if (sizeof($results) > 1) {
        $paths = [];
        foreach ($results as $res) {
            if (!in_array($res['_source']['path'], $paths)) {
                if ($res['_source']['end_at']) {
                    $paths[] = $res['_source']['path'];
                }
            }
        }
        return $paths;
    } else {
        $path = $results[0]['_source']['path'];
        return $path;
    }
}


// return time in ES format
function gettime($time)
{
    // default 0 days time filter
    if (empty($time) || $time === "now" || $time === 0) {
        $time = 'now/m';
    } elseif ($time === "today") {
        $time = 'now/m';
    } elseif ($time === "tomorrow") {
        $time = 'now/m+1d/d';
    } elseif ($time === "yesterday") {
        $time = 'now/m-1d/d';
    } elseif ($time === "1d") {
        $time = 'now/m-1d/d';
    } elseif ($time === "1w") {
        $time = 'now/m-1w/d';
    } elseif ($time === "2w") {
        $time = 'now/m-2w/d';
    } elseif ($time === "1m") {
        $time = 'now/m-1M/d';
    } elseif ($time === "2m") {
        $time = 'now/m-2M/d';
    } elseif ($time === "3m") {
        $time = 'now/m-3M/d';
    } elseif ($time === "6m") {
        $time = 'now/m-6M/d';
    } elseif ($time === "1y") {
        $time = 'now/m-1y/d';
    } elseif ($time === "2y") {
        $time = 'now/m-2y/d';
    } elseif ($time === "3y") {
        $time = 'now/m-3y/d';
    } elseif ($time === "5y") {
        $time = 'now/m-5y/d';
    } elseif ($time === "10y") {
        $time = 'now/m-10y/d';
    }
    return $time;
}

// update url param with new value and return url
function build_url($param, $val)
{
    parse_str($_SERVER['QUERY_STRING'], $queries);
    // defaults
    $queries['index'] = isset($_GET['index']) ? $_GET['index'] : getCookie('index');
    $queries['index2'] = isset($_GET['index2']) ? $_GET['index2'] : getCookie('index2');
    $queries['path'] = isset($_GET['path']) ? $_GET['path'] : getCookie('path');
    // update q param (es query) if on search results page
    if (basename($_SERVER['PHP_SELF']) == 'search.php' && $param == 'path') {
        $queries['q'] = 'parent_path:' . escape_chars($val);
    } else {
        $queries['filter'] = isset($_GET['filter']) ? $_GET['filter'] : getCookie('filter');
        $queries['time'] = isset($_GET['time']) ? $_GET['time'] : getCookie('time');
        $queries['use_count'] = isset($_GET['use_count']) ? $_GET['use_count'] : getCookie('use_count');
        $queries['show_files'] = isset($_GET['show_files']) ? $_GET['show_files'] : getCookie('show_files');
    }
    // set new param
    $queries[$param] = $val;
    $q = http_build_query($queries, '', '&', PHP_QUERY_RFC3986);
    $url = $_SERVER['PHP_SELF'] . "?" . $q;
    return $url;
}

// human readable file size format function
function formatBytes($bytes, $precision = 1)
{
    if ($bytes == 0) {
        return "0 Bytes";
    }
    if (getCookie('filesizebase10') == '1') {
        $basen = 1000;
    } else {
        $basen = 1024;
    }
    $precision_cookie = getCookie('filesizedec');
    if ($precision_cookie != '') {
        $precision = $precision_cookie;
    }
    $base = log($bytes) / log($basen);
    $suffix = array("Bytes", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")[floor($base)];

    return round(pow($basen, $base - floor($base)), $precision) . " " . $suffix;
}

// convert human readable file size format to bytes
function convertToBytes($num, $unit)
{
    if ($num == 0) return 0;
    if ($unit == "") return $num;
    if ($unit == "bytes") {
        return $num;
    } elseif ($unit == "KB") {
        return $num * 1024;
    } elseif ($unit == "MB") {
        return $num * 1024 * 1024;
    } elseif ($unit == "GB") {
        return $num * 1024 * 1024 * 1024;
    }
}


// cookie functions
// set default expiry time to 1 year
function createCookie($cname, $cvalue, $days = 365)
{
    $expire = time() + ($days * 24 * 60 * 60);
    setcookie($cname, $cvalue, $expire, "/");
}


function getCookie($cname)
{
    $c = (isset($_COOKIE[$cname])) ? $_COOKIE[$cname] : '';
    return $c;
}


function createCookieFromArray($cname, $cvalue, $days = 365)
{
    $expire = time() + ($days * 24 * 60 * 60);
    setcookie($cname, json_encode($cvalue), $expire, "/");
}


function getCookieToArray($cname)
{
    $c = (isset($_COOKIE[$cname])) ? json_decode($_COOKIE[$cname], true) : '';
    return $c;
}


function deleteCookie($cname)
{
    setcookie($cname, "", time() - 3600);
}


// saved search query functions
function saveSearchQuery($req)
{
    if (!isset($_REQUEST['userinput']) || !$_REQUEST['userinput']) return;
    
    ($req === "") ? $req = "type:(file OR directory)" : "";
    if (getCookie('savedsearches') != "") {
        $json = getCookie('savedsearches');
        $savedsearches = json_decode(rawurldecode($json), true);
        if (sizeof($savedsearches) >= 10) {
            array_shift($savedsearches);
        }
        if (!in_array($req, $savedsearches)) {
            $savedsearches[] = $req;
        }
    } else {
        $savedsearches = array();
        $savedsearches[] = $req;
    }
    $json = rawurlencode(json_encode($savedsearches));
    createCookie('savedsearches', $json);
}


function getSavedSearchQuery()
{
    if (!isset($_SESSION['savedsearches'])) {
        return false;
    }
    $json = $_SESSION['savedsearches'];
    $savedsearches = json_decode($json, true);
    $savedsearches = array_reverse($savedsearches);
    $savedsearches = array_slice($savedsearches, 0, 10);
    return $savedsearches;
}


function changePercent($a, $b)
{
    return (($a - $b) / $b) * 100;
}


function getParentDir($p)
{
    if (strlen($p) > strlen($_SESSION['rootpath'])) {
        return getDirName($p);
    } else {
        return $_SESSION['rootpath'];
    }
}


function secondsToTime($seconds)
{
    $seconds = (int) $seconds;
    $dtF = new \DateTime('@0');
    $dtT = new \DateTime("@$seconds");
    if ($seconds < 60) {
        $time = $dtF->diff($dtT)->format('%Ss');
    } elseif ($seconds < 3600) {
        $time = $dtF->diff($dtT)->format('%Im:%Ss');
    } elseif ($seconds < 86400) {
        $time = $dtF->diff($dtT)->format('%Hh:%Im:%Ss');
    } else {
        $time = $dtF->diff($dtT)->format('%ad:%Hh:%Im:%Ss');
    }
    return $time;
}

// convert utc iso timestamp to local time
function utcTimeToLocal($date)
{
    global $timezone;
    
    if ($date == null) {
        return "-";
    }
    if (getCookie('localtime') == "" || getCookie('localtime') == "0") {
        return $date;
    }
    $l10nDate = new DateTime($date, new DateTimeZone('UTC'));
    $l10nDate->setTimeZone(new DateTimeZone($timezone));
    return $l10nDate->format('Y-m-d H:i:s');
}

// get and change url variable for sorting search results table
function sortURL($sort)
{
    $query = $_GET;
    $sortorder = ['asc', 'desc'];
    $sortorder_icons = ['fas fa-sort-up', 'fas fa-sort-down'];

    $arrows = "";
    foreach ($sortorder as $key => $value) {
        # set class for sort arrow
        if ($_GET['sort'] == $sort && $_GET['sortorder'] == $value) {
            $class = 'sortarrow-' . $value . '-active';
        } elseif ($_GET['sort2'] == $sort && $_GET['sortorder2'] == $value) {
            $class = 'sortarrow2-' . $value . '-active';
        } elseif (!isset($_GET['sort']) && getCookie('sort') == $sort && getCookie('sortorder') == $value) {
            $class = 'sortarrow-' . $value . '-active';
        } elseif (!isset($_GET['sort2']) && getCookie('sort2') == $sort && getCookie('sortorder2') == $value) {
            $class = 'sortarrow2-' . $value . '-active';
        } else {
            $class = '';
        }
        # build link for arrow
        # sort 1 set, set sort 2
        if ((isset($_GET['sort']) || getCookie('sort')) && (!isset($_GET['sort2']) && !getCookie('sort2')) && ($_GET['sort'] != $sort && getCookie('sort') != $sort)) {
            $query['sort2'] = $sort;
            $query['sortorder2'] = $value;
            $query_result = http_build_query($query);
            $arrows .= "<a href=\"" . $_SERVER['PHP_SELF'] . "?" . $query_result . "\" onclick=\"setCookie('sort2', '" . $sort . "'); setCookie('sortorder2', '" . $value . "');\"><i class=\"" . $sortorder_icons[$key] . " sortarrow-" . $value . " " . $class . "\"></i></a>";
        } elseif ((isset($_GET['sort2']) || getCookie('sort2')) && (!isset($_GET['sort']) && !getCookie('sort')) && ($_GET['sort2'] != $sort && getCookie('sort2') != $sort)) {  # sort 2 set, set sort 1
            $query['sort'] = $sort;
            $query['sortorder'] = $value;
            $query_result = http_build_query($query);
            $arrows .= "<a href=\"" . $_SERVER['PHP_SELF'] . "?" . $query_result . "\" onclick=\"setCookie('sort', '" . $sort . "'); setCookie('sortorder', '" . $value . "');\"><i class=\"" . $sortorder_icons[$key] . " sortarrow-" . $value . " " . $class . "\"></i></a>";
        } elseif ((isset($_GET['sort']) || getCookie('sort')) && ($_GET['sort'] == $sort || getCookie('sort') == $sort) && ($_GET['sortorder'] != $value && getCookie('sortorder') != $value)) {
            $query['sort'] = $sort;
            $query['sortorder'] = $value;
            $query_result = http_build_query($query);
            $arrows .= "<a href=\"" . $_SERVER['PHP_SELF'] . "?" . $query_result . "\" onclick=\"setCookie('sort', '" . $sort . "'); setCookie('sortorder', '" . $value . "');\"><i class=\"" . $sortorder_icons[$key] . " sortarrow-" . $value . " " . $class . "\"></i></a>";
        } elseif ((isset($_GET['sort']) || getCookie('sort')) && ($_GET['sort'] == $sort || getCookie('sort') == $sort) && ($_GET['sortorder'] == $value || getCookie('sortorder') == $value)) {
            $query['sort'] = null;
            $query['sortorder'] = null;
            $query_result = http_build_query($query);
            $arrows .= "<a href=\"" . $_SERVER['PHP_SELF'] . "?" . $query_result . "\" onclick=\"deleteCookie('sort'); deleteCookie('sortorder');\"><i class=\"" . $sortorder_icons[$key] . " sortarrow-" . $value . " " . $class . "\"></i></a>";
        } elseif ((isset($_GET['sort2']) || getCookie('sort2')) && ($_GET['sort2'] == $sort || getCookie('sort2') == $sort) && ($_GET['sortorder2'] != $value && getCookie('sortorder2') != $value)) {
            $query['sort2'] = $sort;
            $query['sortorder2'] = $value;
            $query_result = http_build_query($query);
            $arrows .= "<a href=\"" . $_SERVER['PHP_SELF'] . "?" . $query_result . "\" onclick=\"setCookie('sort2', '" . $sort . "'); setCookie('sortorder2', '" . $value . "');\"><i class=\"" . $sortorder_icons[$key] . " sortarrow-" . $value . " " . $class . "\"></i></a>";
        } elseif ((isset($_GET['sort2']) || getCookie('sort2')) && ($_GET['sort2'] == $sort || getCookie('sort2') == $sort) && ($_GET['sortorder2'] == $value || getCookie('sortorder2') == $value)) {
            $query['sort2'] = null;
            $query['sortorder2'] = null;
            $query_result = http_build_query($query);
            $arrows .= "<a href=\"" . $_SERVER['PHP_SELF'] . "?" . $query_result . "\" onclick=\"deleteCookie('sort2'); deleteCookie('sortorder2');\"><i class=\"" . $sortorder_icons[$key] . " sortarrow-" . $value . " " . $class . "\"></i></a>";
        } else {
            $query['sort'] = $sort;
            $query['sortorder'] = $value;
            $query_result = http_build_query($query);
            $arrows .= "<a href=\"" . $_SERVER['PHP_SELF'] . "?" . $query_result . "\" onclick=\"setCookie('sort', '" . $sort . "'); setCookie('sortorder', '" . $value . "');\"><i class=\"" . $sortorder_icons[$key] . " sortarrow-" . $value . " " . $class . "\"></i></a>";
        }
    }

    return "<span class=\"sortarrow-container\">" . $arrows . "</span>";
}

// escape special characters
function escape_chars($text)
{
    $chr = '+-=&|<>!(){}[]^"~*?:\'/ ';
    return addcslashes($text, $chr);
}

// open file and return file pointer
function openFile($file, $mode) {
    try {
        if (!file_exists($file)) {
            handleError("File " . $file . " not found.", false, false, true);
        }
        $fp = fopen($file, $mode);
        if (!$fp) {
            handleError("File ".$file." open failed.", false, false, true);
        }
    } catch (Exception $e) {
        handleError("Error opening " . $file . " " . $e->getMessage(), false, false, true);
    }
    return $fp;
}

// write data to file
function writeToFile($fp, $file, $data) {
    try {
        fwrite($fp, $data);
    } catch (Exception $e) {
        handleError("Error writing to " . $file . " " . $e->getMessage(), false, false, true);
    }
}

// sort search results and set cookies for search pages
function sortSearchResults($request, $searchParams)
{
    if (!isset($request['sort']) && !isset($request['sort2']) && !getCookie("sort") && !getCookie("sort2")) {
        if (getCookie('unsorted') == 1) {
            $searchParams['body']['sort'] = [];
        } else {
            $searchParams['body']['sort'] = ['parent_path' => ['order' => 'asc'], 'name' => 'asc'];
            createCookie('sort', 'parent_path');
            createCookie('sortorder', 'asc');
            createCookie('sort2', 'name');
            createCookie('sortorder2', 'asc');
        }
    } else {
        $searchParams['body']['sort'] = [];
        $sortarr = ['sort', 'sort2'];
        $sortorderarr = ['sortorder', 'sortorder2'];
        foreach ($sortarr as $key => $value) {
            if (isset($request[$value]) && !$request[$sortorderarr[$key]]) {
                $searchParams['body']['sort'] = $request[$value];
                createCookie($value, $request[$value]);
            } elseif (isset($request[$value]) && $request[$sortorderarr[$key]]) {
                array_push($searchParams['body']['sort'], [$request[$value] => ['order' => $request[$sortorderarr[$key]]]]);
                createCookie($value, $request[$value]);
                createCookie($sortorderarr[$key], $request[$sortorderarr[$key]]);
            } elseif (getCookie($value) && !getCookie($sortorderarr[$key])) {
                $searchParams['body']['sort'] = getCookie($value);
            } elseif (getCookie($value) && getCookie($sortorderarr[$key])) {
                array_push($searchParams['body']['sort'], [getCookie($value) => ['order' => getCookie($sortorderarr[$key])]]);
            }
        }
    }
    return $searchParams;
}

// predict search request
function predict_search($q)
{
    // remove any extra white space and check for escape character and space at end to not trim off trailing space
    if (substr($q, -2) == '\ ') {
        $q = ltrim($q);
    } else {
        $q = trim($q);
    }

    $lucene = false;

    // check for escape character to use lucene quuery
    if (strpos($q, '\\') === 0) {
        // remove escape character \
        $request = ltrim($q, '\\');
        $lucene = true;
        // check for path input
    } elseif (strpos($q, '/') === 0 && strpos($q, 'parent_path') === false) {
        // trim any trailing slash unless root /
        if ($q !== "/") {
            $q = rtrim($q, '/');
        }
        // check for escaped paths
        if (strpos($q, '\/') !== false) {
            $request = $q;
        } else {
            $request = escape_chars($q);
        }
        // check for / path
        if ($q == '/') {
            $path = '/';
            setRootPath($path);
            $request = 'parent_path:\/ AND NOT name:""';
        // check for wildcard at end of path
        } elseif (preg_match('/^.*\\*$/', $request)) {
            $pathnowild = rtrim($request, '\*');
            $path = str_replace('\\', '', $pathnowild);
            setRootPath($path);
            $request = 'parent_path:' . $pathnowild . '*';
        } elseif (preg_match('/(^.*\.\w{3,4}(\.\w{2}){0,1}$)|(^.*\/\..*$)/', $request)) { // file
            $pp = rtrim(dirname($request), '\/');
            if ($pp === "") $pp = '""';
            $path = rtrim(dirname($q), '/');
            setRootPath($path);
            $request = 'parent_path:' . $pp . ' AND name:' . rtrim(basename($request), '\/');
        } else { // directory
            $pp = rtrim(dirname($request), '\/');
            if ($pp === "") $pp = '""';
            $path = str_replace('\\', '', $request);
            setRootPath($path);
            $request = '(parent_path:' . $pp  . ' AND name:' . rtrim(basename($request), '\/') . ') OR parent_path:' . $request;
        }
        // NOT es field query such as name:filename
    } elseif (preg_match('/(\w+):/i', $q) == false && !empty($q)) {
        $request = '';
        $keywords = explode(' ', $q);
        if (sizeof($keywords) === 1) {
            $request = $keywords[0];
        } else {
            $n = sizeof($keywords);
            $x = 0;
            foreach ($keywords as $keyword) {
                $request .= $keyword;
                if ($x < $n - 1) $request .= ' ';
                $x++;
            }
        }
    } else {
        $request = $q;
    }

    if (!$lucene) {
        // replace any and with AND and or with OR and not with NOT, except got lucene search
        $request = preg_replace('/ and /', ' AND ', $request);
        $request = preg_replace('/ or /', ' OR ', $request);
        $request = preg_replace('/ not /', ' NOT ', $request);
    }

    return $request;
}


// curl function to get ES data
function curl_es($url, $request = null, $return_json = true)
{
    global $es_responsetime;

    $hostname = getenv('ES_HOST') ?: $GLOBALS['config']->ES_HOST;
    $port = getenv('ES_PORT') ?: $GLOBALS['config']->ES_PORT;
    $user = getenv('ES_USER') ?: $GLOBALS['config']->ES_USER;
    $pass = getenv('ES_PASS') ?: $GLOBALS['config']->ES_PASS;
    $scheme = (strtolower(getenv('ES_HTTPS')) === "true" || $GLOBALS['config']->ES_HTTPS) ? 'https' : 'http';
    $sslverify = (strtolower(getenv('ES_SSLVERIFICATION')) === "false" || !$GLOBALS['config']->ES_SSLVERIFICATION) ? FALSE : TRUE;

    // Get cURL resource
    $curl = curl_init();
    // Set curl options
    curl_setopt($curl, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($curl, CURLOPT_CONNECTTIMEOUT, 10);
    curl_setopt($curl, CURLOPT_TIMEOUT, 30);
    if (!$sslverify) {
        curl_setopt($curl, CURLOPT_SSL_VERIFYPEER, false);
        curl_setopt($curl, CURLOPT_SSL_VERIFYHOST, false);
        curl_setopt($curl, CURLOPT_SSL_VERIFYSTATUS, false);
    }
    if ($request === "DELETE") {
        curl_setopt($curl, CURLOPT_CUSTOMREQUEST, 'DELETE');
    } elseif ($request === "POST") {
        curl_setopt($curl, CURLOPT_CUSTOMREQUEST, 'POST');
    }
    $curl_url = $scheme . '://' . $hostname . ':' . $port . $url;
    curl_setopt($curl, CURLOPT_URL, $curl_url);
    // Add user/pass if using ES auth
    if (!empty($user) && !empty($pass)) {
        curl_setopt($curl, CURLOPT_USERPWD, "$user:$pass");
        curl_setopt($curl, CURLOPT_HTTPAUTH, CURLAUTH_BASIC);
    }
    // Send the request & save response to $curlresp
    $curlresp = curl_exec($curl);
    // Get status code of curl
    $status_code = curl_getinfo($curl, CURLINFO_HTTP_CODE);
    $hostwport = $hostname . ":" . $port;
    // Handle any curl errors
    if (curl_errno($curl)) {
        if ($curlerror = curl_error($curl)) {
            $curlerror = " Error: " . $curlerror;
        } else {
            $curlerror = "";
        }
        $err = "Unable to connect to Elasticsearch host " . $hostwport . "." . $curlerror;
        handleError($err);
    } elseif ($status_code != 200) {
        $err = "Error connecting to Elasticsearch host " . $hostwport . ". Status code: " . $status_code;
        handleError($err);
    }
    // Get response time
    $info = curl_getinfo($curl);
    $es_responsetime = $info['total_time'];
    $_SESSION['es_responsetime'] = $es_responsetime;
    // Close request to clear up some resources
    curl_close($curl);
    if ($return_json) {
        $curlresp = json_decode($curlresp, true);
    }

    return $curlresp;
}


// calculate file rating
function calcFileRating($file)
{
    $date1 = date_create(date('Y-m-dTH:i:s'));
    $date2 = date_create($file['mtime']);
    $diff = date_diff($date1, $date2);
    $mtime_daysago = $diff->format('%a');
    if ($mtime_daysago >= 730) {
        $file_rating = 1;
    } elseif ($mtime_daysago < 730 && $mtime_daysago >= 365) {
        $file_rating = .75;
    } elseif ($mtime_daysago < 365 && $mtime_daysago >= 180) {
        $file_rating = .5;
    } elseif ($mtime_daysago < 180 && $mtime_daysago >= 90) {
        $file_rating = .25;
    } elseif ($mtime_daysago < 90 && $mtime_daysago >= 30) {
        $file_rating = .1;
    } else {
        $file_rating = 0;
    }
    return $file_rating;
}

// Filter chart results
function filterChartResults($searchParams)
{
    // check if filtercharts is checked in filters page
    if (getCookie('filtercharts') == 1) {
        return filterSearchResults($searchParams);
    }
    return $searchParams;
}

// Filter search results
function filterSearchResults($searchParams)
{
    if (isset($_GET['path'])) {
        $path = $_GET['path'];
        $pathinurl = true;
    } else {
        $path = getCookie('path');
        $pathinurl = false;
    }

    $savedfilters = getCookieToArray("searchfilters");

    // check if current dir only nav toggle is active
    if (getCookie('searchcurrentdironly') == 1) {
        if ($pathinurl) {
            $searchParams['body']['query']['query_string']['query'] .= " AND parent_path:" . escape_chars($path) . '*';
        } else {
            $searchParams['body']['query']['query_string']['query'] .= " AND (parent_path:" . escape_chars($path) . " OR parent_path:" . escape_chars($path) . '*)';
        }
    }

    // return if there are no saved filters
    if (!$savedfilters) return $searchParams;

    if ($savedfilters['file_size_bytes_low']) {
        switch ($savedfilters['file_size_bytes_low_unit']) {
            case "Bytes":
                $size_bytes = $savedfilters['file_size_bytes_low'];
                break;
            case "KB":
                $size_bytes = $savedfilters['file_size_bytes_low'] * 1024;
                break;
            case "MB":
                $size_bytes = $savedfilters['file_size_bytes_low'] * 1024 * 1024;
                break;
            case "GB":
                $size_bytes = $savedfilters['file_size_bytes_low'] * 1024 * 1024 * 1024;
                break;
            case "TB":
                $size_bytes = $savedfilters['file_size_bytes_low'] * 1024 * 1024 * 1024 * 1024;
                break;
        }
        $searchParams['body']['query']['query_string']['query'] .= " AND size:>=" . $size_bytes;
    }

    if ($savedfilters['file_size_bytes_high']) {
        switch ($savedfilters['file_size_bytes_high_unit']) {
            case "Bytes":
                $size_bytes = $savedfilters['file_size_bytes_high'];
                break;
            case "KB":
                $size_bytes = $savedfilters['file_size_bytes_high'] * 1024;
                break;
            case "MB":
                $size_bytes = $savedfilters['file_size_bytes_high'] * 1024 * 1024;
                break;
            case "GB":
                $size_bytes = $savedfilters['file_size_bytes_high'] * 1024 * 1024 * 1024;
                break;
            case "TB":
                $size_bytes = $savedfilters['file_size_bytes_high'] * 1024 * 1024 * 1024 * 1024;
                break;
        }
        $searchParams['body']['query']['query_string']['query'] .= " AND size:<=" . $size_bytes;
    }

    if ($savedfilters['last_mod_time_low'] || $savedfilters['last_mod_time_high']) {
        $mtime_low = ($savedfilters['last_mod_time_low']) ? $savedfilters['last_mod_time_low'] : "*";
        $mtime_high = ($savedfilters['last_mod_time_high']) ? $savedfilters['last_mod_time_high'] : "now/m";
        $searchParams['body']['query']['query_string']['query'] .= " AND mtime:[" . $mtime_low . " TO " . $mtime_high . "]";
    }

    if ($savedfilters['last_accessed_time_low'] || $savedfilters['last_accessed_time_high']) {
        $atime_low = ($savedfilters['last_accessed_time_low']) ? $savedfilters['last_accessed_time_low'] : "*";
        $atime_high = ($savedfilters['last_accessed_time_high']) ? $savedfilters['last_accessed_time_high'] : "now/m";
        $searchParams['body']['query']['query_string']['query'] .= " AND atime:[" . $atime_low . " TO " . $atime_high . "]";
    }

    if ($savedfilters['last_changed_time_low'] || $savedfilters['last_changed_time_high']) {
        $ctime_low = ($savedfilters['last_changed_time_low']) ? $savedfilters['last_changed_time_low'] : "*";
        $ctime_high = ($savedfilters['last_changed_time_high']) ? $savedfilters['last_changed_time_high'] : "now/m";
        $searchParams['body']['query']['query_string']['query'] .= " AND ctime:[" . $ctime_low . " TO " . $ctime_high . "]";
    }

    if ($savedfilters['hardlinks_low']) {
        $searchParams['body']['query']['query_string']['query'] .= " AND nlink:>= " . $savedfilters['hardlinks_low'];
    }

    if ($savedfilters['hardlinks_high']) {
        $searchParams['body']['query']['query_string']['query'] .= " AND nlink:<= " . $savedfilters['hardlinks_high'];
    }

    if ($savedfilters['owner']) {
        if ($savedfilters['owner_operator'] == 'is') {
            $searchParams['body']['query']['query_string']['query'] .= " AND owner:" . $savedfilters['owner'];
        } else {
            $searchParams['body']['query']['query_string']['query'] .= " AND NOT owner:" . $savedfilters['owner'];
        }
    }

    if ($savedfilters['group']) {
        if ($savedfilters['group_operator'] == 'is') {
            $searchParams['body']['query']['query_string']['query'] .= " AND group:" . $savedfilters['owner'];
        } else {
            $searchParams['body']['query']['query_string']['query'] .= " AND NOT group:" . $savedfilters['owner'];
        }
    }

    if ($savedfilters['extensions']) {
        $extension_str = implode(" OR ", $savedfilters['extensions']);
        if ($savedfilters['extensions_operator'] == 'is') {
            $searchParams['body']['query']['query_string']['query'] .= " AND extension:(" . $extension_str . ")";
        } else {
            $searchParams['body']['query']['query_string']['query'] .= " AND NOT extension:(" . $extension_str . ")";
        }
    }

    if ($savedfilters['extension']) {
        if ($savedfilters['extension_operator'] == 'is') {
            $searchParams['body']['query']['query_string']['query'] .= " AND extension:" . $savedfilters['extension'];
        } else {
            $searchParams['body']['query']['query_string']['query'] .= " AND NOT extension:" . $savedfilters['extension'];
        }
    }

    if ($savedfilters['filetype']) {
        $extensions = array();
        foreach ($savedfilters['filetype'] as $filetype) {
            foreach ($GLOBALS['config']->FILE_TYPES[$filetype] as $ext) {
                $extensions[] = $ext;
            }
        }
        $extension_str = implode(" OR ", $extensions);
        if ($savedfilters['filetype_operator'] == 'is') {
            $searchParams['body']['query']['query_string']['query'] .= " AND extension:(" . $extension_str . ")";
        } else {
            $searchParams['body']['query']['query_string']['query'] .= " AND NOT extension:(" . $extension_str . ")";
        }
    }

    if ($savedfilters['otherfields'] && $savedfilters['otherfields_input']) {
        switch ($savedfilters['otherfields_operator']) {
            case 'contains':
                $searchParams['body']['query']['query_string']['query'] .= " AND " . $savedfilters['otherfields'] . ":*" . $savedfilters['otherfields_input'] . "*";
                break;
            case 'notcontains':
                $searchParams['body']['query']['query_string']['query'] .= " AND NOT " . $savedfilters['otherfields'] . ":*" . $savedfilters['otherfields_input'] . "*";
                break;
            case 'is':
                $searchParams['body']['query']['query_string']['query'] .= " AND " . $savedfilters['otherfields'] . ":" . $savedfilters['otherfields_input'];
                break;
            case 'isnot':
                $searchParams['body']['query']['query_string']['query'] .= " AND NOT " . $savedfilters['otherfields'] . ":" . $savedfilters['otherfields_input'];
                break;
            case '>':
                $searchParams['body']['query']['query_string']['query'] .= " AND " . $savedfilters['otherfields'] . ":>" . $savedfilters['otherfields_input'];
                break;
            case '>=':
                $searchParams['body']['query']['query_string']['query'] .= " AND " . $savedfilters['otherfields'] . ":>=" . $savedfilters['otherfields_input'];
                break;
            case '<':
                $searchParams['body']['query']['query_string']['query'] .= " AND " . $savedfilters['otherfields'] . ":<" . $savedfilters['otherfields_input'];
                break;
            case '<=':
                $searchParams['body']['query']['query_string']['query'] .= " AND " . $savedfilters['otherfields'] . ":<=" . $savedfilters['otherfields_input'];
                break;
            case 'regexp':
                $searchParams['body']['query']['query_string']['query'] .= " AND " . $savedfilters['otherfields'] . ":/" . $savedfilters['otherfields_input'] . "/";
                break;
        }
    }

    if ($savedfilters['nofilterdirs'] == "on") {
        $searchParams['body']['query']['query_string']['query'] = "(" . $searchParams['body']['query']['query_string']['query'] . ") OR (parent_path:" . escape_chars($path) . " AND type:directory)";
    }

    return $searchParams;
}

// reset search sort order and reload page
function resetSort($reason)
{
    createCookie('sort', 'parent_path');
    createCookie('sortorder', 'asc');
    createCookie('sort2', 'name');
    createCookie('sortorder2', 'asc');
    $_SESSION['resetsortreason'] = $reason;
    $query = $_GET;
    $query['sort'] = 'parent_path';
    $query['sortorder'] = 'asc';
    $query_result = http_build_query($query);
    header('Location: ' . $_SERVER['PHP_SELF'] . '?' . $query_result);
    exit;
}
