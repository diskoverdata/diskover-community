<?php
if (count($results) > 0) {
?>
<span class="label label-success"><?php echo $total; ?> files found.</span>
<form method="post" action="/tagfiles.php" class="form-inline">
<table class="table table-striped table-hover ">
  <thead>
    <th>Filename</th>
    <th>Directory</th>
    <th>Size (bytes)</th>
    <th>Owner</th>
    <th>Group</th>
    <th>Last Modified (utc)</th>
    <th>Last Access (utc)</th>
  </thead>
  <tbody>
<?php
    error_reporting(E_ALL ^ E_NOTICE);

    foreach ($results as $result) {
        $file = $result['_source'];
?>
<input type="hidden" name="<?php echo $result['_id']; ?>" value="<?php echo $result['_index']; ?>" />
  <tr>
    <td><a href="/view.php?id=<?php echo $result['_id'] . '&index=' . $result['_index']; ?>"><?php echo $file['filename']; ?></a></td>
    <td><?php echo $file['path_parent']; ?></td>
    <td><?php echo $file['filesize']; ?></td>
    <td><?php echo $file['owner']; ?></td>
    <td><?php echo $file['group']; ?></td>
    <td><?php echo $file['last_modified']; ?></td>
    <td><?php echo $file['last_access']; ?></td>
  </tr>
  <tr>
    <td colspan="7"><div class="btn-group" data-toggle="buttons">
        <label class="tagDeleteLabel btn btn-info <?php if ($file['tag'] == 'delete') { echo 'active'; }?>">
          <input class="tagDeleteInput" type="radio" name="ids[<?php echo $result['_id']; ?>]" value="delete" <?php if ($file['tag'] == 'delete') { echo 'checked'; }; ?> /> delete
        </label>
        <label class="tagArchiveLabel btn btn-info <?php if ($file['tag'] == 'archive') { echo 'active'; }?>">
          <input class="tagArchiveInput" type="radio" name="ids[<?php echo $result['_id']; ?>]" value="archive" <?php if ($file['tag'] == 'archive') { echo 'checked'; }; ?> /> archive
        </label>
        <label class="tagKeepLabel btn btn-info <?php if ($file['tag'] == 'keep') { echo 'active'; }?>">
          <input class="tagKeepInput" type="radio" name="ids[<?php echo $result['_id']; ?>]" value="keep" <?php if ($file['tag'] == 'keep') { echo 'checked'; }; ?> /> keep
        </label>
      </div></td>
  </tr>
<?php
    } // END foreach loop over results
?>
  </tbody>
</table>
<div class="btn-group">
  <button class="btn btn-default" type="button" name="tagAll" id="tagAllDelete" /> Select All Delete</button>
  <button class="btn btn-default" type="button" name="tagAll" id="tagAllArchive" /> Select All Archive</button>
  <button class="btn btn-default" type="button" name="tagAll" id="tagAllKeep" /> Select All Keep</button>
</div>
<button type="button" id="refresh" class="btn btn-default">Refresh</button>
<button type="submit" class="btn btn-primary">Tag files</button>
</form>
<?php if ($total > $searchParams['size']) { ?>
<p><ul class="pagination">
  <li <?php if ($_REQUEST['p'] == 1) { echo 'class="disabled"'; }?>><a <?php if ($_REQUEST['p'] == 1) { echo 'href="#"'; } else {?> href="<?php echo $_SERVER['PHP_SELF'] . '?q=' . $_REQUEST['q'] . '&submitted=' . $_REQUEST['submitted'] . '&p=' . ($_REQUEST['p'] - 1); ?>"<?php } ?>>&laquo;</a></li>
  <?php for ($p=1; $p<=$total / $searchParams['size'] + 1; $p++) { if ($_REQUEST['p'] == $p) { echo '<li class="active">'; } else { echo '<li>'; } ?>
  <a href="<?php echo $_SERVER['PHP_SELF'] . '?q=' . $_REQUEST['q'] . '&submitted=' . $_REQUEST['submitted'] . '&p=' . $p; ?>"><?php echo $p; ?></a></li>
  <?php }; ?>
  <li <?php if (($_REQUEST['p'] + 1) > ($total / $searchParams['size'] + 1)) { echo 'class="disabled"'; }?>><a <?php if (($_REQUEST['p'] + 1) > ($total / $searchParams['size'] + 1)) { echo 'href="#"'; } else {?> href="<?php echo $_SERVER['PHP_SELF'] . '?q=' . $_REQUEST['q'] . '&submitted=' . $_REQUEST['submitted'] . '&p=' . ($_REQUEST['p'] + 1); ?>"<?php } ?>>&raquo;</a></li>
</ul></p>
<?php }; ?>
<?php
} // END if there are search results

else {
?>
<span class="label label-warning">Sorry, no files found :(</span>
<?php

} // END elsif there are no search results

?>
