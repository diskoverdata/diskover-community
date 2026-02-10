# Diskover Community Edition | Installation Instructions

## Requirements

- Python 3.8+
- PHP 8+
- Nginx
- Elasticsearch 8.x

## Download

```sh
git clone https://github.com/diskoverdata/diskover-community.git
```

- See [Releases](https://github.com/diskoverdata/diskover-community/releases) to download latest stable version in zip or tar format.
- Diskover Community Edition v2.3 linuxserver.io Docker container. Download on [Docker Hub](https://hub.docker.com/r/linuxserver/diskover) or [Github](https://github.com/linuxserver/docker-diskover).

## Supported Operating Systems

Diskover Community Edition can be installed on any Linux distribution that allows the requirements to be installed properly. However, our team actively suggests any RHEL 8/9 or Rocky Linux 8/9 distributions!

## Elasticsearch 8.X Installation

🔴 Install the Java OpenJDK packages:

```
yum -y install java-21-openjdk
```

🔴 Configure YUM repository for ES 8:

```
vi /etc/yum.repos.d/elasticsearch.repo
```
 
 🔴 Add the following to the file and save it:

```sh
[elasticsearch]
name=Elasticsearch repository for 8.x packages
baseurl=https://artifacts.elastic.co/packages/8.x/yum
gpgcheck=1
gpgkey=https://artifacts.elastic.co/GPG-KEY-elasticsearch
enabled=0
autorefresh=1
type=rpm-md
```

🔴 Install the latest ES 8 package:

```
yum -y install --disablerepo="*" --enablerepo=elasticsearch elasticsearch
```

🔴  ES Setting Modifications

```
vi /etc/elasticsearch/elasticsearch.yml
```

🔴 Ensure the following properties are set and uncommented:

```sh
cluster.name: <name of your cluster>        (Should be a distinctive name)
node.name: node-1                           (Can be named anything, but should be distinctive)
path.data: /var/lib/elasticsearch           (or some other custom ES data directory)
path.logs: /var/log/elasticsearch           (or some other custom ES logging directory)
bootstrap.memory_lock: true                 (lock RAM on startup)
network.host: 0.0.0.0                       (binds ES to all available IP addresses)
cluster.initial_master_nodes: ["node-1"]    (Should be set to the value you put for node.name above)
xpack.security.enabled: false               (disable security)
xpack.security.enrollment.enabled: false    (disable security enrollment on first boot)
xpack.ml.enabled: false                     (disable machine learning functionality - not needed)
```

🔴 ES memory lock:

```
vi /etc/elasticsearch/jvm.options.d/jvm.options
```

🔴 Ensure the JVM args are uncommented and set to 1/2 of your available RAM:

```sh
-Xms32g
-Xmx32g
```

🔴 ES SystemD Service memory settings:

```
mkdir /etc/systemd/system/elasticsearch.service.d
```

```
vi /etc/systemd/system/elasticsearch.service.d/elasticsearch.conf
```

🔴 Add the following to the file and save it:

```sh  
[Service]
LimitMEMLOCK=infinity
LimitNPROC=4096
LimitNOFILE=65536
```

🔴  Start and enable the ES service:

```sh
systemctl enable elasticsearch
systemctl start elasticsearch
```

🔴 Check the ES cluster health:

```sh
curl http://localhost:9200/_cluster/health?pretty
{
  "cluster_name" : "elasticsearch",
  "status" : "green",
  "timed_out" : false,
  "number_of_nodes" : 1,
  "number_of_data_nodes" : 1,
  "active_primary_shards" : 0,
  "active_shards" : 0,
  "relocating_shards" : 0,
  "initializing_shards" : 0,
  "unassigned_shards" : 0,
  "delayed_unassigned_shards" : 0,
  "number_of_pending_tasks" : 0,
  "number_of_in_flight_fetch" : 0,
  "task_max_waiting_in_queue_millis" : 0,
  "active_shards_percent_as_number" : 100.0
}
```

## Nginx Installation

🔴 Install Nginx:
```
yum -y install nginx
```

🔴 Enable and start the Nginx service:

```sh
systemctl enable nginx
systemctl start nginx
systemctl status nginx
```

## PHP Installation

🔴 Enable EPEL and REMI repositories -- *change the 8s to 9s if using RHEL / Rocky Linux 9*:

```sh
yum -y install https://dl.fedoraproject.org/pub/epel/epel-release-latest-8.noarch.rpm
yum -y install https://rpms.remirepo.net/enterprise/remi-release-8.rpm
```

🔴 Install PHP 8 packages:

```sh
yum -y install php84 php84-php-common php84-php-fpm php84-php-opcache \
php84-php-cli php84-php-gd php84-php-mysqlnd php84-php-ldap php84-php-pecl-zip \
php84-php-xml php84-php-mbstring php84-php-json php84-php-sqlite3
```

🔴 Copy in production `php.ini`:

```sh
cp /opt/remi/php84/root/usr/share/doc/php84-php-common/php.ini-production /etc/opt/remi/php84/php.ini 
        * This copy command may differ depending on your PHP8 install directory location
        * If this does not work, the below commands can be used to find the files that you need to copy

* Quick way to find your PHP install directory location: `php84 -i | grep 'Configuration File'`

find / -mount -name php.ini-production
  -- /opt/remi/php84/root/usr/share/dovi /etc/php84-php-common/php.ini-production
find / -mount -name php.ini
  -- /etc/opt/remi/php84/php.ini
```

🔴 Edit PHP-FPM configurations:

```
vi /etc/opt/remi/php84/php-fpm.d/www.conf
```

🔴 Ensure the following properties are set and uncommented:

```sh
user = nginx                                        (change user from 'apache') 
group = nginx                                       (change user from 'apache') 
listen = /var/opt/remi/php84/run/php-fpm/www.sock   (take note of this .sock location, you will need it later)
listen.owner = nginx                                (change user from 'nobody' and uncomment) 
listen.group = nginx                                (change user from 'nobody' and uncomment) 
;listen.acl_users = apache                          (ensure this is commented out with the ;)
```

🔴 PHP directories ownership:

```sh
chown -R root:nginx /var/opt/remi/php84/lib/php     (this command may differ depending on your PHP8 install directory)
mkdir /var/run/php-fpm
chown -R nginx:nginx /var/run/php-fpm
```

🔴 Create SystemD service file:
```
vi /etc/systemd/system/php-fpm.service
```

🔴 Add the following to the file and save it:

```sh
[Unit]
Description=PHP FastCGI process manager
After=local-fs.target network.target nginx.service

[Service]
PIDFile=/opt/php/php-fpm.pid
ExecStart=/opt/remi/php84/root/usr/sbin/php-fpm --fpm-config /etc/opt/remi/php84/php-fpm.conf --nodaemonize
Type=simple

[Install]
WantedBy=multi-user.target
```

🔴 Set permissions, enable and start the service:

```sh
chmod 644 /etc/systemd/system/php-fpm.service
systemctl daemon-reload
systemctl enable php-fpm
systemctl start php-fpm
systemctl status php-fpm
```

## Python Installation

Diskover Community Edition v2.3 requires at a minimum Python3.8 to be installed on the system. You can validate the Python3 version that was installed on your OS by default by running : `python3 -V` -- If this returns a version equal to or higher than 3.8, you can skip this section!

🔴 Install Python v3.12:

```
yum -y install python3.12 python3.12-devel gcc
```

🔴 Configure Python v3.12 for usage - there are a couple of options here:

- Call Python3.12 directly from Diskover and do nothing to the system level **Python3 executable (Recommended)**.
- **Symlink** Python3.12 in as the default Python3 executable on your OS.

### Diskover Python Executable

Using this approach, we will simply execute Diskover with the full path to our Python3.12 version : `/usr/bin/python3.12`

When we do a scan at the end of this install, we will use that full path instead of just `python3`

### Symlink

```sh
unlink /usr/bin/python3
ln -s /usr/bin/python3.12 /usr/bin/python3
which python3
python3 -V
```

The output of your `python3 -V` command should show a 3.12.X

⚠️ **WARNING!** Depending on your distributtion and version of Linux, modifying the system level Python3 executable version could have unintended consequences.

## Diskover Installation

Now that we've settled all the requirements to run the Diskover Community Edition, let's put the actual software in place. You'll want to get the code from this repository on the server you've been working on. Either by cloning this Git Repo directly on the server or pulling from our [Releases](https://github.com/diskoverdata/diskover-community/releases) page!

🔴 Uncompress the TAR:

```
tar -xvzf diskover-community-2.3.0.tar.gz
```

🔴 Move the Source Code:

```sh
cd diskover-community-2.3.0/
cp -a diskover /opt/
cp -a diskover-web /var/www/
```

🔴 Install the Python libraries:

```sh
/usr/bin/python3.12 -m ensurepip
/usr/bin/python3.12 -m pip install -r /opt/diskover/requirements.txt
```

🔴 Copy the Diskover-Web Nginx configuration:

```sh
mv /var/www/diskover-web/diskover-web.conf /etc/nginx/conf.d/
systemctl restart nginx php-fpm
systemctl status nginx php-fpm
chown -R nginx.nginx /var/www/diskover-web/
```

✏️ **NOTE!** You should now be able to hit your Diskover system at the IP address in the browser : **`http://IP:8000`** if this does not work initially and you get a 500 error, re-run that `chown` command above!

🔴 Default credentials to log in - you can change the password once logged in by going to **⚙️ → Settings**:

- Username: **diskover**
- Password: **darkdata**

## Execute a Scan Task

We have installed all of the necessary components for Diskover Community Edition. 

🔴 Let's run a scan of a folder on our local system and ensure things are working properly:

```
/usr/bin/python3.12 /opt/diskover/diskover.py -i diskover-test /opt/diskover
```

🔴 Now that your scan has completed.. Let's view the contents! 

- Go Back to Diskover Web `http://IP:8000`
- Click the **⚙️ → Settings** Icon in the Top-Right Corner
- Choose **Indices**
- Select the `diskover-test` Index and Choose `Save Selection`
- Click the **Dashboard** or **📁 File Search** Icon in the Top-Left Corner

You've now successfully installed the Diskover Community Edition v2.3.X!

## License

The Community Edition is free to use for an unlimited time and operates without the need for license keys, subject to the terms of the [Apache License](https://github.com/diskoverdata/diskover-community/blob/master/LICENSE)

## Community Support

If you have any questions feel free to reach out on our Community Slack Organization - [Diskover Slack Workspace](https://join.slack.com/t/diskoverworkspace/shared_invite/zt-2up4tjux2-eZYt1OFgCeA3kSFQfsU93A).

Please note that Diskover doesn't offer dedicated support for the free Community Edition.

## Feature Upgrade Information

- If you are a **home user**, the Community Edition is your best option as it is free to use for an unlimited time, and offers features to find and organize your data. The Diskover’s [subscription plans](https://diskoverdata.com/platforms/diskover-plans/) are designed for businesses, offering advanced features that exceed the budget of most home users.

- If you are a **business** trying out Diskover, please [contact us](https://diskoverdata.com/contact/) if would like to have more information regarding our [subscription options](https://diskoverdata.com/platforms/diskover-plans/).
  
