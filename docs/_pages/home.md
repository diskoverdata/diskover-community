---
layout: splash
permalink: /
header:
  overlay_color: "#000"
  overlay_filter: "0.3"
  overlay_image: https://github.com/shirosaidev/diskover/blob/master/docs/_pages/heatmap.png?raw=true
  cta_label: "<i class='fa fa-download' aria-hidden='true'></i> Download"
  cta_url: "https://diskoverspace.com/diskover/"
  caption:
excerpt: '<img src="https://github.com/shirosaidev/diskover/raw/master/docs/diskover.png?raw=true" style="width: 183px; float: left; margin: 0px 30px 10px 0px;">File system crawler, storage search engine and storage analytics software powered by Elasticsearch to help visualize and manage your disk space usage.<br /> <br /><br />
{::nomarkdown}<iframe style="display: inline-block;" src="https://ghbtns.com/github-btn.html?user=shirosaidev&repo=diskover&type=star&count=true&size=large" frameborder="0" scrolling="0" width="160px" height="30px"></iframe> <iframe style="display: inline-block;" src="https://ghbtns.com/github-btn.html?user=shirosaidev&repo=diskover&type=fork&count=true&size=large" frameborder="0" scrolling="0" width="158px" height="30px"></iframe>{:/nomarkdown}'
feature_row:
  - url: https://github.com/shirosaidev/diskover-web/blob/master/docs/diskover-web-filetree-screenshot.png?raw=true
    image_path: https://github.com/shirosaidev/diskover-web/blob/master/docs/diskover-web-filetree-screenshot.png?raw=true
    alt: "file system crawler"
    title: "File System Crawler"
    excerpt: "diskover crawls your storage servers locally or over NFS/SMB and scrapes file/directory meta data into Elasticsearch."
    url: "https://github.com/shirosaidev/diskover"
    btn_class: "btn--primary"
    btn_label: "Learn More"
  - url: https://github.com/shirosaidev/diskover-web/blob/master/docs/diskover-web-dashboard-screenshot.png?raw=true
    image_path: https://github.com/shirosaidev/diskover-web/blob/master/docs/diskover-web-dashboard-screenshot.png?raw=true
    alt: "analyze metadata"
    title: "Visualize Your Storage"
    excerpt: "Identify old and unused files and give better insights into data change, duplicate files and wasted disk space."
    url: "https://github.com/shirosaidev/diskover"
    btn_class: "btn--primary"
    btn_label: "Learn More"
  - url: https://github.com/shirosaidev/diskover-web/blob/master/docs/diskover-web-treemap-screenshot.png?raw=true
    image_path: https://github.com/shirosaidev/diskover-web/blob/master/docs/diskover-web-treemap-screenshot.png?raw=true
    alt: "open-source"
    title: "Open Source"
    excerpt: "Built using Python + PHP + HTML5 + Javascript + D3.js. diskover runs on Linux, macOS, and Windows."
    url: "https://github.com/shirosaidev/diskover"
    btn_class: "btn--primary"
    btn_label: "Learn More"
github:
  - excerpt: '{::nomarkdown}<iframe style="display: inline-block;" src="https://ghbtns.com/github-btn.html?user=shirosaidev&repo=diskover&type=star&count=true&size=large" frameborder="0" scrolling="0" width="160px" height="30px"></iframe> <iframe style="display: inline-block;" src="https://ghbtns.com/github-btn.html?user=shirosaidev&repo=diskover&type=fork&count=true&size=large" frameborder="0" scrolling="0" width="158px" height="30px"></iframe>
