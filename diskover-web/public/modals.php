<?php
/*
diskover-web community edition (ce)
https://github.com/diskoverdata/diskover-community/
https://diskoverdata.com

Copyright 2017-2021 Diskover Data, Inc.
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

<div id="sendanondataModal" class="modal fade" role="dialog" style="display:none">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <button type="button" class="close" data-dismiss="modal" onclick="setSendAnonData()">&times;</button>
                <h4 class="modal-title">Send anonymous usage data</h4>
            </div>
            <div class="modal-body">
                <p><i class="fas fa-bullhorn"></i> Welcome to diskover-web community edition (ce). Help us improve diskover by sending anonymous usage data to Diskover Data. No personal information is sent. You can change this anytime on the settings page.</p>
                <div class="form-check">
                    <input type="checkbox" class="form-check-input" id="sendanondata" onclick="setSendAnonData()" checked>
                    <label class="form-check-label" for="sendanondata">Send anonymous data</label>
                </div>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-default" data-dismiss="modal" onclick="setSendAnonData()">Close</button>
            </div>
        </div>
    </div>
</div>