#!/bin/sh
#
# diskover/diskover-web v2 installer script
# v0.5
# installs diskover v2 from ftp server or local tar.gz file
# Tested and working on Fresh Centos 8 install

### SET FOR YOUR ENV ###
FTPUSER=""
FTPPASS=''
DISKOVER_PATH=/opt/diskover
DISKOVER_WEB_PATH=/var/www/diskover-web
# set to true for ftp install or false for local tar.gz
FTP_INSTALL=true
# set to path of local install file if not installing via ftp
INSTALL_FILE=./diskover-v2-latest.tar.gz
# set to true or false for components you want to install
INSTALL_DISKOVER=true
INSTALL_DISKOVERWEB=true
INSTALL_ELASTICSEARCH=true
INSTALL_KIBANA=false
INSTALL_WEB_SERVER=true
# memory for Elasticsearch, Example 8g for 8 GB, ideal is 8 GB or more up to 32 GB max, use half of system memory
ES_MEM_HEAP="8g"
# ip to bind Elasticsearch to, default is localhost.
ES_BIND_IP="localhost"
# ip to bind Kibana to, default is localhost.
KIBANA_BIND_IP="localhost"
# port diskover-web will listen on, default is 8000.
WEB_SERVER_PORT="8000"
########################

echo
echo Installing...
echo

# check if running with sudo/root
if [ `id -u` -ne 0 ]; then echo "Please run as root/sudo"; exit 1; fi

# disable SE linux
sed -i 's/^SELINUX=.*$/SELINUX=disabled/' /etc/selinux/config
if [ $? -gt 0 ]; then echo "Error disabling SE linux"; exit 1; fi

yum -y update
if [ $? -gt 0 ]; then echo "Error running yum update"; exit 1; fi

#install and enable a few requirements
yum install -y wget
dnf install -y firewalld
systemctl enable firewalld
systemctl start firewalld

if [ "$INSTALL_ELASTICSEARCH" = true ]
then
    yum -y install java-1.8.0-openjdk.x86_64
    if [ $? -gt 0 ]; then echo "Error installing Java"; exit 1; fi
    yum install -y https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-7.10.2-x86_64.rpm
    if [ $? -gt 0 ]; then echo "Error installing Elasticsearch"; exit 1; fi
    firewall-cmd --add-port=9200/tcp --permanent
    firewall-cmd --reload
    sed -i "s/#-Xms1g/-Xms$ES_MEM_HEAP/" /etc/elasticsearch/jvm.options
    sed -i "s/#-Xmx1g/-Xmx$ES_MEM_HEAP/" /etc/elasticsearch/jvm.options
    if [ "$ES_BIND_IP" != "localhost" ]
    then
        sed -i "s/#network_host:.*$/network_host: \"$ES_BIND_IP\"/" /etc/elasticsearch/elasticsearch.yml
        sed -i "s/#discovery.seed_hosts:.*$/discovery.seed_hosts: [\"$ES_BIND_IP\"]/" /etc/elasticsearch/elasticsearch.yml
    fi
    sed -i 's/#bootstrap.memory_lock: true/bootstrap.memory_lock: true/' /etc/elasticsearch/elasticsearch.yml
    mkdir /etc/systemd/system/elasticsearch.service.d
    cat <<EOF > /etc/systemd/system/elasticsearch.service.d/elasticsearch.conf
[Service]
LimitMEMLOCK=infinity
LimitNPROC=4096
LimitNOFILE=65536
EOF
    systemctl enable elasticsearch.service
    systemctl start elasticsearch.service
fi

if [ "$INSTALL_KIBANA" = true ]
then
    yum install -y https://artifacts.elastic.co/downloads/kibana/kibana-7.10.2-x86_64.rpm
    if [ $? -gt 0 ]; then echo "Error installing Kibana"; exit 1; fi
    if [ "$KIBANA_BIND_IP" != "localhost" ]
    then
        sed -i "s/#server.host:.*$/server.host: \"$KIBANA_BIND_IP\"/" /etc/kibana/kibana.yml
    fi
    firewall-cmd --add-port=5601/tcp --permanent
    firewall-cmd --reload
    systemctl enable kibana.service
    systemctl start kibana.service
fi

