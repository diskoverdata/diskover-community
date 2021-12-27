# Diskover-web v2 Community Edition Change Log

# [2.0-rc.3] - 2021-12-26
### fixed
- select indices table not saving sort order or show number of entries setting on page reload
- issue when only single item on search results chart not showing bar in chart
### added
### changed
- chart colors for items in bar and pie charts now match on dashboard and file search


# [2.0-rc.2] - 2021-12-01
### fixed
- issue with setting ES_HTTPS to TRUE in config file or env var
- directory info at top of charts not displaying when hide tree enabled on search results
- extra fields field description not displaying correctly on view file/directory info page
- extra fields not showing true or false for bool values on search results and view info page
- extra fields showing Array when ES doc field is an array of associated arrays (object type) on search results and view info page
- issue with view info page file and full path links when file name contains spaces returning no search results
### added
- disk space bar chart next to drive icon in search results file tree
- percent on mouse over to search results and dashboard charts
- documentation link to help page
### changed
- set specific version of elastisearch php client in composer.json
- improved search results ui
    - file tree is now fixed when scrolling
- removed Docker files, use linuxserver.io diskover docker container on docker hub


# [2.0-rc.1] - 2021-10-08
- first community edition v2.0 rc release