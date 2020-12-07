# Diskover v2 Install Guide

Below is an install guide for diskover v2 and diskover-web v2. It is written for CentOS 7.x but could also be used as a rough-guide for how to install on Ubuntu or other Linux distros.

### Main requirements

* Python 3.5+
* Elasticsearch 7.x
* PHP 7 + PHP-FPM (fastcgi) (for diskover-web)
* Nginx (for diskover-web)

### Other notes

Disabling SELinux and using software firewall are optional and not required to run diskover.


## Installation How-to - diskover

1. Install CentOS 7.x (tested with CentOS 7.8 DVD iso using minimal install)
2. Disable SELINUX (optional, not required to run diskover, if you use selinux you will need to adjust the selinux policies to allow diskover to run)
```
vi /etc/sysconfig/selinux
change SELINUX to disabled
reboot now
```
3. Update Server
```
yum -y update
```
4. Install wget
```
yum -y install wget
```
5. Install Java 8 JDK (OpenJDK) (req. for ES)
```
yum -y install java-1.8.0-openjdk.x86_64
```
6. Install ElasticSearch 7.x
```
wget https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-7.9.2-x86_64.rpm
yum localinstall -y elasticsearch-7.9.2-x86_64.rpm
**Set JVM Configuration
vi /etc/elasticsearch/jvm.options
-Xms8g <-should be no more than 50% of Memory, up to 32g max
-Xmx8g <-should be no more than 50% of Memory, up to 32g max
**Set Firewall rules
firewall-cmd --add-port=9200/tcp --permanent
firewall-cmd --reload
**Update /etc/elasticsearch/elasticsearch.yml
path.data: *SSD path or other fast disk* /cache/elasticsearch/data
path.logs: *SSD path or other fast disk* /cache/elasticsearch/logs
bootstrap.memory_lock: true  *** uncomment
systemctl enable elasticsearch.service
systemctl start elasticsearch.service
systemctl status elasticsearch.service
```

7. Install Kibana 7.x
```
wget https://artifacts.elastic.co/downloads/kibana/kibana-7.9.2-x86_64.rpm
yum localinstall -y kibana-7.9.2-x86_64.rpm
vi /etc/kibana/kibana.yml
**Uncomment and set the following line:
server.host: "<host ip>"
**Set Firewall rules
firewall-cmd --add-port=5601/tcp --permanent
firewall-cmd --reload
systemctl enable kibana.service
systemctl start kibana.service
systemctl status kibana.service
```

8. Install Python 3 (Python 3.6.8), Pip and dev tools
```
yum -y install python3 python3-devel gcc
python3 -V
pip3 -V
```
9. Install diskover
```
** Extract diskover compressed file
tar -zxvf diskover-<version>.tar.gz -C /opt/
cd /opt
mv diskover-<version> diskover
cd diskover
pip3 install -r requirements.txt
mkdir ~/.config/diskover
cp config.yaml ~/.diskover/config.yaml
vi ~/.diskover/config.yaml (edit for your env, set Elasticsearch hostname/ip)
```
10. Mount your network storage (set up client connection to storage)
```
*** for NFS
yum -y install nfs-utils
mkdir /mnt/nfsstor1
mount -t nfs -o ro,noatime,nodiratime server_name:/export_name /mnt/nfsstor1
*** for SMB/CIFS
yum -y install cifs-utils
mkdir /mnt/smbstor1
mount -t cifs -o username=user_name //server_name/share_name /mnt/smbstor1
```

11. Run your first crawl
```
cd /opt/diskover
**start crawling
python3 diskover.py -i diskover-<indexname> <storage_top_dir>
```

## Installation How-to - diskover-web

1. Install Nginx
```
yum -y install epel-release yum-utils
yum -y install http://rpms.remirepo.net/enterprise/remi-release-7.rpm
yum -y install nginx
systemctl enable nginx
systemctl start nginx
systemctl status nginx
```

2. Install PHP 7 and PHP-FPM (fastcgi)
```
yum-config-manager --enable remi-php72
yum -y install php php-common php-fpm php-opcache php-pecl-mcrypt php-cli php-gd php-mysqlnd php-ldap php-pecl-zip php-xml php-xmlrpc php-mbstring php-json
vi /etc/php-fpm.d/www.conf
** change user = nginx and group = nginx
** uncomment and change listen.owner = nginx and listen.group = nginx
** change listen to listen = /var/run/php-fpm/php-fpm.sock
chown -R root:nginx /var/lib/php
systemctl enable php-fpm
systemctl start php-fpm
systemctl status php-fpm
```

3. Install diskover-web
```
** Extract diskover-web compressed file
tar -zxvf diskover-web-<version>.tar.gz -C /var/www/
mv /var/www/diskover-web-<version> /var/www/diskover-web
cd /var/www/diskover-web/src/diskover
cp Constants.php.sample Constants.php
vi Constants.php (diskover-web config file, edit for your env, set Elasticsearch hostname/ip)
cd /var/www/diskover-web/public
cp extrafields.txt.sample extrafields.txt
cp smartsearches.txt.sample smartsearches.txt
cp customtags.txt.sample customtags.txt
cp costanalysis.txt.sample costanalysis.txt
chmod 660 *.txt
chown -R nginx:nginx /var/www/diskover-web
vi /etc/nginx/conf.d/diskover-web.conf
*** add below text to diskover-web.conf

server {
        listen   8000;
        server_name  diskover-web;
        root   /var/www/diskover-web/public;
        index  index.php index.html index.htm;
        error_log  /var/log/nginx/error.log;
        access_log /var/log/nginx/access.log;
        location / {
            try_files $uri $uri/ /index.php?$query_string;
        }
        location ~ \.php(/|$) {
            try_files $uri =404;
            fastcgi_split_path_info ^(.+\.php)(/.+)$;
            fastcgi_pass unix:/var/run/php-fpm/php-fpm.sock;
            #fastcgi_pass 127.0.0.1:9000;
            fastcgi_index index.php;
            include fastcgi_params;
            fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
            fastcgi_param PATH_INFO $fastcgi_path_info;
            fastcgi_read_timeout 900;
            fastcgi_buffers 16 16k;
            fastcgi_buffer_size 32k;
        }
}

systemctl reload nginx
**open firewall ports for diskover-web
firewall-cmd --add-port=8000/tcp --permanent
firewall-cmd --reload
```
4. View index in diskover-web after crawl finishes
```
http://<host_ip>:8000/
```
