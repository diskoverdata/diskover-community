<div class="modal" id="newindexnotification">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <button type="button" class="close" data-dismiss="modal" aria-hidden="true">&times;</button>
                <h4 class="modal-title">New index available</h4>
            </div>
            <div class="modal-body">
                <p>There is a newer index <span class="text-success"><?php echo $latest_completed_index; ?></span>, go to the select index page to load it.</p>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-default" onclick="setCookie('newindexnotification_hide', '<?php echo $latest_completed_index; ?>')" data-dismiss="modal">Hide</button>
                <button type="button" class="btn btn-default" data-dismiss="modal">Close</button>
                <button type="button" class="btn btn-primary" onclick="location.href='selectindices.php'">Go</button>
            </div>
        </div>
    </div>
</div>