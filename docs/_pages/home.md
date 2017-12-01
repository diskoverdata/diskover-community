---
layout: splash
permalink: /
header:
  overlay_color: "#5e616c"
  overlay_image: /assets/images/mm-home-page-feature.jpg
  cta_label: "<i class='fa fa-download'></i> Install Now"
  cta_url: "https://github.com/shirosaidev/diskover/releases/latest"
  caption:
excerpt: 'diskover is a file system analytics application that includes a multi-threaded disk crawler that uses Elasticsearch to index your file metadata. diskover crawls and indexes your files on a local computer or remote server using NFS or SMB.<br />
File metadata is bulk added and streamed into Elasticsearch, allowing you to search and visualize your files in diskover-web or Kibana without having to wait until the crawl is finished. diskover is written in Python and runs on Linux and OS X/macOS.<br />
diskover aims to help manage your storage by identifying old and unused files and give better insights into data change "hotfiles", file duplication "dupes" and wasted space. It is designed to help deal with managing large amounts of data growth and provide detailed storage analytics.<br />
diskover includes a built-in UDP socket server for remote commands and also has plug-in support for expanding diskover's indexing capabilities.<br /> <small><a href="https://github.com/shirosaidev/diskover/releases/tag/1.4.0">Latest release v1.4.0</a></small><br /><br /> {::nomarkdown}<iframe style="display: inline-block;" src="https://ghbtns.com/github-btn.html?user=shirosaidev&repo=diskover&type=star&count=true&size=large" frameborder="0" scrolling="0" width="160px" height="30px"></iframe> <iframe style="display: inline-block;" src="https://ghbtns.com/github-btn.html?user=shirosaidev&repo=diskover&type=fork&count=true&size=large" frameborder="0" scrolling="0" width="158px" height="30px"></iframe>{:/nomarkdown}'
feature_row:
  - image_path: /assets/images/mm-customizable-feature.png
    alt: "customizable"
    title: "Super Customizable"
    excerpt: "Everything from the menus, sidebars, comments, and more can be configured or set with YAML Front Matter."
    url: "/docs/configuration/"
    btn_class: "btn--primary"
    btn_label: "Learn More"
  - image_path: /assets/images/mm-responsive-feature.png
    alt: "fully responsive"
    title: "Responsive Layouts"
    excerpt: "Built on HTML5 + CSS3. All layouts are fully responsive with helpers to augment your content."
    url: "/docs/layouts/"
    btn_class: "btn--primary"
    btn_label: "Learn More"
  - image_path: /assets/images/mm-free-feature.png
    alt: "100% free"
    title: "100% Free"
    excerpt: "Free to use however you want under the MIT License. Clone it, fork it, customize it, whatever!"
    url: "/docs/license/"
    btn_class: "btn--primary"
    btn_label: "Learn More"
github:
  - excerpt: '{::nomarkdown}<iframe style="display: inline-block;" src="https://ghbtns.com/github-btn.html?user=shirosaidev&repo=diskover&type=star&count=true&size=large" frameborder="0" scrolling="0" width="160px" height="30px"></iframe> <iframe style="display: inline-block;" src="https://ghbtns.com/github-btn.html?user=shirosaidev&repo=diskover&type=fork&count=true&size=large" frameborder="0" scrolling="0" width="158px" height="30px"></iframe>{:/nomarkdown}'
intro:
  - excerpt: 'Get notified when I add new stuff &nbsp; [<i class="fa fa-twitter"></i> @shirosaidev](https://twitter.com/shirosaidev){: .btn .btn--twitter} [<i class="fa fa-paypal"></i> Tip Me](https://www.paypal.me/shirosaidev){: .btn .btn--primary}'
---

{% include feature_row id="intro" type="center" %}

{% include feature_row %}
