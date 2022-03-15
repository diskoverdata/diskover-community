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

require '../vendor/autoload.php';
require '../src/diskover/config_inc.php';

error_reporting(E_ALL ^ E_NOTICE);

?>
<nav class="navbar navbar-inverse navbar-fixed-top">
    <div class="container-fluid">
        <div class="navbar-header">
            <button type="button" class="navbar-toggle collapsed" data-toggle="collapse" data-target="#navbar-collapsible">
                <span class="sr-only">Toggle navigation</span>
                <span class="icon-bar"></span>
                <span class="icon-bar"></span>
                <span class="icon-bar"></span>
            </button>
            <img class="pull-left" title="diskover-web v<?php echo $VERSION ?>" alt="diskover-web logo" style="position:absolute;left:12px;top:8px;" src="images/diskovernav.png" width="40" height="30" /><span style="margin-left:45px;"> </span>
        </div>

        <div class="collapse navbar-collapse" id="navbar-collapsible">
            <ul class="nav navbar-nav">
                <li><a href="dashboard.php?index=<?php echo $esIndex; ?>" title="dashboard"><i class="fas fa-tachometer-alt"></i> </a></li>
                <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;q=parent_path:<?php echo rawurlencode(escape_chars($path)); ?>&amp;submitted=true&amp;p=1&amp;doctype=&amp;path=<?php echo rawurlencode($path); ?>" title="file search"><i class="far fa-folder"></i> </a></li>
                <li class="dropdown">
                    <a href="#" class="dropdown-toggle" data-toggle="dropdown" role="button" aria-expanded="false" title="analytics"><i class="fas fa-chart-bar"></i> Analytics <span class="caret"></span></a>
                    <ul class="dropdown-menu multi-level" role="menu">
                        <li><a href="#"><i class="glyphicon glyphicon-folder-open"></i> File Tree <span class="label label-info">Essential</span></a></li>
                        <li><a href="#"><i class="glyphicon glyphicon-th"></i> Treemap <span class="label label-info">Essential</span></a></li>
                        <li><a href="#"><i class="glyphicon glyphicon-fire"></i> Heatmap <span class="label label-info">Pro</span></a></li>
                        <li><a href="#"><i class="glyphicon glyphicon-tags"></i> Tags <span class="label label-info">Pro</span></a></li>
                        <li><a href="#"><i class="glyphicon glyphicon-equalizer"></i> Smart Searches <span class="label label-info">Pro</span></a></li>
                        <li><a href="#"><i class="glyphicon glyphicon-user"></i> User Analysis <span class="label label-info">Essential</span></a></li>
                        <li><a href="#"><i class="glyphicon glyphicon-piggy-bank"></i> Cost Analysis <span class="label label-info">Pro</span></a></li>
                    </ul>
                </li>
                <li class="dropdown">
                    <a href="#" class="dropdown-toggle" data-toggle="dropdown" role="button" aria-expanded="false" title="Quick Search"><i class="fas fa-search"></i> Quick</i> <span class="caret"></span></a>
                    <ul class="dropdown-menu multi-level" role="menu">
                        <li class="dropdown-submenu">
                            <a href="#">Files</a>
                            <ul class="dropdown-menu">
                                <li class="dropdown-submenu">
                                    <a href="#">Date</a>
                                    <ul class="dropdown-menu">
                                        <li class="dropdown-submenu">
                                            <a href="#">Modified</a>
                                            <ul class="dropdown-menu">
                                                <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=mtime:[* TO now/m-1w/d]&amp;doctype=file">Date modified >1 week</a></li>
                                                <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=mtime:[* TO now/m-2w/d]&amp;doctype=file">Date modified >2 weeks</a></li>
                                                <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=mtime:[* TO now/m-1M/d]&amp;doctype=file">Date modified >1 month</a></li>
                                                <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=mtime:[* TO now/m-2M/d]&amp;doctype=file">Date modified >2 months</a></li>
                                                <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=mtime:[* TO now/m-3M/d]&amp;doctype=file">Date modified >3 months</a></li>
                                                <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=mtime:[* TO now/m-6M/d]&amp;doctype=file">Date modified >6 months</a></li>
                                                <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=mtime:[* TO now/m-1y/d]&amp;doctype=file">Date modified >1 year</a></li>
                                                <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=mtime:[* TO now/m-2y/d]&amp;doctype=file">Date modified >2 years</a></li>
                                                <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=mtime:[* TO now/m-3y/d]&amp;doctype=file">Date modified >3 years</a></li>
                                            </ul>
                                        </li>
                                        <li class="dropdown-submenu">
                                            <a href="#">Accessed</a>
                                            <ul class="dropdown-menu">
                                                <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=atime:[* TO now/m-1w/d]&amp;doctype=file">Last accessed >1 week</a></li>
                                                <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=atime:[* TO now/m-2w/d]&amp;doctype=file">Last accessed >2 weeks</a></li>
                                                <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=atime:[* TO now/m-1M/d]&amp;doctype=file">Last accessed >1 month</a></li>
                                                <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=atime:[* TO now/m-2M/d]&amp;doctype=file">Last accessed >2 months</a></li>
                                                <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=atime:[* TO now/m-3M/d]&amp;doctype=file">Last accessed >3 months</a></li>
                                                <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=atime:[* TO now/m-6M/d]&amp;doctype=file">Last accessed >6 months</a></li>
                                                <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=atime:[* TO now/m-1y/d]&amp;doctype=file">Last accessed >1 year</a></li>
                                                <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=atime:[* TO now/m-2y/d]&amp;doctype=file">Last accessed >2 years</a></li>
                                                <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=atime:[* TO now/m-3y/d]&amp;doctype=file">Last accessed >3 years</a></li>
                                            </ul>
                                        </li>
                                        <li class="dropdown-submenu">
                                            <a href="#">Changed</a>
                                            <ul class="dropdown-menu">
                                                <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=ctime:[* TO now/m-1w/d]&amp;doctype=file">Date changed >1 week</a></li>
                                                <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=ctime:[* TO now/m-2w/d]&amp;doctype=file">Date changed >2 weeks</a></li>
                                                <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=ctime:[* TO now/m-1M/d]&amp;doctype=file">Date changed >1 month</a></li>
                                                <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=ctime:[* TO now/m-2M/d]&amp;doctype=file">Date changed >2 months</a></li>
                                                <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=ctime:[* TO now/m-3M/d]&amp;doctype=file">Date changed >3 months</a></li>
                                                <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=ctime:[* TO now/m-6M/d]&amp;doctype=file">Date changed >6 months</a></li>
                                                <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=ctime:[* TO now/m-1y/d]&amp;doctype=file">Date changed >1 year</a></li>
                                                <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=ctime:[* TO now/m-2y/d]&amp;doctype=file">Date changed >2 years</a></li>
                                                <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=ctime:[* TO now/m-3y/d]&amp;doctype=file">Date changed >3 years</a></li>
                                            </ul>
                                        </li>
                                    </ul>
                                </li>
                                <li class="dropdown-submenu">
                                    <a href="#">Size</a>
                                    <ul class="dropdown-menu">
                                        <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=size:>1&amp;doctype=file">Size >1 byte</a></li>
                                        <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=size:>1024&amp;doctype=file">Size >1 KB</a></li>
                                        <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=size:>65536&amp;doctype=file">Size >64 KB</a></li>
                                        <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=size:>262144&amp;doctype=file">Size >256 KB</a></li>
                                        <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=size:>524288&amp;doctype=file">Size >512 KB</a></li>
                                        <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=size:>1048576&amp;doctype=file">Size >1 MB</a></li>
                                        <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=size:>10485760&amp;doctype=file">Size >10 MB</a></li>
                                        <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=size:>26214400&amp;doctype=file">Size >25 MB</a></li>
                                        <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=size:>52428800&amp;doctype=file">Size >50 MB</a></li>
                                        <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=size:>104857600&amp;doctype=file">Size >100 MB</a></li>
                                        <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=size:>262144000&amp;doctype=file">Size >250 MB</a></li>
                                        <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=size:>524288000&amp;doctype=file">Size >500 MB</a></li>
                                        <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=size:>1048576000&amp;doctype=file">Size >1 GB</a></li>
                                    </ul>
                                </li>
                                <li class="dropdown-submenu">
                                    <a href="#">Type</a>
                                    <ul class="dropdown-menu">
                                        <?php foreach ($config->FILE_TYPES as $type_name => $type_extensions) {
                                            $extensions = '(';
                                            $n = sizeof($type_extensions);
                                            $i = 0;
                                            while ($i <= $n) {
                                                $extensions .= $type_extensions[$i];
                                                if ($i < $n - 1) {
                                                    $extensions .= ' OR ';
                                                }
                                                $i++;
                                            }
                                            $extensions .= ')';
                                        ?>
                                            <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=extension:<?php echo $extensions; ?>&amp;doctype=file"><?php echo $type_name; ?></a></li>
                                        <?php } ?>
                                    </ul>
                                </li>
                                <li class="divider"></li>
                                <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=nlink:>1&amp;doctype=file">Hardlinks >1</a></li>
                                <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=size:0&amp;doctype=file">Empty (0 b) files</a></li>
                                <li><a href="#">Duplicate files <span class="label label-info">Essential</span></a></li>
                                <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=mtime:[* TO now/m-6M/d] AND atime:[* TO now/m-6M/d]&amp;doctype=file">Recommended to remove</a></li>
                            </ul>
                        </li>
                        <li class="dropdown-submenu">
                            <a tabindex="-2" href="#">Directories</a>
                            <ul class="dropdown-menu">
                                <li class="dropdown-submenu">
                                    <a href="#">Date</a>
                                    <ul class="dropdown-menu">
                                        <li class="dropdown-submenu">
                                            <a href="#">Modified</a>
                                            <ul class="dropdown-menu">
                                                <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=mtime:[* TO now/m-1w/d]&amp;doctype=directory">Date modified >1 week</a></li>
                                                <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=mtime:[* TO now/m-2w/d]&amp;doctype=directory">Date modified >2 weeks</a></li>
                                                <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=mtime:[* TO now/m-1M/d]&amp;doctype=directory">Date modified >1 month</a></li>
                                                <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=mtime:[* TO now/m-2M/d]&amp;doctype=directory">Date modified >2 months</a></li>
                                                <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=mtime:[* TO now/m-3M/d]&amp;doctype=directory">Date modified >3 months</a></li>
                                                <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=mtime:[* TO now/m-6M/d]&amp;doctype=directory">Date modified >6 months</a></li>
                                                <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=mtime:[* TO now/m-1y/d]&amp;doctype=directory">Date modified >1 year</a></li>
                                                <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=mtime:[* TO now/m-2y/d]&amp;doctype=directory">Date modified >2 years</a></li>
                                                <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=mtime:[* TO now/m-3y/d]&amp;doctype=directory">Date modified >3 years</a></li>
                                            </ul>
                                        </li>
                                        <li class="dropdown-submenu">
                                            <a href="#">Accessed</a>
                                            <ul class="dropdown-menu">
                                                <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=atime:[* TO now/m-1w/d]&amp;doctype=directory">Last accessed >1 week</a></li>
                                                <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=atime:[* TO now/m-2w/d]&amp;doctype=directory">Last accessed >2 weeks</a></li>
                                                <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=atime:[* TO now/m-1M/d]&amp;doctype=directory">Last accessed >1 month</a></li>
                                                <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=atime:[* TO now/m-2M/d]&amp;doctype=directory">Last accessed >2 months</a></li>
                                                <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=atime:[* TO now/m-3M/d]&amp;doctype=directory">Last accessed >3 months</a></li>
                                                <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=atime:[* TO now/m-6M/d]&amp;doctype=directory">Last accessed >6 months</a></li>
                                                <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=atime:[* TO now/m-1y/d]&amp;doctype=directory">Last accessed >1 year</a></li>
                                                <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=atime:[* TO now/m-2y/d]&amp;doctype=directory">Last accessed >2 years</a></li>
                                                <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=atime:[* TO now/m-3y/d]&amp;doctype=directory">Last accessed >3 years</a></li>
                                            </ul>
                                        </li>
                                        <li class="dropdown-submenu">
                                            <a href="#">Changed</a>
                                            <ul class="dropdown-menu">
                                                <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=ctime:[* TO now/m-1w/d]&amp;doctype=directory">Date changed >1 week</a></li>
                                                <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=ctime:[* TO now/m-2w/d]&amp;doctype=directory">Date changed >2 weeks</a></li>
                                                <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=ctime:[* TO now/m-1M/d]&amp;doctype=directory">Date changed >1 month</a></li>
                                                <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=ctime:[* TO now/m-2M/d]&amp;doctype=directory">Date changed >2 months</a></li>
                                                <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=ctime:[* TO now/m-3M/d]&amp;doctype=directory">Date changed >3 months</a></li>
                                                <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=ctime:[* TO now/m-6M/d]&amp;doctype=directory">Date changed >6 months</a></li>
                                                <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=ctime:[* TO now/m-1y/d]&amp;doctype=directory">Date changed >1 year</a></li>
                                                <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=ctime:[* TO now/m-2y/d]&amp;doctype=directory">Date changed >2 years</a></li>
                                                <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=ctime:[* TO now/m-3y/d]&amp;doctype=directory">Date changed >3 years</a></li>
                                            </ul>
                                        </li>
                                    </ul>
                                </li>
                                <li class="dropdown-submenu">
                                    <a href="#">Size</a>
                                    <ul class="dropdown-menu">
                                        <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=size:>1&amp;doctype=directory">Size >1 byte</a></li>
                                        <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=size:>1024&amp;doctype=directory">Size >1 KB</a></li>
                                        <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=size:>65536&amp;doctype=directory">Size >64 KB</a></li>
                                        <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=size:>262144&amp;doctype=directory">Size >256 KB</a></li>
                                        <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=size:>524288&amp;doctype=directory">Size >512 KB</a></li>
                                        <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=size:>1048576&amp;doctype=directory">Size >1 MB</a></li>
                                        <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=size:>10485760&amp;doctype=directory">Size >10 MB</a></li>
                                        <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=size:>26214400&amp;doctype=directory">Size >25 MB</a></li>
                                        <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=size:>52428800&amp;doctype=directory">Size >50 MB</a></li>
                                        <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=size:>104857600&amp;doctype=directory">Size >100 MB</a></li>
                                        <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=size:>262144000&amp;doctype=directory">Size >250 MB</a></li>
                                        <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=size:>524288000&amp;doctype=directory">Size >500 MB</a></li>
                                        <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=size:>1048576000&amp;doctype=directory">Size >1 GB</a></li>
                                    </ul>
                                </li>
                                <li class="divider"></li>
                                <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=size:0&amp;doctype=directory">Empty (0 b) directories</a></li>
                                <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=mtime:[* TO now/m-6M/d] AND atime:[* TO now/m-6M/d]&amp;doctype=directory">Recommended to remove</a></li>
                            </ul>
                        </li>
                        <li class="dropdown-submenu">
                            <a tabindex="-3" href="#">All</a>
                            <ul class="dropdown-menu">
                                <li class="dropdown-submenu">
                                    <a href="#">Date</a>
                                    <ul class="dropdown-menu">
                                        <li class="dropdown-submenu">
                                            <a href="#">Modified</a>
                                            <ul class="dropdown-menu">
                                                <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=mtime:[* TO now/m-1w/d]">Date modified >1 week</a></li>
                                                <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=mtime:[* TO now/m-2w/d]">Date modified >2 weeks</a></li>
                                                <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=mtime:[* TO now/m-1M/d]">Date modified >1 month</a></li>
                                                <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=mtime:[* TO now/m-2M/d]">Date modified >2 months</a></li>
                                                <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=mtime:[* TO now/m-3M/d]">Date modified >3 months</a></li>
                                                <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=mtime:[* TO now/m-6M/d]">Date modified >6 months</a></li>
                                                <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=mtime:[* TO now/m-1y/d]">Date modified >1 year</a></li>
                                                <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=mtime:[* TO now/m-2y/d]">Date modified >2 years</a></li>
                                                <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=mtime:[* TO now/m-3y/d]">Date modified >3 years</a></li>
                                            </ul>
                                        </li>
                                        <li class="dropdown-submenu">
                                            <a href="#">Accessed</a>
                                            <ul class="dropdown-menu">
                                                <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=atime:[* TO now/m-1w/d]">Last accessed >1 week</a></li>
                                                <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=atime:[* TO now/m-2w/d]">Last accessed >2 weeks</a></li>
                                                <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=atime:[* TO now/m-1M/d]">Last accessed >1 month</a></li>
                                                <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=atime:[* TO now/m-2M/d]">Last accessed >2 months</a></li>
                                                <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=atime:[* TO now/m-3M/d]">Last accessed >3 months</a></li>
                                                <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=atime:[* TO now/m-6M/d]">Last accessed >6 months</a></li>
                                                <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=atime:[* TO now/m-1y/d]">Last accessed >1 year</a></li>
                                                <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=atime:[* TO now/m-2y/d]">Last accessed >2 years</a></li>
                                                <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=atime:[* TO now/m-3y/d]">Last accessed >3 years</a></li>
                                            </ul>
                                        </li>
                                        <li class="dropdown-submenu">
                                            <a href="#">Changed</a>
                                            <ul class="dropdown-menu">
                                                <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=ctime:[* TO now/m-1w/d]">Date changed >1 week</a></li>
                                                <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=ctime:[* TO now/m-2w/d]">Date changed >2 weeks</a></li>
                                                <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=ctime:[* TO now/m-1M/d]">Date changed >1 month</a></li>
                                                <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=ctime:[* TO now/m-2M/d]">Date changed >2 months</a></li>
                                                <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=ctime:[* TO now/m-3M/d]">Date changed >3 months</a></li>
                                                <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=ctime:[* TO now/m-6M/d]">Date changed >6 months</a></li>
                                                <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=ctime:[* TO now/m-1y/d]">Date changed >1 year</a></li>
                                                <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=ctime:[* TO now/m-2y/d]">Date changed >2 years</a></li>
                                                <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=ctime:[* TO now/m-3y/d]">Date changed >3 years</a></li>
                                            </ul>
                                        </li>
                                    </ul>
                                </li>
                                <li class="dropdown-submenu">
                                    <a href="#">Size</a>
                                    <ul class="dropdown-menu">
                                        <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=size:>1">Size >1 byte</a></li>
                                        <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=size:>1024">Size >1 KB</a></li>
                                        <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=size:>65536">Size >64 KB</a></li>
                                        <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=size:>262144">Size >256 KB</a></li>
                                        <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=size:>524288">Size >512 KB</a></li>
                                        <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=size:>1048576">Size >1 MB</a></li>
                                        <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=size:>10485760">Size >10 MB</a></li>
                                        <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=size:>26214400">Size >25 MB</a></li>
                                        <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=size:>52428800">Size >50 MB</a></li>
                                        <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=size:>104857600">Size >100 MB</a></li>
                                        <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=size:>262144000">Size >250 MB</a></li>
                                        <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=size:>524288000">Size >500 MB</a></li>
                                        <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=size:>1048576000">Size >1 GB</a></li>
                                    </ul>
                                </li>
                                <li class="divider"></li>
                                <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=size:0">Empty (0 b)</a></li>
                                <li><a href="search.php?index=<?php echo $esIndex; ?>&amp;submitted=true&amp;p=1&amp;q=mtime:[* TO now/m-6M/d] AND atime:[* TO now/m-6M/d]">Recommended to remove</a></li>
                            </ul>
                        </li>
                    </ul>
                </li>
            </ul>
            <ul class="nav navbar-nav navbar-right">
                <li class="dropdown">
                    <a href="#" class="dropdown-toggle" data-toggle="dropdown" role="button" aria-expanded="false"><i class="glyphicon glyphicon-cog"></i> <span class="caret"></span></a>
                    <ul class="dropdown-menu" role="menu">
                        <li><a href="settings.php"><i class="fas fa-user-cog"></i> Settings</a></li>
                        <li><a href="selectindices.php"><i class="glyphicon glyphicon-list-alt"></i> Indices</a></li>
                        <li><a href="#"><i class="glyphicon glyphicon-tasks"></i> Task Panel <span class="label label-info">Essential</span></a></li>
                        <li><a href="help.php"><i class="glyphicon glyphicon-question-sign"></i> Help</a></li>
                        <li><a href="https://github.com/diskoverdata/diskover-community/" target="_blank"><i class="fab fa-github-alt"></i> diskover GitHub</a></li>
                        <li><a href="https://diskoverdata.com/solutions/" target="_blank"><i class="fas fa-cart-plus"></i> Upgrade license</a></li>
                        <li class="divider"></li>
                        <li><a title="reload indices and get latest" href="<?php echo $_SERVER['REQUEST_URI'] . (parse_url($_SERVER['REQUEST_URI'], PHP_URL_QUERY) ? '&' : '?') . 'reloadindices'; ?>"><i class="glyphicon glyphicon-refresh"></i> Reload indices</a> <span class="small text-primary" style="padding-left:3px"><i class="fas fa-clock"></i> last updated <?php echo $indexinfo_updatetime->format('h:i:s A'); ?></span></li>
                        <?php if ($config->LOGIN_REQUIRED) { ?>
                            <li class="divider"></li>
                            <li><a href="logout.php"><i class="glyphicon glyphicon-log-out"></i> Logout</a></li>
                        <?php } ?>
                    </ul>
                </li>
            </ul>
            <form method="get" action="search.php" role="search" id="searchnav" class="navbar-form">
                <input type="hidden" name="index" value="<?php echo $esIndex; ?>" />
                <input type="hidden" name="index2" value="<?php echo $esIndex2; ?>" />
                <input type="hidden" name="submitted" value="true" />
                <input type="hidden" name="p" value="1" />
                <?php if (isset($_REQUEST['resultsize'])) {
                    $resultSize = $_REQUEST['resultsize'];
                } elseif (getCookie("resultsize") != "") {
                    $resultSize = getCookie("resultsize");
                } else {
                    $resultSize = $config->SEARCH_RESULTS;
                } ?>
                <input type="hidden" name="resultsize" value="<?php echo $resultSize; ?>" />
                <input type="hidden" name="userinput" value="true" />
                <div class="form-group" style="display:inline;">
                    <div id="searchnavbox" class="input-group" style="display:table;">
                        <input id="searchnavinput" autocomplete="off" spellcheck="false" type="text" name="q" class="form-control input navsearchbox" placeholder="Search" value="<?php echo ($_REQUEST['userinput']) ? htmlspecialchars($_REQUEST['q']) : "" ?>">
                        <span class="input-group-addon" style="width: 1%; margin: 1px; padding: 1px; height:20px; background:#202225;">
                            <button title="clear search" type="button" onclick="javascript:clearSearchBox(); return false;" class="btn btn-default btn-sm" style="background:#373737"><span style="font-size:10px; color:gray"><i class="glyphicon glyphicon-remove"></i></span></button>
                        </span>
                        <span class="input-group-addon" style="width: 1%; margin: 1px; padding: 1px; height:20px;">
                            <button title="search" type="submit" class="btn btn-default btn-sm" style="width:65px"><span style="font-size:12px"><i class="fas fa-search" style="color:lightgray"></i></span></button>
                        </span>
                        <span class="input-group-addon" style="width: 1%; margin: 1px; padding: 1px; height:20px;">
                            <span title="search current directory only (recursive)" style="position:relative; top:4px; padding-left:2px"><label class="nav-switch"><input onchange="searchCurrentDirOnly()" id="searchcurrentdironly" name="searchcurrentdironly" type="checkbox" <?php echo (getCookie('searchcurrentdironly') == 1) ? 'checked' : '' ?>><span class="nav-slider round"></span></label></span><span style="font-size:12px; position:relative; top:-4px; padding-right:2px; color:lightgray">&nbsp;Current Dir&nbsp;</span>
                        </span>
                        <span class="input-group-addon" style="width: 1%; margin: 1px; padding: 1px; height:20px;">
                            <button title="search filters" type="button" class="btn btn-default btn-sm" data-toggle="modal" data-target="#searchFilterModal"><span style="font-size:12px; color:lightgray">&nbsp;<i class="fas fa-filter" style="color:gray"></i> Filters&nbsp;</span><span class="" id="filtercount"></span></button>
                        </span>
                    </div>
                </div>
            </form>
            <div class="essearchreply" id="essearchreply-nav">
                <div class="essearchreply-text" id="essearchreply-text-nav"></div>
            </div>
        </div>
    </div>
</nav>

<?php
// new index notifier
if (basename($_SERVER['PHP_SELF']) !== 'selectindices.php') {
    require "newindexnotice.php";
}
// search filter modal
require "searchfilters.php";
?>

<script>
    // hide search box in nav
    function hideSearchBox() {
        document.getElementById('searchnavinput').value = '';
        document.getElementById('essearchreply-nav').style.display = 'none';
        $("#searchnavinput").attr("placeholder", "Search");
        //$('#searchbox').hide();
        // set search nav input background colour back to default
        $("#searchnavinput").attr('style', 'background-color: #373737 !important');
    }
    // clear search box
    function clearSearchBox() {
        document.getElementById('searchnavinput').value = '';
        enableSearchSubmit();
    }
    // search current dir only toggle
    function searchCurrentDirOnly() {
        if (document.getElementById("searchcurrentdironly").checked) {
            setCookie('searchcurrentdironly', 1);
        } else {
            setCookie('searchcurrentdironly', 0);
        }
    }
</script>