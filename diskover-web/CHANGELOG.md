# Diskover-web v2 Community Edition Change Log

# [2.0.3] - 2022-07-20
### fixed
- view file info page file and full path links not finding any search results when file name has double quote " in name


# [2.0.2] - 2022-05-31
### added
- sqlite db checks


# [2.0.1] - 2022-04-04
### fixed
- directories with trailing whitespace not returning any search results


# [2.0] - 2022-03-26
### fixed
- minor bug fixes and improvements


# [2.0-rc.5] - 2022-03-15
### fixed
- multiple ES queries delay when typing text into search bar
- index fields getting added multiple times to filters and help page
- increasing MAX_INDEX setting in config not updating maxindex user browser cookie if set lower
- issue with select indices page and php warning message if new index not in cache
### added
- defaults for config
- DATABASE to default/sample config (Constants.php.sample), can be used to change sqlite database file path
### changed
- improved table text wrapping on search results page
- if any missing config items are not in Constants.php (web config file), a default config value gets set and a message gets printed in web server error log
- MAX_INDEX setting in default/sample config to 250
- increasing MAX_INDEX in config also increases it for all users who may have it set lower in browser cookie


# [2.0-rc.4] - 2022-02-18
### BREAKING CHANGES
- added MAX_INDEX, INDEXINFO_CACHETIME, NEWINDEX_CHECKTIME settings to default/sample web config file, copy to your config file
- password for diskover user required to be hashed and stored in separate sqlite db, you will be prompted to change password at next login, config passwords are just used for defaults
### fixed
- charts displaying more data than selected index
- reduced login time when many indices
- issue with not staying logged in and getting logged out before login time limit expires
- issue with extra field value text on file view info page not wrapping when text string is very long
- issue with extra field and object type not displaying correctly
- changing chart/tree filter settings such as SIZE_FIELD in config did not change until browser cookies were cleared
### added
- MAX_INDEX, INDEXINFO_CACHETIME, NEWINDEX_CHECKTIME to default/sample web config file, copy to your config file
- change password to settings page
- after deleting indices on select indices page, index list will reload automatically after 3 seconds
### changed
- user login password required to be hashed and stored in separate sqlite db
- reduced api calls to ES to check for new index info
- improved file/directory view info page for extra fields


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