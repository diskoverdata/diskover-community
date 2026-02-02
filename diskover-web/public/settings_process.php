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

// diskover-web community edition (ce) settings page forms processing

namespace diskover;

require '../vendor/autoload.php';

use diskover\ConfigDatabase;

// Load database and get config settings.
$db = new ConfigDatabase();
$db->connect();

$errors = [];
$data = [];

// form validation check
if ($_POST['formname'] === 'elasticsearchform') {
    if (empty($_POST['ES_HOST'])) {
        $errors['ES_HOST'] = 'ES_HOST is required.';
    }
    
    if (empty($_POST['ES_PORT'])) {
        $errors['ES_PORT'] = 'ES_PORT is required.';
    }
    
    if (empty($_POST['ES_HTTPS'])) {
        $errors['ES_HTTPS'] = 'ES_HTTPS is required.';
    } elseif ($_POST['ES_HTTPS'] !== 'true' && $_POST['ES_HTTPS'] !== 'false') {
        $errors['ES_HTTPS'] = 'ES_HTTPS must be set to true or false.';
    }
    
    if (empty($_POST['ES_SSLVERIFICATION'])) {
        $errors['ES_SSLVERIFICATION'] = 'ES_SSLVERIFICATION is required.';
    } elseif ($_POST['ES_SSLVERIFICATION'] !== 'true' && $_POST['ES_SSLVERIFICATION'] !== 'false') {
        $errors['ES_SSLVERIFICATION'] = 'ES_SSLVERIFICATION must be set to true or false.';
    }

    if (empty($_POST['ES_HTTPCOMPRESS'])) {
        $errors['ES_HTTPCOMPRESS'] = 'ES_HTTPCOMPRESS is required.';
    } elseif ($_POST['ES_HTTPCOMPRESS'] !== 'true' && $_POST['ES_HTTPCOMPRESS'] !== 'false') {
        $errors['ES_HTTPCOMPRESS'] = 'ES_HTTPCOMPRESS must be set to true or false.';
    }
} elseif ($_POST['formname'] === 'webotherform') {
    if (empty($_POST['TIMEZONE'])) {
        $errors['TIMEZONE'] = 'TIMEZONE is required.';
    }
    
    if (empty($_POST['LOGIN_REQUIRED'])) {
        $errors['LOGIN_REQUIRED'] = 'LOGIN_REQUIRED is required.';
    } elseif ($_POST['LOGIN_REQUIRED'] !== 'true' && $_POST['LOGIN_REQUIRED'] !== 'false') {
        $errors['LOGIN_REQUIRED'] = 'LOGIN_REQUIRED must be set to true or false.';
    }
    
    if (empty($_POST['SEARCH_RESULTS'])) {
        $errors['SEARCH_RESULTS'] = 'SEARCH_RESULTS is required.';
    } elseif (!is_numeric($_POST['SEARCH_RESULTS']) || $_POST['SEARCH_RESULTS'] < 10 || $_POST['SEARCH_RESULTS'] > 1000) {
        $errors['SEARCH_RESULTS'] = 'SEARCH_RESULTS must be set to a number between 10 and 1000.';
    }

    if (empty($_POST['SIZE_FIELD'])) {
        $errors['SIZE_FIELD'] = 'SIZE_FIELD is required.';
    } elseif ($_POST['SIZE_FIELD'] !== 'size' && $_POST['SIZE_FIELD'] !== 'size_du') {
        $errors['SIZE_FIELD'] = 'SIZE_FIELD must be set to size or size_du.';
    }

    if (empty($_POST['FILE_TYPES'])) {
        $errors['FILE_TYPES'] = 'FILE_TYPES is required.';
    }

    if (empty($_POST['MAX_INDEX'])) {
        $errors['MAX_INDEX'] = 'MAX_INDEX is required.';
    } elseif (!is_numeric($_POST['MAX_INDEX'])) {
        $errors['MAX_INDEX'] = 'MAX_INDEX must be set to a number.';
    }

    if (empty($_POST['INDEXINFO_CACHETIME'])) {
        $errors['INDEXINFO_CACHETIME'] = 'INDEXINFO_CACHETIME is required.';
    } elseif (!is_numeric($_POST['INDEXINFO_CACHETIME'])) {
        $errors['INDEXINFO_CACHETIME'] = 'INDEXINFO_CACHETIME must be set to a number.';
    }

    if (empty($_POST['NEWINDEX_CHECKTIME'])) {
        $errors['NEWINDEX_CHECKTIME'] = 'NEWINDEX_CHECKTIME is required.';
    } elseif (!is_numeric($_POST['NEWINDEX_CHECKTIME'])) {
        $errors['NEWINDEX_CHECKTIME'] = 'NEWINDEX_CHECKTIME must be set to a number.';
    }
} elseif ($_POST['formname'] === 'diskoverform') {
    if (empty($_POST['LOGLEVEL'])) {
        $errors['LOGLEVEL'] = 'LOGLEVEL is required.';
    } elseif (!in_array($_POST['LOGLEVEL'], ['INFO','WARN','DEBUG'])) {
        $errors['LOGLEVEL'] = 'LOGLEVEL must be set to either INFO, WARN or DEBUG.';
    }

    if (empty($_POST['LOGTOFILE'])) {
        $errors['LOGTOFILE'] = 'LOGTOFILE is required.';
    } elseif ($_POST['LOGTOFILE'] !== 'true' && $_POST['LOGTOFILE'] !== 'false') {
        $errors['LOGTOFILE'] = 'LOGTOFILE must be set to true or false.';
    }

    if (empty($_POST['LOGDIRECTORY'])) {
        $errors['LOGDIRECTORY'] = 'LOGDIRECTORY is required.';
    }

    if (!empty($_POST['MAXTHREADS']) && !is_numeric($_POST['MAXTHREADS'])) {
        $errors['MAXTHREADS'] = 'MAXTHREADS must be set to a number or empty.';
    }

    if (empty($_POST['INDEXTHREADS'])) {
        $errors['INDEXTHREADS'] = 'INDEXTHREADS is required.';
    } elseif (!is_numeric($_POST['INDEXTHREADS'])) {
        $errors['INDEXTHREADS'] = 'INDEXTHREADS must be set to a number.';
    }

    if (empty($_POST['BLOCKSIZE'])) {
        $errors['BLOCKSIZE'] = 'BLOCKSIZE is required.';
    } elseif (!is_numeric($_POST['BLOCKSIZE'])) {
        $errors['BLOCKSIZE'] = 'BLOCKSIZE must be set to a number.';
    }

    if (empty($_POST['EXCLUDES_EMPTYFILES'])) {
        $errors['EXCLUDES_EMPTYFILES'] = 'EXCLUDES_EMPTYFILES is required.';
    } elseif ($_POST['EXCLUDES_EMPTYFILES'] !== 'true' && $_POST['EXCLUDES_EMPTYFILES'] !== 'false') {
        $errors['EXCLUDES_EMPTYFILES'] = 'EXCLUDES_EMPTYFILES must be set to true or false.';
    }

    if (empty($_POST['EXCLUDES_EMPTYDIRS'])) {
        $errors['EXCLUDES_EMPTYDIRS'] = 'EXCLUDES_EMPTYDIRS is required.';
    } elseif ($_POST['EXCLUDES_EMPTYDIRS'] !== 'true' && $_POST['EXCLUDES_EMPTYDIRS'] !== 'false') {
        $errors['EXCLUDES_EMPTYDIRS'] = 'EXCLUDES_EMPTYDIRS must be set to true or false.';
    }

    if (empty($_POST['EXCLUDES_MINFILESIZE'])) {
        $errors['EXCLUDES_MINFILESIZE'] = 'EXCLUDES_MINFILESIZE is required.';
    } elseif (!is_numeric($_POST['EXCLUDES_MINFILESIZE'])) {
        $errors['EXCLUDES_MINFILESIZE'] = 'EXCLUDES_MINFILESIZE must be set to a number.';
    }

    if (empty($_POST['EXCLUDES_CHECKFILETIMES'])) {
        $errors['EXCLUDES_CHECKFILETIMES'] = 'EXCLUDES_CHECKFILETIMES is required.';
    } elseif ($_POST['EXCLUDES_CHECKFILETIMES'] !== 'true' && $_POST['EXCLUDES_CHECKFILETIMES'] !== 'false') {
        $errors['EXCLUDES_CHECKFILETIMES'] = 'EXCLUDES_CHECKFILETIMES must be set to true or false.';
    }

    if (is_null($_POST['EXCLUDES_MINMTIME'])) {
        $errors['EXCLUDES_MINMTIME'] = 'EXCLUDES_MINMTIME is required.';
    } elseif (!is_numeric($_POST['EXCLUDES_MINMTIME'])) {
        $errors['EXCLUDES_MINMTIME'] = 'EXCLUDES_MINMTIME must be set to a number.';
    }

    if (is_null($_POST['EXCLUDES_MAXMTIME'])) {
        $errors['EXCLUDES_MAXMTIME'] = 'EXCLUDES_MAXMTIME is required.';
    } elseif (!is_numeric($_POST['EXCLUDES_MAXMTIME'])) {
        $errors['EXCLUDES_MAXMTIME'] = 'EXCLUDES_MAXMTIME must be set to a number.';
    }

    if (is_null($_POST['EXCLUDES_MINCTIME'])) {
        $errors['EXCLUDES_MINCTIME'] = 'EXCLUDES_MINCTIME is required.';
    } elseif (!is_numeric($_POST['EXCLUDES_MINCTIME'])) {
        $errors['EXCLUDES_MINCTIME'] = 'EXCLUDES_MINCTIME must be set to a number.';
    }

    if (is_null($_POST['EXCLUDES_MAXCTIME'])) {
        $errors['EXCLUDES_MAXCTIME'] = 'EXCLUDES_MAXCTIME is required.';
    } elseif (!is_numeric($_POST['EXCLUDES_MAXCTIME'])) {
        $errors['EXCLUDES_MAXCTIME'] = 'EXCLUDES_MAXCTIME must be set to a number.';
    }

    if (is_null($_POST['EXCLUDES_MINATIME'])) {
        $errors['EXCLUDES_MINATIME'] = 'EXCLUDES_MINATIME is required.';
    } elseif (!is_numeric($_POST['EXCLUDES_MINATIME'])) {
        $errors['EXCLUDES_MINATIME'] = 'EXCLUDES_MINATIME must be set to a number.';
    }

    if (is_null($_POST['EXCLUDES_MAXATIME'])) {
        $errors['EXCLUDES_MAXATIME'] = 'EXCLUDES_MAXATIME is required.';
    } elseif (!is_numeric($_POST['EXCLUDES_MAXATIME'])) {
        $errors['EXCLUDES_MAXATIME'] = 'EXCLUDES_MAXATIME must be set to a number.';
    }

    if (empty($_POST['OWNERSGROUPS_UIDGIDONLY'])) {
        $errors['OWNERSGROUPS_UIDGIDONLY'] = 'OWNERSGROUPS_UIDGIDONLY is required.';
    } elseif ($_POST['OWNERSGROUPS_UIDGIDONLY'] !== 'true' && $_POST['OWNERSGROUPS_UIDGIDONLY'] !== 'false') {
        $errors['OWNERSGROUPS_UIDGIDONLY'] = 'OWNERSGROUPS_UIDGIDONLY must be set to true or false.';
    }

    if (empty($_POST['OWNERSGROUPS_DOMAIN'])) {
        $errors['OWNERSGROUPS_DOMAIN'] = 'OWNERSGROUPS_DOMAIN is required.';
    } elseif ($_POST['OWNERSGROUPS_DOMAIN'] !== 'true' && $_POST['OWNERSGROUPS_DOMAIN'] !== 'false') {
        $errors['OWNERSGROUPS_DOMAIN'] = 'OWNERSGROUPS_DOMAIN must be set to true or false.';
    }

    if (empty($_POST['OWNERSGROUPS_DOMAINSEP'])) {
        $errors['OWNERSGROUPS_DOMAINSEP'] = 'OWNERSGROUPS_DOMAINSEP is required.';
    }

    if (empty($_POST['OWNERSGROUPS_DOMAINFIRST'])) {
        $errors['OWNERSGROUPS_DOMAINFIRST'] = 'OWNERSGROUPS_DOMAINFIRST is required.';
    } elseif ($_POST['OWNERSGROUPS_DOMAINFIRST'] !== 'true' && $_POST['OWNERSGROUPS_DOMAINFIRST'] !== 'false') {
        $errors['OWNERSGROUPS_DOMAINFIRST'] = 'OWNERSGROUPS_DOMAINFIRST must be set to true or false.';
    }

    if (empty($_POST['OWNERSGROUPS_KEEPDOMAIN'])) {
        $errors['OWNERSGROUPS_KEEPDOMAIN'] = 'OWNERSGROUPS_KEEPDOMAIN is required.';
    } elseif ($_POST['OWNERSGROUPS_KEEPDOMAIN'] !== 'true' && $_POST['OWNERSGROUPS_KEEPDOMAIN'] !== 'false') {
        $errors['OWNERSGROUPS_KEEPDOMAIN'] = 'OWNERSGROUPS_KEEPDOMAIN must be set to true or false.';
    }

    if (empty($_POST['REPLACEPATHS_REPLACE'])) {
        $errors['REPLACEPATHS_REPLACE'] = 'REPLACEPATHS_REPLACE is required.';
    } elseif ($_POST['REPLACEPATHS_REPLACE'] !== 'true' && $_POST['REPLACEPATHS_REPLACE'] !== 'false') {
        $errors['REPLACEPATHS_REPLACE'] = 'REPLACEPATHS_REPLACE must be set to true or false.';
    }

    if (empty($_POST['PLUGINS_ENABLE'])) {
        $errors['PLUGINS_ENABLE'] = 'PLUGINS_ENABLE is required.';
    } elseif ($_POST['PLUGINS_ENABLE'] !== 'true' && $_POST['PLUGINS_ENABLE'] !== 'false') {
        $errors['PLUGINS_ENABLE'] = 'PLUGINS_ENABLE must be set to true or false.';
    }

    if (empty($_POST['RESTORETIMES'])) {
        $errors['RESTORETIMES'] = 'RESTORETIMES is required.';
    } elseif ($_POST['RESTORETIMES'] !== 'true' && $_POST['RESTORETIMES'] !== 'false') {
        $errors['RESTORETIMES'] = 'RESTORETIMES must be set to true or false.';
    }
}