if [ "$INSTALL_WEB_SERVER" = true ]
then
    # install nginx
    yum -y install yum-utils
    dnf -y install https://dl.fedoraproject.org/pub/epel/epel-release-latest-8.noarch.rpm
    yum -y install http://rpms.remirepo.net/enterprise/remi-release-8.rpm
    yum -y install nginx
    systemctl enable nginx
    # install PHP 7 and PHP-FPM (fastcgi)
    dnf -y module install php:remi-7.4
    yum -y install php php-common php-fpm php-opcache php-pecl-mcrypt php-cli php-gd php-mysqlnd php-ldap php-pecl-zip php-xml php-xmlrpc php-mbstring php-json
    sed -i 's/user =.*$/user = nginx/' /etc/php-fpm.d/www.conf
    sed -i 's/group =.*$/group = nginx/' /etc/php-fpm.d/www.conf
    sed -i 's/#listen.owner =.*$/listen.owner = nginx/' /etc/php-fpm.d/www.conf
    sed -i 's/#listen.group =.*$/listen.group = nginx/' /etc/php-fpm.d/www.conf
    sed -i 's/listen =.*$/listen = \/var\/run\/php-fpm\/php-fpm.sock/' /etc/php-fpm.d/www.conf
    chown -R root:nginx /var/lib/php
    systemctl enable php-fpm
    systemctl start php-fpm
fi

if [ "$INSTALL_DISKOVER" = true ]
then
    # install Python 3
    yum -y install python3 python3-devel gcc
    if [ "$FTP_INSTALL" = true ]
    then
        INSTALL_FILE=diskover-v2-latest.tar.gz
        wget --user=$FTPUSER --password=$FTPPASS ftp://diskoverspace.com/downloads/diskover_v2/latest/$INSTALL_FILE
        if [ $? -gt 0 ]; then echo "Error downloading"; exit 1; fi
    else
        if [ ! -f "$INSTALL_FILE" ]; then echo "Error install file not found"; exit 1; fi
    fi
    cp $INSTALL_FILE /tmp/diskover-v2-install.tar.gz
    cd /tmp
    mkdir diskover_install || exit 1
    tar -zxvf diskover-v2-install.tar.gz -C diskover_install/
    cd diskover_install/diskover-* || exit 1
    cp -a ./diskover/. $DISKOVER_PATH/
    if [ "$INSTALL_DISKOVERWEB" = true ]
    then
        cp -a ./diskover-web/. $DISKOVER_WEB_PATH/
        cd $DISKOVER_WEB_PATH/src/diskover
        cp Constants.php.sample Constants.php
        if [ "$ES_BIND_IP" != "localhost" ]
        then
            sed -i "s/ES_HOST =.*$/ES_HOST = '$ES_BIND_IP'/" Constants.php
        fi
        cd $DISKOVER_WEB_PATH/public
        for f in *.txt.sample; do cp $f "${f%.*}"; done
        chmod 660 *.txt
        cd $DISKOVER_WEB_PATH/public/tasks
        for f in *.json.sample; do cp $f "${f%.*}"; done
        chmod 660 *.json
        chown -R nginx:nginx $DISKOVER_WEB_PATH
echo 'server {
        listen   8000;
        server_name  diskover-web;
        root   /var/www/diskover-web/public;
        index  index.php index.html index.htm;
        error_log  /var/log/nginx/error.log;
        access_log /var/log/nginx/access.log;
        location / {
            try_files $uri $uri/ /index.php?$args =404;
        }
        location ~ \.php(/|$) {
            fastcgi_split_path_info ^(.+\.php)(/.+)$;
            set $path_info $fastcgi_path_info;
            fastcgi_param PATH_INFO $path_info;
            try_files $fastcgi_script_name =404; 
            fastcgi_pass unix:/var/run/php-fpm/php-fpm.sock;
            #fastcgi_pass 127.0.0.1:9000;
            fastcgi_index index.php;
            include fastcgi_params;
            fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
            include fastcgi_params;
            fastcgi_read_timeout 900;
            fastcgi_buffers 16 16k;
            fastcgi_buffer_size 32k;
        }
}' > /etc/nginx/conf.d/diskover-web.conf

        systemctl start nginx
        firewall-cmd --add-port=$WEB_SERVER_PORT/tcp --permanent
        firewall-cmd --reload
    fi
    cd $DISKOVER_PATH
    pip3 install -r $DISKOVER_PATH/requirements.txt
    sudo -i -u centos pip3 install -r $DISKOVER_PATH/requirements.txt
    for d in configs_sample/*; do d=`basename $d` && mkdir -p ~/.config/$d && cp configs_sample/$d/* ~/.config/$d/; done
    if [ "$ES_BIND_IP" != "localhost" ]
    then
        sed -i "s/host:.*$/host: $ES_BIND_IP/" ~/.config/diskover/config.yaml
    fi
fi

#create test php page
echo '<?php
phpinfo();' > /var/www/diskover-web/public/info.php

echo
echo Installation done.
echo Cleaning up...
echo after reboot point webpage to 'http://< diskover_web_host_ip >:8000/info.php' to confirm Installation

cd /tmp
rm -rf diskover_install > /dev/null 2>&1
rm -f /tmp/diskover-v2-install.tar.gz > /dev/null 2>&1
reboot