<script async defer src="https://buttons.github.io/buttons.js"></script>{:/nomarkdown}'
intro:
  - excerpt: '{::nomarkdown}Support the development&nbsp;<a class="btn btn--primary" href="https://www.patreon.com/shirosaidev" target="_blank" role="button"><i class="fa fa-heart" aria-hidden="true"></i> Sponsor Patreon</a>&nbsp;<a class="btn btn--primary" href="https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=CLF223XAS4W72" target="_blank" role="button"><i class="fa fa-credit-card" aria-hidden="true"></i> Donate PayPal</a>{:/nomarkdown}'
  - excerpt: '{::nomarkdown}<strong>For businesses interested in diskover enterprise version, please visit <a href="https://diskoverspace.com">https://diskoverspace.com</a> to learn more.</strong><br><br>Join the conversation, get support on <a href="https://join.slack.com/t/diskoverworkspace/shared_invite/enQtNzQ0NjE1Njk5MjIyLWI4NWQ0MjFhYzQyMTRhMzk4NTQ3YjBlYjJiMDk1YWUzMTZmZjI1MTdhYTA3NzAzNTU0MDc5NDA2ZDI4OWRiMjM">diskover Slack</a>.<br><br><a href="https://diskoverspace.com/diskover/">Create an account</a> to download and get your auth token to run diskover.{:/nomarkdown}'
---

{% include feature_row id="intro" type="center" %}

{% include feature_row %}

<h2>News/ Updates</h2>
<p>diskover v2 will be released soon (Q1 2021), please sign up and register at <a href="https://diskoverspace.com/diskover/">https://diskoverspace.com/diskover/</a> for updates and join diskover Slack. <strong>v1 will be discontinued soon and no longer supported.</strong></p>
<blockquote><h3><q>This is the first tool I've found that can index 7m files/2m directories in under 20 min</q></h3> -- linuxserver.io community member</blockquote>
<p><strong>diskover</strong> is an open source file system crawler and disk space usage software that uses <strong>Elasticsearch</strong> to index and manage data across heterogeneous storage systems. Using diskover, you are able to more effectively search and organize files and system administrators are able to manage storage infrastructure, efficiently provision storage, monitor and report on storage use, and effectively make decisions about new infrastructure purchases.</p>
<p>As the amount of file data generated by businesses continues to expand, the stress on expensive storage infrastructure, users and system administrators, and IT budgets continues to grow.</p>
<p>Using diskover, users can identify old and unused files and give better insights into data change, file duplication and wasted space. diskover supports crawling local file-systems or over NFS/SMB.</p>
<div align="center"><img src="https://github.com/shirosaidev/diskover/blob/master/docs/diskover-diagram1-dark.png?raw=true" alt="diskover diagram" width="800" height="525"/></div>
<h2>Screenshots</h2>
<table border="0">
  <tr>
    <td>See data change on your file system and identify hot spots<br />
      <a href="https://github.com/shirosaidev/diskover-web/blob/master/docs/diskover-web-hotdirs-screenshot.png?raw=true"><img src="https://github.com/shirosaidev/diskover-web/blob/master/docs/diskover-web-hotdirs-screenshot.png?raw=true" alt="diskover-web hotdirs" width="600" /></a></td>
    <td>Visualize your file system using one of the many analytics<br />
      <a href="https://github.com/shirosaidev/diskover-web/blob/master/docs/diskover-web-hardlinks-screenshot.png?raw=true"><img src="https://github.com/shirosaidev/diskover-web/blob/master/docs/diskover-web-hardlinks-screenshot.png?raw=true" alt="diskover-web filetree" width="600" /></a></td>
  </tr>
  <tr>
    <td>Tag files and directories using default and custom tags, export file lists<br />
      <a href="https://github.com/shirosaidev/diskover-web/blob/master/docs/diskover-web-searchresults-screenshot.png?raw=true"><img src="https://github.com/shirosaidev/diskover-web/blob/master/docs/diskover-web-searchresults-screenshot.png?raw=true" alt="diskover-web tagging" width="600" /></a></td>
    <td>Use the built-in rest-api to assist with tagged data cleanup/moving<br />
      <a href="https://github.com/shirosaidev/diskover-web/blob/master/docs/diskover-web-tags-screenshot.png?raw=true"><img src="https://github.com/shirosaidev/diskover-web/blob/master/docs/diskover-web-tags-screenshot.png?raw=true" alt="diskover-web tags" width="600" /></a></td>
  </tr>
  <tr>
    <td>Use pre-made or create custom smart searches<br />
      <a href="https://github.com/shirosaidev/diskover-web/blob/master/docs/diskover-web-smartsearches-screenshot.png?raw=true"><img src="https://github.com/shirosaidev/diskover-web/blob/master/docs/diskover-web-smartsearches-screenshot.png?raw=true" alt="diskover-web tagging" width="600" /></a></td>
    <td>Find duplicate files taking up disk space<br />
      <a href="https://github.com/shirosaidev/diskover-web/blob/master/docs/diskover-web-dupes-screenshot.png?raw=true"><img src="https://github.com/shirosaidev/diskover-web/blob/master/docs/diskover-web-dupes-screenshot.png?raw=true" alt="diskover-web dupes" width="600" /></a></td>
  </tr>
  <tr>
    <td>Quickly search all your storage servers<br />
      <a href="https://github.com/shirosaidev/diskover-web/blob/master/docs/diskover-web-advancedsearch-screenshot.png?raw=true"><img src="https://github.com/shirosaidev/diskover-web/blob/master/docs/diskover-web-advancedsearch-screenshot.png?raw=true" alt="diskover-web file search" width="600" /></a></td>
    <td>Use Elasticsearch query syntax to find files and directories<br />
      <a href="https://github.com/shirosaidev/diskover-web/blob/master/docs/diskover-web-simplesearch-screenshot.png?raw=true"><img src="https://github.com/shirosaidev/diskover-web/blob/master/docs/diskover-web-simplesearch-screenshot.png?raw=true" alt="diskover-web file search es query" width="600" /></a></td>
  </tr>
