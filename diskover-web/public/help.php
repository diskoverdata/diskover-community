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
require "../src/diskover/Auth.php";
require "../src/diskover/Diskover.php";

?>

<!DOCTYPE html>
<html lang="en">

<head>
	<?php if (isset($_COOKIE['sendanondata']) && $_COOKIE['sendanondata'] == 1) { ?>
    <!-- Global site tag (gtag.js) - Google Analytics -->
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-DYSE689C04"></script>
    <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){dataLayer.push(arguments);}
    gtag('js', new Date());

    gtag('config', 'G-DYSE689C04');
    </script>
    <?php } ?>
	<meta charset="utf-8">
	<meta http-equiv="X-UA-Compatible" content="IE=edge" />
	<meta name="viewport" content="width=device-width, initial-scale=1">
	<title>diskover &mdash; Help/ Support</title>
	<link rel="stylesheet" href="css/fontawesome-free/css/all.min.css" media="screen" />
	<link rel="stylesheet" href="css/bootswatch.min.css" media="screen" />
	<link rel="stylesheet" href="css/diskover.css" media="screen" />
	<link rel="icon" type="image/png" href="images/diskoverfavico.png" />
	<style>
		code {
			background-color: #333 !important;
			color: #56B6C2 !important;
		}

		strong {
			color: gray;
		}
	</style>
</head>

<body>
	<?php include "nav.php"; ?>

	<div class="container" id="mainwindow" style="margin-top:70px;">
		<h1 class="page-header"><i class="glyphicon glyphicon-question-sign"></i> Help/ Support</h1>
		<div class="row">
			<div class="col-xs-12">
				<div class="alert alert-dismissible alert-info">
					<i class="glyphicon glyphicon-info-sign"></i> For support and discussions, please join the diskover <a href="https://join.slack.com/t/diskoverworkspace/shared_invite/enQtNzQ0NjE1Njk5MjIyLWI4NWQ0MjFhYzQyMTRhMzk4NTQ3YjBlYjJiMDk1YWUzMTZmZjI1MTdhYTA3NzAzNTU0MDc5NDA2ZDI4OWRiMjM" target="_blank" class="alert-link">Slack workspace</a>. For any feedback/ issues, please submit an issue on <a href="https://github.com/diskoverdata/diskover-community/issues" target="_blank" class="alert-link">GitHub issues</a> page</a>.
					<br>Documentation is located at <a href="https://docs.diskoverdata.com" target="_blank" class="alert-link">docs.diskoverdata.com</a>.
				</div>
			</div>
		</div>
		<div class="row">
			<div class="col-xs-6">
				<div class="well">
					<h3>Search queries</h3>
					<ul>
						<li>By default use name, parent_path and extension fields when searching</li>
						<li>By default use AND when searching multiple words</li>
						<li>By default are case-insensitive</li>
						<li>Are case-sensitive when using field names except for name.text and parent_path.text</li>
						<li>By default wildcards are not used, to use wildcards use * or ?, example filename*</li>
						<li>Can be combined with AND, OR, NOT and ( ) round brackets for more granular search results (lowercase works as well)</li>
					</ul>
					<h4>Examples</h4>
					<p>all files > 5 MB:<br>
						<strong>size:>5242880 AND type:file</strong><br />
					<p>all folders > 10 MB:<br>
						<strong>size:>10485760 AND type:directory</strong><br />
					<p>all files in directory:<br>
						<strong>parent_path:"/Users/shirosai/Downloads"</strong><br />
					<p>all files in directory and all subdirs:<br>
						<strong>parent_path:\/Users\/shirosai\/Downloads*</strong><br />
					<p>files that haven't been modified in over 3 months and less than 5 years:<br>
						<strong>mtime:[now-5y TO now-3M]</strong><br />
					<p>files that haven't been modified or accessed in over 1 year:<br><strong>mtime:[* TO now-1y] AND atime:[* TO now-1y]</strong><br />
					<p>image files:<br>
						<strong>extension:(jpg OR gif OR png OR tif OR tiff OR dpx OR exr OR psd OR bmp OR tga)</strong><br />
					<p>audio files:<br>
						<strong>extension:(aif OR iff OR m3u OR m4a OR mid OR mp3 OR mpa OR wav OR wma)</strong><br />
					<p>video files:<br>
						<strong>extension:(asf OR avi OR flv OR m4v OR mov OR mp4 OR mpg OR rm OR vob OR wmv)</strong><br />
					<p>temp files:<br>
						<strong>extension:(cache OR tmp OR temp OR bak OR old)</strong><br />
					<p>compressed files:<br>
						<strong>extension:(7z OR deb OR gz OR pkg OR rar OR rpm OR tar OR zip OR zipx)</strong><br />
					<p>image sequence img001.dpx, img002.dpx, im003.dpx:<br>
						<strong>name:img*.dpx</strong><br />
					<p>all files or folders containing the word shirosai somewhere in the path (case-insensitive):<br>
						<strong>shirosai</strong><br />
					<p>all files or folders containing the word shirosai and diskover somewhere in the path (case-insensitive):<br>
						<strong>shirosai diskover</strong><br />
					<p>all files or folders containing the word shirosai or github somewhere in the path (case-insensitive):<br>
						<strong>shirosai OR github</strong><br />
					<p>all files containing the word shirosai in the file name (case-insensitive):<br>
						<strong>name.text:shirosai AND type:file</strong><br />
					<p>all folders containing the word shirosai in the folder name (case-insensitive):<br>
						<strong>name.text:shirosai AND type:directory</strong><br />
					<p>all files containing the word shirosai (case-sensitive):<br>
						<strong>name:*shirosai* AND type:file</strong><br />
					<p>all folders containing the word shirosai (case-sensitive):<br>
						<strong>name:*shirosai* AND type:directory</strong><br />
					<p>files named "shirosai.doc" with lowercase s:<br>
						<strong>name:shirosai.doc</strong><br />
					<p>files named "Shirosai.doc" with uppercase S:<br>
						<strong>name:Shirosai.doc</strong><br />
					<p>doc files with lowercase word "shirosai" at start of filename:<br>
						<strong>name:shirosai*.doc</strong><br />
					<p>doc files with lowercase word "shirosai" at end of filename:<br>
						<strong>name:*shirosai.doc</strong><br />
					<p>doc files with lowercase and first letter uppercase word "shirosai" somewhere in the filename:<br>
						<strong>name:(*shirosai*.doc OR *Shirosai*.doc)</strong><br />
					<p>files with lowercase "shirosai" somewhere in the filename or path:<br>
						<strong>(name:*shirosai* OR parent_path:*shirosai*) AND type:file</strong><br />
				</div>
			</div>
			<div class="col-xs-6">
				<div class="well">
					<h3>Default index fields</h3>
					<p>Below are a list of index field names which can be used for searching using <strong>fieldname:value</strong>.</p>
					<p>All values are case-sensitive except for fields with the name .text in the name.</p>
					<ul>
						<?php
						foreach ($fields as $field) {
							echo "<li>" . $field . "</li>\n";
						}
						?>
					</ul>
				</div>
			</div>
		</div>
	</div>

	<script language="javascript" src="js/jquery.min.js"></script>
	<script language="javascript" src="js/bootstrap.min.js"></script>
	<script language="javascript" src="js/diskover.js"></script>
</body>

</html>