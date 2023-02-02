<?php
/*
diskover-web community edition (ce)
https://github.com/diskoverdata/diskover-community/
https://diskoverdata.com

Copyright 2017-2022 Diskover Data, Inc.
"Community" portion of Diskover made available under the Apache 2.0 License found here:
https://www.diskoverdata.com/apache-license/
 
All other content is subject to the Diskover Data, Inc. end user license agreement found at:
https://www.diskoverdata.com/eula-subscriptions/
  
Diskover Data products and features for all versions found here:
https://www.diskoverdata.com/solutions/

*/

error_reporting(E_ALL ^ E_NOTICE);


$savedfilters = getCookieToArray('searchfilters');
if (!$savedfilters) {
    $savedfilters = array();
    $savedfilters['doctype'] = null;
    $savedfilters['nofilterdirs'] = null;
    $savedfilters['file_size_bytes_low'] = null;
    $savedfilters['file_size_bytes_low_unit'] = null;
    $savedfilters['file_size_bytes_high'] = null;
    $savedfilters['file_size_bytes_high_unit'] = null;
    $savedfilters['last_mod_time_low'] = null;
    $savedfilters['last_mod_time_high'] = null;
    $savedfilters['last_accessed_time_low'] = null;
    $savedfilters['last_accessed_time_high'] = null;
    $savedfilters['last_changed_time_low'] = null;
    $savedfilters['last_changed_time_high'] = null;
    $savedfilters['hardlinks_low'] = null;
    $savedfilters['hardlinks_high'] = null;
    $savedfilters['owner_operator'] = null;
    $savedfilters['owner'] = null;
    $savedfilters['group_operator'] = null;
    $savedfilters['group'] = null;
    $savedfilters['extensions_operator'] = null;
    $savedfilters['extensions'] = null;
    $savedfilters['extension_operator'] = null;
    $savedfilters['extension'] = null;
    $savedfilters['filetype'] = null;
    $savedfilters['filetype_operator'] = null;
    $savedfilters['otherfields'] = null;
    $savedfilters['otherfields_operator'] = null;
    $savedfilters['otherfields_input'] = null;
}

$filtercount = -2;
foreach ($savedfilters as $filterkey => $filterval) {
    if ($filterkey == 'doctype' && $filterval == 'all') continue;
    if ($filterval != null && !strpos($filterkey, 'operator')) $filtercount += 1;
    if ($filterkey == 'otherfields_input' && $filterval != null) $filtercount -= 1;
}

// add filter count next to nav filter button
if ($filtercount > 0) {
    echo "<script type=\"text/javascript\">
    var s = document.getElementById('filtercount');
    s.innerHTML = \"" . $filtercount . "\";
    s.className = \"label label-info\";
    </script>";
}

?>