</table>
<table border="0">
  <tr>
    <td align="center" width="33%"><span style="font-size:18px;font-weight:bold;">OVA Files for VMware</span></td>
    <td align="center" width="33%"><span style="font-size:18px;font-weight:bold;">Runs on Amazon AWS/S3 Support</span></td>
    <td align="center" width="33%"><span style="font-size:18px;font-weight:bold;">Works with Docker</span></td>
  </tr>
  <tr>
    <td align="center"><img src="https://github.com/shirosaidev/diskover/blob/master/docs/_pages/vmware_logo_1.png?raw=true" alt="diskover ova vmware" width="156" height="153" /></td>
    <td align="center"><img src="https://github.com/shirosaidev/diskover/blob/master/docs/_pages/amazon_web_services_logo_aws.jpg?raw=true" alt="diskover aws" width="178" height="117" /></td>
    <td align="center"><img src="https://github.com/shirosaidev/diskover/blob/master/docs/_pages/docker_logo.png?raw=true" alt="diskover docker" width="200" height="133" /></td>
  </tr>
  <tr>
    <td>Patreon sponsors get access to OVA's which get diskover up and running quickly and easily. The OVA files can be imported into VMware, etc to get you crawling all your storage servers in less than an hour.</td>
    <td>diskover works on AWS using EC2 and Elasticsearch instances. Crawl bots can run locally and push file system meta data into your AWS ES cluster.</td>
    <td>Run diskover and diskover-web containers anywhere. Docker install instructions can be found on diskover github.</td>
  </tr>
</table>
<h2>diskover worker bots crawling file system (gource videos)</h2>
{::nomarkdown}<iframe width="560" height="315" src="https://www.youtube.com/embed/qKLJjZ0TMqA?rel=0" frameborder="0" allow="autoplay; encrypted-media" allowfullscreen></iframe>{:/nomarkdown}<br />
{::nomarkdown}<iframe width="560" height="315" src="https://www.youtube.com/embed/InlfK8GQ-kM?rel=0" frameborder="0" allow="autoplay; encrypted-media" allowfullscreen></iframe>{:/nomarkdown}
