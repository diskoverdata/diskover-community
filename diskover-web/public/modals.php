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

?>

<div class="modal" id="clipboardnotice" style="display:none">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-body text-info"><strong>Copied to clipboard.</strong></div>
        </div>
    </div>
</div>

<div id="welcomemsgModal" class="modal fade" role="dialog" style="display:none">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <button type="button" class="close" data-dismiss="modal" onclick="hideWelcomeMsgModal()">&times;</button>
                <h4 class="modal-title">Welcome to diskover-web community edition (ce)</h4>
            </div>
            <div class="modal-body">
                <p><i class="fas fa-bullhorn"></i> Thank you for downloading diskover ce, we hope you enjoy! <i class="fas fa-star" style="color:yellow"></i> <strong><a href="https://github.com/diskoverdata/diskover-community/stargazers" target="_blank">Star</a></strong> us on GitHub.</p>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-default" data-dismiss="modal" onclick="hideWelcomeMsgModal()">Close</button>
            </div>
        </div>
    </div>
</div>