<!-- search filters modal -->
<div class="modal fade" id="searchFilterModal" tabindex="-1" role="dialog" aria-labelledby="searchFilterModalLabel" aria-hidden="true">
    <div class="modal-dialog modal-lg">
        <div class="modal-content">
            <div class="modal-header">
                <button type="button" class="close" data-dismiss="modal" aria-hidden="true">&times;</button>
                <h4 class="modal-title">Search Filters</h4>
            </div>
            <div class="modal-body">
                <form method="POST" action="" class="form-horizontal" id="searchFiltersForm">
                    <fieldset>
                        <div class="well well-sm">
                            <div class="container">
                                <div class="form-group">
                                    <div class="row">
                                        <div class="col-xs-4">
                                            <label for="doctype">Doc type </label>
                                            <select id="doctype" name="doctype" class="form-control">
                                                <option value="" <?php echo $savedfilters['doctype'] == "" ? "selected" : ""; ?>>all</option>
                                                <option value="file" <?php echo $savedfilters['doctype'] == "file" ? "selected" : ""; ?>>file</option>
                                                <option value="directory" <?php echo $savedfilters['doctype'] == "directory" ? "selected" : ""; ?>>directory</option>
                                            </select>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="well well-sm">
                            <div class="container">
                                <div class="form-group">
                                    <div class="row">
                                        <div class="col-xs-2">
                                            <label for="file_size_bytes_low">File size (min) </label>
                                            <input name="file_size_bytes_low" id="file_size_bytes_low" value="<?php echo $savedfilters['file_size_bytes_low'] ?>" type="number" class="form-control" />
                                        </div>
                                        <div class="col-xs-2">
                                            <label>&nbsp;</label>
                                            <select class="form-control" name="file_size_bytes_low_unit" id="file_size_bytes_low_unit">
                                                <option value="Bytes" <?php echo ($savedfilters['file_size_bytes_low_unit'] == "Bytes") ? "selected" : "" ?>>Bytes</option>
                                                <option value="KB" <?php echo ($savedfilters['file_size_bytes_low_unit'] == "KB") ? "selected" : "" ?>>KB</option>
                                                <option value="MB" <?php echo ($savedfilters['file_size_bytes_low_unit'] == "MB") ? "selected" : "" ?>>MB</option>
                                                <option value="GB" <?php echo ($savedfilters['file_size_bytes_low_unit'] == "GB") ? "selected" : "" ?>>GB</option>
                                                <option value="TB" <?php echo ($savedfilters['file_size_bytes_low_unit'] == "TB") ? "selected" : "" ?>>TB</option>
                                            </select>
                                        </div>
                                        <div class="col-xs-2">
                                            <label for="file_size_bytes_high">File size (max) </label>
                                            <input name="file_size_bytes_high" id="file_size_bytes_high" value="<?php echo $savedfilters['file_size_bytes_high'] ?>" type="number" class="form-control" />
                                        </div>
                                        <div class="col-xs-2">
                                            <label>&nbsp;</label>
                                            <select class="form-control" name="file_size_bytes_high_unit" id="file_size_bytes_high_unit">
                                                <option value="Bytes" <?php echo ($savedfilters['file_size_bytes_high_unit'] == "Bytes") ? "selected" : "" ?>>Bytes</option>
                                                <option value="KB" <?php echo ($savedfilters['file_size_bytes_high_unit'] == "KB") ? "selected" : "" ?>>KB</option>
                                                <option value="MB" <?php echo ($savedfilters['file_size_bytes_high_unit'] == "MB") ? "selected" : "" ?>>MB</option>
                                                <option value="GB" <?php echo ($savedfilters['file_size_bytes_high_unit'] == "GB") ? "selected" : "" ?>>GB</option>
                                                <option value="TB" <?php echo ($savedfilters['file_size_bytes_high_unit'] == "TB") ? "selected" : "" ?>>TB</option>
                                            </select>
                                        </div>
                                    </div>
                                </div>
                                <div class="form-group">
                                    <div class="row">
                                        <div class="col-xs-4">
                                            <label for="last_mod_time_low">Last modified (from) </label>
                                            <select class="form-control" name="last_mod_time_low" id="last_mod_time_low">
                                                <option value=""></option>
                                                <option value="*" <?php echo ($savedfilters['last_mod_time_low'] == "*") ? "selected" : "" ?>>any time (*)</option>
                                                <option value="now/m-1d/d" <?php echo ($savedfilters['last_mod_time_low'] == "now/m-1d/d") ? "selected" : "" ?>>1 day ago</option>
                                                <option value="now/m-2d/d" <?php echo ($savedfilters['last_mod_time_low'] == "now/m-2d/d") ? "selected" : "" ?>>2 days ago</option>
                                                <option value="now/m-1w/d" <?php echo ($savedfilters['last_mod_time_low'] == "now/m-1w/d") ? "selected" : "" ?>>1 week ago</option>
                                                <option value="now/m-2w/d" <?php echo ($savedfilters['last_mod_time_low'] == "now/m-2w/d") ? "selected" : "" ?>>2 weeks ago</option>
                                                <option value="now/m-1M/d" <?php echo ($savedfilters['last_mod_time_low'] == "now/m-1M/d") ? "selected" : "" ?>>1 month ago</option>
                                                <option value="now/m-2M/d" <?php echo ($savedfilters['last_mod_time_low'] == "now/m-2M/d") ? "selected" : "" ?>>2 months ago</option>
                                                <option value="now/m-3M/d" <?php echo ($savedfilters['last_mod_time_low'] == "now/m-3M/d") ? "selected" : "" ?>>3 months ago</option>
                                                <option value="now/m-6M/d" <?php echo ($savedfilters['last_mod_time_low'] == "now/m-6M/d") ? "selected" : "" ?>>6 months ago</option>
                                                <option value="now/m-1y/d" <?php echo ($savedfilters['last_mod_time_low'] == "now/m-1y/d") ? "selected" : "" ?>>1 year ago</option>
                                                <option value="now/m-2y/d" <?php echo ($savedfilters['last_mod_time_low'] == "now/m-2y/d") ? "selected" : "" ?>>2 years ago</option>
                                                <option value="now/m-3y/d" <?php echo ($savedfilters['last_mod_time_low'] == "now/m-3y/d") ? "selected" : "" ?>>3 years ago</option>
                                                <option value="now/m-5y/d" <?php echo ($savedfilters['last_mod_time_low'] == "now/m-5y/d") ? "selected" : "" ?>>5 years ago</option>
                                                <option value="now/m-10y/d" <?php echo ($savedfilters['last_mod_time_low'] == "now/m-10y/d") ? "selected" : "" ?>>10 years ago</option>
                                            </select>
                                        </div>
                                        <div class="col-xs-4">
                                            <label for="last_mod_time_high">Last modified (to) </label>
                                            <select class="form-control" name="last_mod_time_high" id="last_mod_time_high">
                                                <option value=""></option>
                                                <option value="now/m" <?php echo ($savedfilters['last_mod_time_high'] == "now/m") ? "selected" : "" ?>>now</option>
                                                <option value="now/m-1d/d" <?php echo ($savedfilters['last_mod_time_high'] == "now/m-1d/d") ? "selected" : "" ?>>1 day ago</option>
                                                <option value="now/m-2d/d" <?php echo ($savedfilters['last_mod_time_high'] == "now/m-2d/d") ? "selected" : "" ?>>2 days ago</option>
                                                <option value="now/m-1w/d" <?php echo ($savedfilters['last_mod_time_high'] == "now/m-1w/d") ? "selected" : "" ?>>1 week ago</option>
                                                <option value="now/m-2w/d" <?php echo ($savedfilters['last_mod_time_high'] == "now/m-2w/d") ? "selected" : "" ?>>2 weeks ago</option>
                                                <option value="now/m-1M/d" <?php echo ($savedfilters['last_mod_time_high'] == "now/m-1M/d") ? "selected" : "" ?>>1 month ago</option>
                                                <option value="now/m-2M/d" <?php echo ($savedfilters['last_mod_time_high'] == "now/m-2M/d") ? "selected" : "" ?>>2 months ago</option>
                                                <option value="now/m-3M/d" <?php echo ($savedfilters['last_mod_time_high'] == "now/m-3M/d") ? "selected" : "" ?>>3 months ago</option>
                                                <option value="now/m-6M/d" <?php echo ($savedfilters['last_mod_time_high'] == "now/m-6M/d") ? "selected" : "" ?>>6 months ago</option>
                                                <option value="now/m-1y/d" <?php echo ($savedfilters['last_mod_time_high'] == "now/m-1y/d") ? "selected" : "" ?>>1 year ago</option>
                                                <option value="now/m-2y/d" <?php echo ($savedfilters['last_mod_time_high'] == "now/m-2y/d") ? "selected" : "" ?>>2 years ago</option>
                                                <option value="now/m-3y/d" <?php echo ($savedfilters['last_mod_time_high'] == "now/m-3y/d") ? "selected" : "" ?>>3 years ago</option>
                                                <option value="now/m-5y/d" <?php echo ($savedfilters['last_mod_time_high'] == "now/m-5y/d") ? "selected" : "" ?>>5 years ago</option>
                                                <option value="now/m-10y/d" <?php echo ($savedfilters['last_mod_time_high'] == "now/m-10y/d") ? "selected" : "" ?>>10 years ago</option>
                                            </select>
                                        </div>
                                    </div>
                                </div>
                                <div class="form-group">
                                    <div class="row">
                                        <div class="col-xs-4">
                                            <label for="last_accessed_time_low">Last accessed (from) </label>
                                            <select class="form-control" name="last_accessed_time_low" id="last_accessed_time_low">
                                                <option value=""></option>
                                                <option value="*)" <?php echo ($savedfilters['last_accessed_time_low'] == "*") ? "selected" : "" ?>>any time (*)</option>
                                                <option value="now/m-1d/d" <?php echo ($savedfilters['last_accessed_time_low'] == "now/m-1d/d") ? "selected" : "" ?>>1 day ago</option>
                                                <option value="now/m-2d/d" <?php echo ($savedfilters['last_accessed_time_low'] == "now/m-2d/d") ? "selected" : "" ?>>2 days ago</option>
                                                <option value="now/m-1w/d" <?php echo ($savedfilters['last_accessed_time_low'] == "now/m-1w/d") ? "selected" : "" ?>>1 week ago</option>
                                                <option value="now/m-2w/d" <?php echo ($savedfilters['last_accessed_time_low'] == "now/m-2w/d") ? "selected" : "" ?>>2 weeks ago</option>
                                                <option value="now/m-1M/d" <?php echo ($savedfilters['last_accessed_time_low'] == "now/m-1M/d") ? "selected" : "" ?>>1 month ago</option>
                                                <option value="now/m-2M/d" <?php echo ($savedfilters['last_accessed_time_low'] == "now/m-2M/d") ? "selected" : "" ?>>2 months ago</option>
                                                <option value="now/m-3M/d" <?php echo ($savedfilters['last_accessed_time_low'] == "now/m-3M/d") ? "selected" : "" ?>>3 months ago</option>
                                                <option value="now/m-6M/d" <?php echo ($savedfilters['last_accessed_time_low'] == "now/m-6M/d") ? "selected" : "" ?>>6 months ago</option>
                                                <option value="now/m-1y/d" <?php echo ($savedfilters['last_accessed_time_low'] == "now/m-1y/d") ? "selected" : "" ?>>1 year ago</option>
                                                <option value="now/m-2y/d" <?php echo ($savedfilters['last_accessed_time_low'] == "now/m-2y/d") ? "selected" : "" ?>>2 years ago</option>
                                                <option value="now/m-3y/d" <?php echo ($savedfilters['last_accessed_time_low'] == "now/m-3y/d") ? "selected" : "" ?>>3 years ago</option>
                                                <option value="now/m-5y/d" <?php echo ($savedfilters['last_accessed_time_low'] == "now/m-5y/d") ? "selected" : "" ?>>5 years ago</option>
                                                <option value="now/m-10y/d" <?php echo ($savedfilters['last_accessed_time_low'] == "now/m-10y/d") ? "selected" : "" ?>>10 years ago</option>
                                            </select>
                                        </div>
                                        <div class="col-xs-4">
                                            <label for="last_accessed_time_high">Last accessed (to) </label>
                                            <select class="form-control" name="last_accessed_time_high" id="last_accessed_time_high">
                                                <option value=""></option>
                                                <option value="now/m" <?php echo ($savedfilters['last_accessed_time_high'] == "now/m") ? "selected" : "" ?>>now</option>
                                                <option value="now/m-1d/d" <?php echo ($savedfilters['last_accessed_time_high'] == "now/m-1d/d") ? "selected" : "" ?>>1 day ago</option>
                                                <option value="now/m-2d/d" <?php echo ($savedfilters['last_accessed_time_high'] == "now/m-2d/d") ? "selected" : "" ?>>2 days ago</option>
                                                <option value="now/m-1w/d" <?php echo ($savedfilters['last_accessed_time_high'] == "now/m-1w/d") ? "selected" : "" ?>>1 week ago</option>
                                                <option value="now/m-2w/d" <?php echo ($savedfilters['last_accessed_time_high'] == "now/m-2w/d") ? "selected" : "" ?>>2 weeks ago</option>
                                                <option value="now/m-1M/d" <?php echo ($savedfilters['last_accessed_time_high'] == "now/m-1M/d") ? "selected" : "" ?>>1 month ago</option>
                                                <option value="now/m-2M/d" <?php echo ($savedfilters['last_accessed_time_high'] == "now/m-2M/d") ? "selected" : "" ?>>2 months ago</option>
                                                <option value="now/m-3M/d" <?php echo ($savedfilters['last_accessed_time_high'] == "now/m-3M/d") ? "selected" : "" ?>>3 months ago</option>
                                                <option value="now/m-6M/d" <?php echo ($savedfilters['last_accessed_time_high'] == "now/m-6M/d") ? "selected" : "" ?>>6 months ago</option>
                                                <option value="now/m-1y/d" <?php echo ($savedfilters['last_accessed_time_high'] == "now/m-1y/d") ? "selected" : "" ?>>1 year ago</option>
                                                <option value="now/m-2y/d" <?php echo ($savedfilters['last_accessed_time_high'] == "now/m-2y/d") ? "selected" : "" ?>>2 years ago</option>
                                                <option value="now/m-3y/d" <?php echo ($savedfilters['last_accessed_time_high'] == "now/m-3y/d") ? "selected" : "" ?>>3 years ago</option>
                                                <option value="now/m-5y/d" <?php echo ($savedfilters['last_accessed_time_high'] == "now/m-5y/d") ? "selected" : "" ?>>5 years ago</option>
                                                <option value="now/m-10y/d" <?php echo ($savedfilters['last_accessed_time_high'] == "now/m-10y/d") ? "selected" : "" ?>>10 years ago</option>
                                            </select>
                                        </div>
                                    </div>
                                </div>
                                <div class="form-group">
                                    <div class="row">
                                        <div class="col-xs-4">
                                            <label for="last_changed_time_low">Last changed (from) </label>
                                            <select class="form-control" name="last_changed_time_low" id="last_changed_time_low">
                                                <option value=""></option>
                                                <option value="*" <?php echo ($savedfilters['last_changed_time_low'] == "*") ? "selected" : "" ?>>any time (*)</option>
                                                <option value="now/m-1d/d" <?php echo ($savedfilters['last_changed_time_low'] == "now/m-1d/d") ? "selected" : "" ?>>1 day ago</option>
                                                <option value="now/m-2d/d" <?php echo ($savedfilters['last_changed_time_low'] == "now/m-2d/d") ? "selected" : "" ?>>2 days ago</option>
                                                <option value="now/m-1w/d" <?php echo ($savedfilters['last_changed_time_low'] == "now/m-1w/d") ? "selected" : "" ?>>1 week ago</option>
                                                <option value="now/m-2w/d" <?php echo ($savedfilters['last_changed_time_low'] == "now/m-2w/d") ? "selected" : "" ?>>2 weeks ago</option>
                                                <option value="now/m-1M/d" <?php echo ($savedfilters['last_changed_time_low'] == "now/m-1M/d") ? "selected" : "" ?>>1 month ago</option>
                                                <option value="now/m-2M/d" <?php echo ($savedfilters['last_changed_time_low'] == "now/m-2M/d") ? "selected" : "" ?>>2 months ago</option>
                                                <option value="now/m-3M/d" <?php echo ($savedfilters['last_changed_time_low'] == "now/m-3M/d") ? "selected" : "" ?>>3 months ago</option>
                                                <option value="now/m-6M/d" <?php echo ($savedfilters['last_changed_time_low'] == "now/m-6M/d") ? "selected" : "" ?>>6 months ago</option>
                                                <option value="now/m-1y/d" <?php echo ($savedfilters['last_changed_time_low'] == "now/m-1y/d") ? "selected" : "" ?>>1 year ago</option>
                                                <option value="now/m-2y/d" <?php echo ($savedfilters['last_changed_time_low'] == "now/m-2y/d") ? "selected" : "" ?>>2 years ago</option>
                                                <option value="now/m-3y/d" <?php echo ($savedfilters['last_changed_time_low'] == "now/m-3y/d") ? "selected" : "" ?>>3 years ago</option>
                                                <option value="now/m-5y/d" <?php echo ($savedfilters['last_changed_time_low'] == "now/m-5y/d") ? "selected" : "" ?>>5 years ago</option>
                                                <option value="now/m-10y/d" <?php echo ($savedfilters['last_changed_time_low'] == "now/m-10y/d") ? "selected" : "" ?>>10 years ago</option>
                                            </select>
                                        </div>
                                        <div class="col-xs-4">
                                            <label for="last_changed_time_high">Last changed (to) </label>
                                            <select class="form-control" name="last_changed_time_high" id="last_changed_time_high">
                                                <option value=""></option>
                                                <option value="now/m" <?php echo ($savedfilters['last_changed_time_high'] == "now/m") ? "selected" : "" ?>>now</option>
                                                <option value="now/m-1d/d" <?php echo ($savedfilters['last_changed_time_high'] == "now/m-1d/d") ? "selected" : "" ?>>1 day ago</option>
                                                <option value="now/m-2d/d" <?php echo ($savedfilters['last_changed_time_high'] == "now/m-2d/d") ? "selected" : "" ?>>2 days ago</option>
                                                <option value="now/m-1w/d" <?php echo ($savedfilters['last_changed_time_high'] == "now/m-1w/d") ? "selected" : "" ?>>1 week ago</option>
                                                <option value="now/m-2w/d" <?php echo ($savedfilters['last_changed_time_high'] == "now/m-2w/d") ? "selected" : "" ?>>2 weeks ago</option>
                                                <option value="now/m-1M/d" <?php echo ($savedfilters['last_changed_time_high'] == "now/m-1M/d") ? "selected" : "" ?>>1 month ago</option>
                                                <option value="now/m-2M/d" <?php echo ($savedfilters['last_changed_time_high'] == "now/m-2M/d") ? "selected" : "" ?>>2 months ago</option>
                                                <option value="now/m-3M/d" <?php echo ($savedfilters['last_changed_time_high'] == "now/m-3M/d") ? "selected" : "" ?>>3 months ago</option>
                                                <option value="now/m-6M/d" <?php echo ($savedfilters['last_changed_time_high'] == "now/m-6M/d") ? "selected" : "" ?>>6 months ago</option>
                                                <option value="now/m-1y/d" <?php echo ($savedfilters['last_changed_time_high'] == "now/m-1y/d") ? "selected" : "" ?>>1 year ago</option>
                                                <option value="now/m-2y/d" <?php echo ($savedfilters['last_changed_time_high'] == "now/m-2y/d") ? "selected" : "" ?>>2 years ago</option>
                                                <option value="now/m-3y/d" <?php echo ($savedfilters['last_changed_time_high'] == "now/m-3y/d") ? "selected" : "" ?>>3 years ago</option>
                                                <option value="now/m-5y/d" <?php echo ($savedfilters['last_changed_time_high'] == "now/m-5y/d") ? "selected" : "" ?>>5 years ago</option>
                                                <option value="now/m-10y/d" <?php echo ($savedfilters['last_changed_time_high'] == "now/m-10y/d") ? "selected" : "" ?>>10 years ago</option>
                                            </select>
                                        </div>
                                    </div>
                                </div>
                                <div class="form-group">
                                    <div class="row">
                                        <div class="col-xs-2">
                                            <label for="hardlinks_low">Hardlinks (min) </label>
                                            <input name="hardlinks_low" id="hardlinks_low" value="<?php echo $savedfilters['hardlinks_low'] ?>" type="number" class="form-control" />
                                        </div>
                                        <div class="col-xs-2">
                                            <label for="hardlinks_high">Hardlinks (max) </label>
                                            <input name="hardlinks_high" id="hardlinks_high" value="<?php echo $savedfilters['hardlinks_high'] ?>" type="number" class="form-control" />
                                        </div>
                                    </div>
                                </div>
                                <div class="form-group">
                                    <div class="row">
                                        <div class="col-xs-4">
                                            <label for="owner">Owner </label><br>
                                            <select class="form-control" name="owner_operator" id="owner_operator" style="width:100px; display: inline">
                                                <option value="is" <?php echo ($savedfilters['owner_operator'] == "is") ? "selected" : "" ?>>is</option>
                                                <option value="isnot" <?php echo ($savedfilters['owner_operator'] == "isnot") ? "selected" : "" ?>>is not</option>
                                            </select>
                                            <?php echo '<input name="owner" id="owner" value="' . $savedfilters['owner'] . '" class="form-control" style="width:200px; display: inline" />'; ?>
                                        </div>
                                        <div class="col-xs-4">
                                            <label for="group">Group </label><br>
                                            <select class="form-control" name="group_operator" id="group_operator" style="width:100px; display: inline">
                                                <option value="is" <?php echo ($savedfilters['group_operator'] == "is") ? "selected" : "" ?>>is</option>
                                                <option value="isnot" <?php echo ($savedfilters['group_operator'] == "isnot") ? "selected" : "" ?>>is not</option>
                                            </select>
                                            <?php echo '<input name="group" id="group" value="' . $savedfilters['group'] . '" class="form-control" style="width:200px; display: inline" />'; ?>
                                        </div>
                                    </div>
                                </div>
                                <div class="form-group">
                                    <div class="row">
                                        <div class="col-xs-8">
                                            <label for="extensions">Extensions </label><br>
                                            <select class="form-control" name="extensions_operator" id="extensions_operator" style="width:100px; display: inline">
                                                <option value="is" <?php echo ($savedfilters['extensions_operator'] == "is") ? "selected" : "" ?>>is</option>
                                                <option value="isnot" <?php echo ($savedfilters['extensions_operator'] == "isnot") ? "selected" : "" ?>>is not</option>
                                            </select>
                                            <?php
                                            if ($savedfilters['extensions']) {
                                                foreach ($savedfilters['extensions'] as $ext) {
                                                    $extlabel = ($ext === "NULL") ? "NULL (no ext)" : $ext;
                                            ?>
                                                    <input name="extensions" type="checkbox" value="<?php echo $ext ?>" checked>&nbsp;<?php echo $extlabel ?>
                                            <?php }
                                            } ?>
                                            <?php
                                            if (isset($ext_onpage)) {
                                                foreach ($ext_onpage as $ext => $ext_arr) {
                                                    if (is_array($savedfilters['extensions']) && in_array($ext, $savedfilters['extensions'])) continue;
                                                    $ext_count = $ext_arr[0];
                                                    $ext_size = $ext_arr[1];
                                                    $extlabel = ($ext === "NULL") ? "NULL (no ext)" : $ext;
                                            ?>
                                                    <label><input name="extensions" type="checkbox" value="<?php echo $ext ?>" <?php echo ($savedfilters['extensions'] && in_array($ext, $savedfilters['extensions'])) ? "checked" : "" ?>>
                                                        <?php echo $extlabel ?></label>
                                            <?php }
                                            } ?>
                                        </div>
                                    </div>
                                </div>
                                <div class="form-group">
                                    <div class="row">
                                        <div class="col-xs-6">
                                            <label for="extension_operator">Extension </label><br>
                                            <select class="form-control" name="extension_operator" id="extension_operator" style="width:100px; display: inline">
                                                <option value="is" <?php echo ($savedfilters['extension_operator'] == "is") ? "selected" : "" ?>>is</option>
                                                <option value="isnot" <?php echo ($savedfilters['extension_operator'] == "isnot") ? "selected" : "" ?>>is not</option>
                                            </select>
                                            <input name="extension" id="extension" value="<?php echo $savedfilters['extension'] ?>" type="string" class="form-control" style="width:200px; display: inline" />
                                        </div>
                                    </div>
                                </div>
                                <div class="form-group">
                                    <div class="row">
                                        <div class="col-xs-8">
                                            <label for="filetype">File type </label><br>
                                            <select class="form-control" name="filetype_operator" id="filetype_operator" style="width:100px; display: inline">
                                                <option value="is" <?php echo ($savedfilters['filetype_operator'] == "is") ? "selected" : "" ?>>is</option>
                                                <option value="isnot" <?php echo ($savedfilters['filetype_operator'] == "isnot") ? "selected" : "" ?>>is not</option>
                                            </select>
                                            <?php foreach ($config->FILE_TYPES as $type_name => $type_extensions) { ?>
                                                <label><input name="filetype" type="checkbox" value="<?php echo $type_name ?>" <?php echo ($savedfilters['filetype'] && in_array($type_name, $savedfilters['filetype'])) ? "checked" : "" ?>>
                                                        <?php echo $type_name ?></label>
                                            <?php } ?>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="well well-sm">
                            <div class="container">
                                <div class="form-group">
                                    <div class="row">
                                        <div class="col-xs-12">
                                            <label for="otherfields">Other field </label><br>
                                            <select name="otherfields" id="otherfields" class="form-control" style="width:150px; display: inline">
                                                <option value="" selected></option>
                                                <?php foreach ($fields as $key => $value) { ?>
                                                    <option value="<?php echo $value; ?>" <?php echo ($savedfilters['otherfields'] == $value) ? "selected" : "" ?>><?php echo $value; ?></option>
                                                <?php } ?>
                                            </select>
                                            <select name="otherfields_operator" id="otherfields_operator" class="form-control" style="width:150px; display: inline">
                                                <option value="contains" <?php echo ($savedfilters['otherfields_operator'] == "contains") ? "selected" : "" ?>>contains</option>
                                                <option value="notcontains" <?php echo ($savedfilters['otherfields_operator'] == "notcontains") ? "selected" : "" ?>>does not contain</option>
                                                <option value="is" <?php echo ($savedfilters['otherfields_operator'] == "is") ? "selected" : "" ?>>is</option>
                                                <option value="isnot" <?php echo ($savedfilters['otherfields_operator'] == "isnot") ? "selected" : "" ?>>is not</option>
                                                <option value=">" <?php echo ($savedfilters['otherfields_operator'] == ">") ? "selected" : "" ?>>is greater than</option>
                                                <option value=">=" <?php echo ($savedfilters['otherfields_operator'] == ">=") ? "selected" : "" ?>>is greater than or equal to</option>
                                                <option value="<" <?php echo ($savedfilters['otherfields_operator'] == "<") ? "selected" : "" ?>>is less than</option>
                                                <option value="<=" <?php echo ($savedfilters['otherfields_operator'] == "<=") ? "selected" : "" ?>>is less than or equal to</option>
                                                <option value="regexp" <?php echo ($savedfilters['otherfields_operator'] == "regexp") ? "selected" : "" ?>>regexp</option>
                                            </select>
                                            <input class="form-control" name="otherfields_input" value="<?php echo $savedfilters['otherfields_input'] ?>" id="otherfields_input" style="width:400px; display: inline"></input>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="well well-sm">
                            <div class="row">
                                <div class="col-xs-6">
                                    <label>
                                        <input name="nofilterdirs" id="nofilterdirs" type="checkbox" <?php echo ($savedfilters['nofilterdirs'] == "on") ? "checked" : "" ?>>
                                        Exclude folders</label><br>
                                        <span class="small"><i class="fas fa-info-circle"></i> Don't apply filters to directory docs</span>
                                </div>
                                <div class="col-xs-6">
                                    <label>
                                        <input name="filtercharts" id="filtercharts" type="checkbox" <?php echo (getCookie('filtercharts') == 1) ? "checked" : "" ?>>
                                        Filter charts</label><br>
                                        <span class="small"><i class="fas fa-info-circle"></i> Apply filters to charts on search results and dashboard</span>
                                </div>
                            </div>
                        </div>
                        <span class="text-primary">
                            <i class="fas fa-info-circle"></i> For OR conditions, use brackets and OR, example: (jpg OR png)<br>
                            Search filter inputs are case-sensitive
                        </span>
                    </fieldset>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-default" data-dismiss="modal">Close</button>
                <button type="button" class="btn btn-default" onclick="saveSearchFilters('clearall')">Clear filters</button>
                <button type="button" class="btn btn-primary" onclick="saveSearchFilters('save')">Save filters</button>
            </div>
            </form>
        </div>
    </div>
</div>
<!-- end search filters modal -->