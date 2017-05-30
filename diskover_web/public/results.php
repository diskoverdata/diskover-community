<?php
if (count($results) > 0) {
?>
<div class="container-fluid searchresults">
  <div class="row">
    <div class="alert alert-dismissible alert-success col-xs-4">
      <button type="button" class="close" data-dismiss="alert">&times;</button>
      <span class="glyphicon glyphicon-search"></span> <strong><?php echo $total; ?> files found</strong>.
    </div>
  </div>
  <div class="row">
    <form method="post" action="/tagfiles.php" class="form-inline">
      <div class="form-group pull-right">
        <input type="text" class="search form-control" placeholder="Search within results">
      </div>
    <span class="counter pull-right"></span>
    <table class="table table-striped table-hover table-condensed table-bordered results" style="word-break:break-word;word-wrap:break-word;">
      <thead>
        <tr>
          <th class="text-nowrap">#</th>
          <th class="text-nowrap">Filename</th>
          <th class="text-nowrap">Directory</th>
          <th class="text-nowrap">Size(bytes)</th>
          <th class="text-nowrap">Owner</th>
          <th class="text-nowrap">Group</th>
          <th class="text-nowrap">Last Modified (utc)</th>
          <th class="text-nowrap">Last Access (utc)</th>
          <th class="text-nowrap">Tag (del/arch/keep)</th>
        </tr>
        <tr class="warning no-result">
          <td colspan="9"><i class="fa fa-warning"></i> No result</td>
        </tr>
      </thead>
      <tfoot>
        <th>#</th>
        <th>Filename</th>
        <th>Directory</th>
        <th>Size(bytes)</th>
        <th>Owner</th>
        <th>Group</th>
        <th>Last Modified (utc)</th>
        <th>Last Access (utc)</th>
        <th>Tag (del/arch/keep)</th>
      </tfoot>
      <tbody>
      <?php
        error_reporting(E_ALL ^ E_NOTICE);
        $i = $p * 100 - 100;
        foreach ($results as $result) {
            $file = $result['_source'];
            $i += 1;
      ?>
      <input type="hidden" name="<?php echo $result['_id']; ?>" value="<?php echo $result['_index']; ?>" />
      <tr class="<?php if ($file['tag'] == 'delete') { echo 'warning'; } elseif ($file['tag'] == 'archive') { echo 'success'; } elseif ($file['tag'] == 'keep') { echo 'info'; }?>">
        <th scope="row" class="text-nowrap"><?php echo $i; ?></th>
        <td><a href="/view.php?id=<?php echo $result['_id'] . '&index=' . $result['_index']; ?>"><?php echo $file['filename']; ?></a></td>
        <td><?php echo $file['path_parent']; ?></td>
        <td class="text-nowrap"><?php echo $file['filesize']; ?></td>
        <td class="text-nowrap"><?php echo $file['owner']; ?></td>
        <td class="text-nowrap"><?php echo $file['group']; ?></td>
        <td class="text-nowrap"><?php echo $file['last_modified']; ?></td>
        <td class="text-nowrap"><?php echo $file['last_access']; ?></td>
        <td class="text-nowrap"><div class="btn-group" style="white-space:nowrap;" data-toggle="buttons">
            <label class="tagDeleteLabel btn btn-warning <?php if ($file['tag'] == 'delete') { echo 'active'; }?>" style="display:inline-block;float:none;" id="highlightRowDelete">
              <input class="tagDeleteInput" type="radio" name="ids[<?php echo $result['_id']; ?>]" value="delete" <?php if ($file['tag'] == 'delete') { echo 'checked'; }; ?> /><span class="glyphicon glyphicon-trash"></span>
            </label>
            <label class="tagArchiveLabel btn btn-success <?php if ($file['tag'] == 'archive') { echo 'active'; }?>" style="display:inline-block;float:none;" id="highlightRowArchive">
              <input class="tagArchiveInput" type="radio" name="ids[<?php echo $result['_id']; ?>]" value="archive" <?php if ($file['tag'] == 'archive') { echo 'checked'; }; ?> /><span class="glyphicon glyphicon-cloud-upload"></span>
            </label>
            <label class="tagKeepLabel btn btn-info <?php if ($file['tag'] == 'keep') { echo 'active'; }?>" style="display:inline-block;float:none;" id="highlightRowKeep">
              <input class="tagKeepInput" type="radio" name="ids[<?php echo $result['_id']; ?>]" value="keep" <?php if ($file['tag'] == 'keep') { echo 'checked'; }; ?> /><span class="glyphicon glyphicon-floppy-saved"></span>
            </label>
          </div></td>
      </tr>
      <?php
        } // END foreach loop over results
      ?>
      </tbody>
    </table>
  </div>
  <div class="row pull-right">
    <div class="col-xs-12">
      <p class="text-right">
      <div class="btn-group">
        <button class="btn btn-default" type="button" name="tagAll" id="tagAllDelete" /> Select All Delete</button>
        <button class="btn btn-default" type="button" name="tagAll" id="tagAllArchive" /> Select All Archive</button>
        <button class="btn btn-default" type="button" name="tagAll" id="tagAllKeep" /> Select All Keep</button>
      </div>
      <button type="button" id="refresh" class="btn btn-default">Refresh</button>
      <button type="submit" class="btn btn-primary">Tag files</button>
      </p>
      </form>
    </div>
  </div>
  <div class="row">
    <div class="col-xs-12 text-right">
      <?php
      // pagination
      if ($total > $searchParams['size']) {
      ?>
      <ul class="pagination">
        <?php
        parse_str($_SERVER["QUERY_STRING"], $querystring);
        $qsp = $querystring;
        $qsn = $querystring;
        if ($qsp['p'] > 1) {
          $qsp['p'] -= 1;
        }
        if ($qsn['p'] < $total/$searchParams['size']+1) {
          $qsn['p'] += 1;
        }
        $qsn = http_build_query($qsn);
        $qsp = http_build_query($qsp);
        $prevpage = $_SERVER['PHP_SELF'] . "?" . $qsp;
        $nextpage = $_SERVER['PHP_SELF'] . "?" . $qsn;
        ?>
        <?php if ($querystring['p'] == 1) { echo '<li class="disabled"><a href="#">'; } else { echo '<li><a href="' . $prevpage . '">'; } ?>&laquo;</a></li>
        <?php
        for ($pn=1; $pn<=$total/$searchParams['size']+1; $pn++) {
          $qs = $querystring;
          $qs['p'] = $pn;
          $qs1 = http_build_query($qs);
          $url = $_SERVER['PHP_SELF'] . "?" . $qs1;
        ?>
        <li<?php if ($querystring['p'] == $pn) { echo ' class="active"'; } ?>><a href="<?php echo $url; ?>"><?php echo $pn; ?></a></li>
        <?php } ?>
        <?php if ($querystring['p'] >= $total/$searchParams['size']) { echo '<li class="disabled"><a href="#">'; } else { echo '<li><a href="' . $nextpage . '">'; } ?>&raquo;</a></li>
      </ul>
      <?php } ?>
    </div>
  </div>
</div>
<?php
} // END if there are search results

else {
?>
<div class="container">
  <div class="row">
    <div class="alert alert-dismissible alert-danger col-xs-8">
      <button type="button" class="close" data-dismiss="alert">&times;</button>
      <span class="glyphicon glyphicon-exclamation-sign"></span> <strong>Sorry, no files found :(</strong> Change a few things up and try searching again.
    </div>
  </div>
</div>
<?php

} // END elsif there are no search results

?>