if (!empty($errors)) {
    $data['success'] = false;
    $data['errors'] = $errors;
} else {
    // update sqlite db
    foreach ($_POST as $key => $value) {
        // skip hidden field formname
        if ($key === 'formname') continue;
        // handle form input arrays
        if ($_POST['formname'] === 'webotherform') {
            if (in_array($key, ['FILE_TYPES','EXTRA_FIELDS'])) {
                $arr = array();
                foreach ($value as $k => $v) {
                    if (empty($v)) continue;
                    if (!($k & 1)) {
                        $arr[$v] = ($key === 'FILE_TYPES') ? explode(", ", $value[$k+1]) : $value[$k+1];
                    }
                }
                $db->updateConfigSetting('configweb', $key, $arr);
            } else {
                $db->updateConfigSetting('configweb', $key, $value);
            }
        } elseif ($_POST['formname'] === 'elasticsearchform') {
            $db->updateConfigSetting('configweb', $key, $value);
            $db->updateConfigSetting('configdiskover', $key, $value);
        } elseif ($_POST['formname'] === 'diskoverform') {
            if (in_array($key, ['EXCLUDES_DIRS','EXCLUDES_FILES','INCLUDES_DIRS','INCLUDES_FILES'])) {
                if (empty($value)) {
                    $arr = array();
                } else {
                    $arr = explode(",", str_replace(" ","",$value));
                }
                $db->updateConfigSetting('configdiskover', $key, $arr);
            } else {
                $db->updateConfigSetting('configdiskover', $key, $value);
            }
        }
    }
    $data['success'] = true;
    $data['message'] = 'Success!';
}

echo json_encode($data);