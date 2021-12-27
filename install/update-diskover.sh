#!/bin/sh
#
# diskover v2 community edition update script (ce)
# v0.2
# updates diskover v2 community edtion (ce) to latest version from github or local tar.gz file
#

### SET FOR YOUR ENV ###
DISKOVER_PATH=/opt/diskover
DISKOVER_WEB_PATH=/var/www/diskover-web
# set to true for github update or false for local tar.gz
GITHUB_UPDATE=true
# set to path of local update file if not updating via github
UPDATE_FILE=./diskover-v2-2.0-b.2.tar.gz
########################

echo
echo Updating diskover..
echo
rm -f /tmp/diskover-v2-update.tar.gz > /dev/null 2>&1
if [ "$GITHUB_UPDATE" = true ]
then
  if [ ! -d "/tmp/diskover_install" ]
  then
    git clone https://github.com/diskoverdata/diskover-community.git /tmp/diskover_install
    if [ $? -gt 0 ]; then echo "Error cloning github repo"; exit 1; fi
  else
    cd /tmp/diskover_install
    git pull
    if [ $? -gt 0 ]; then echo "Error updating cloned github repo"; exit 1; fi
  fi
  cd /tmp
else
  if [ ! -f "$UPDATE_FILE" ]; then echo "Error update file not found"; exit 1; fi
  cp $UPDATE_FILE /tmp/diskover-v2-update.tar.gz
  cd /tmp
  rm -rf diskover_update > /dev/null 2>&1
  mkdir diskover_update || exit 1
  tar -zxvf diskover-v2-update.tar.gz -C diskover_update/
  cd diskover_update/diskover-* || exit 1
fi
rsync -avu ./diskover/ $DISKOVER_PATH/
rsync -avu ./diskover-web/ $DISKOVER_WEB_PATH/
chown -R nginx:nginx $DISKOVER_WEB_PATH
echo
echo Update done.
echo Cleaning up...
cd /tmp
rm -rf diskover_update > /dev/null 2>&1
rm -f /tmp/diskover-v2-update.tar.gz > /dev/null 2>&1