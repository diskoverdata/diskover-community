#!/usr/bin/env python3
"""
diskover community edition (ce)
https://github.com/diskoverdata/diskover-community/
https://diskoverdata.com

Copyright 2017-2024 Diskover Data, Inc.
"Community" portion of Diskover made available under the Apache 2.0 License found here:
https://www.diskoverdata.com/apache-license/
 
All other content is subject to the Diskover Data, Inc. end user license agreement found at:
https://www.diskoverdata.com/eula-subscriptions/
  
Diskover Data products and features for all versions found here:
https://www.diskoverdata.com/solutions/

"""

import os
import sys
import sqlite3
import json
import confuse
from distutils.util import strtobool
from config_defaults import conf

if os.name == 'nt':
    IS_WIN = True
else:
    IS_WIN = False


def db_connect():
    """Connect to sqlite db and return connection."""
    # Get database file path from config defaults
    dbfile = conf['DATABASE']
    # Check for env var
    if os.getenv('DATABASE') is not None:
        dbfile = os.getenv('DATABASE')

    # Open sqlite database
    try:
        con = sqlite3.connect(dbfile)
    except sqlite3.Error as e:
        print('There was an error connecting to the database! {}'.format(e))
        sys.exit(1)

    # Check database file is writable
    if not os.access(dbfile, os.W_OK):
        print('{} is not writable!'.format(dbfile))
        sys.exit(1)
    
    return con


def db_getconfig():
    """Get config from sqlite db and return config dictionary."""
    con = db_connect()
    cur = con.cursor()
    
    # Set up sqlite configdiskover table if does not yet exist.
    cur.execute("""CREATE TABLE IF NOT EXISTS configdiskover(
    id INTEGER PRIMARY KEY AUTOINCREMENT, 
    name TEXT NOT NULL, 
    value TEXT,
    UNIQUE(name)
    )""")
    con.commit()
    
    # Load any existing confuse config.yaml file
    config_confuse = confuse.Configuration('diskover', __name__)
    config_confuse_file = os.path.join(config_confuse.config_dir(), confuse.CONFIG_FILENAME)
    if os.path.exists(config_confuse_file):
        # Rename existing config to config.yaml.old
        try:
            os.rename(config_confuse_file, config_confuse_file + '.old')
        except:
            pass
        config_confuse = get_config(config_confuse)
    
    config_tups = []
    # Add any missing settings from config_defaults to configdiskover table.
    for name, value in conf.items():
        # check if in existing confuse config
        if config_confuse and name in config_confuse:
            config_tups.append((name, json.dumps(config_confuse[name])))
        else:
            config_tups.append((name, json.dumps(value)))
    cur.executemany("INSERT OR IGNORE INTO configdiskover ('name', 'value') VALUES(?, ?)", config_tups)
    con.commit()
    
    # Get all config settings from configdiskover table and add to config_dict
    config_dict = {}
    for name, value in cur.execute("SELECT name, value from configdiskover"):
        value = json.loads(value)
        if isinstance(value, str):
            # check if empty string
            if value == "":
                value = None
            # check if bool
            elif value == "true" or value == "false":
                value = bool(strtobool(value))
            # check if int
            elif value.isdigit():
                value = int(value)
            # float
            elif value.isnumeric():
                value = float(value)
        config_dict[name] = value
    
    cur.close()
    con.close()
    
    return config_dict


def get_config(config):
    """Get config items from confuse config and return dictionary."""
    config_confuse = {}
    
    try:
        config_confuse['LOGLEVEL'] = config['logLevel'].get()
    except confuse.NotFoundError:
        pass
    try:
        config_confuse['LOGTOFILE'] = config['logToFile'].get()
    except confuse.NotFoundError:
        pass
    try:
        config_confuse['LOGDIRECTORY'] = config['logDirectory'].get()
    except confuse.NotFoundError:
        pass
    try:
        config_confuse['MAXTHREADS'] = config['diskover']['maxthreads'].get()
        if config_confuse['MAXTHREADS'] is None:
            config_confuse['MAXTHREADS'] = int(os.cpu_count())
    except confuse.NotFoundError:
        pass
    try:
        config_confuse['BLOCKSIZE'] = config['diskover']['blocksize'].get()
    except confuse.NotFoundError:
        pass
    try:
        config_confuse['EXCLUDES_DIRS'] = config['diskover']['excludes']['dirs'].get()
    except confuse.NotFoundError:
        pass
    try:
        config_confuse['EXCLUDES_FILES'] = config['diskover']['excludes']['files'].get()
    except confuse.NotFoundError:
        pass
    try:
        config_confuse['EXCLUDES_EMPTYFILES'] = config['diskover']['excludes']['emptyfiles'].get()
    except confuse.NotFoundError:
        pass
    try:
        config_confuse['EXCLUDES_EMPTYDIRS'] = config['diskover']['excludes']['emptydirs'].get()
    except confuse.NotFoundError:
        pass
    try:
        config_confuse['EXCLUDES_MINFILESIZE'] = config['diskover']['excludes']['minfilesize'].get()
    except confuse.NotFoundError:
        pass
    try:
        config_confuse['EXCLUDES_CHECKFILETIMES'] = config['diskover']['excludes']['checkfiletimes'].get()
    except confuse.NotFoundError:
        pass
    try:
        config_confuse['EXCLUDES_MINMTIME'] = config['diskover']['excludes']['minmtime'].get() * 86400
    except confuse.NotFoundError:
        pass
    try:
        config_confuse['EXCLUDES_MAXMTIME'] = config['diskover']['excludes']['maxmtime'].get() * 86400
    except confuse.NotFoundError:
        pass
    try:
        config_confuse['EXCLUDES_MINCTIME'] = config['diskover']['excludes']['minctime'].get() * 86400
    except confuse.NotFoundError:
        pass
    try:
        config_confuse['EXCLUDES_MAXCTIME'] = config['diskover']['excludes']['maxctime'].get() * 86400
    except confuse.NotFoundError:
        pass
    try:
        config_confuse['EXCLUDES_MINATIME'] = config['diskover']['excludes']['minatime'].get() * 86400
    except confuse.NotFoundError:
        pass
    try:
        config_confuse['EXCLUDES_MAXATIME'] = config['diskover']['excludes']['maxatime'].get() * 86400
    except confuse.NotFoundError:
        pass
    try:
        config_confuse['INCLUDES_DIRS'] = config['diskover']['includes']['dirs'].get()
    except confuse.NotFoundError:
        pass
    try:
        config_confuse['INCLUDES_FILES'] = config['diskover']['includes']['files'].get()
    except confuse.NotFoundError:
        pass
    try:
        config_confuse['OWNERSGROUPS_UIDGIDONLY'] = config['diskover']['ownersgroups']['uidgidonly'].get()
    except confuse.NotFoundError:
        pass
    try:
        config_confuse['OWNERSGROUPS_DOMAIN'] = config['diskover']['ownersgroups']['domain'].get()
    except confuse.NotFoundError:
        pass
    try:
        config_confuse['OWNERSGROUPS_DOMAINSEP'] = config['diskover']['ownersgroups']['domainsep'].get()
    except confuse.NotFoundError:
        pass
    try:
        config_confuse['OWNERSGROUPS_DOMAINFIRST'] = config['diskover']['ownersgroups']['domainfirst'].get()
    except confuse.NotFoundError:
        pass
    try:
        config_confuse['OWNERSGROUPS_KEEPDOMAIN'] = config['diskover']['ownersgroups']['keepdomain'].get()
    except confuse.NotFoundError:
        pass
    try:
        config_confuse['REPLACEPATHS_REPLACE'] = config['diskover']['replacepaths']['replace'].get()
        if IS_WIN:
            config_confuse['REPLACEPATHS_REPLACE'] = True
    except confuse.NotFoundError:
        pass
    try:
        config_confuse['REPLACEPATHS_FROM'] = config['diskover']['replacepaths']['from'].get()
    except confuse.NotFoundError:
        pass
    try:
        config_confuse['REPLACEPATHS_TO'] = config['diskover']['replacepaths']['to'].get()
    except confuse.NotFoundError:
        pass
    try:
        config_confuse['PLUGINS_ENABLE'] = config['diskover']['plugins']['enable'].get()
    except confuse.NotFoundError:
        pass
    try:
        config_confuse['PLUGINS_DIRS'] = config['diskover']['plugins']['dirs'].get()
    except confuse.NotFoundError:
        pass
    try:
        config_confuse['PLUGINS_FILES'] = config['diskover']['plugins']['files'].get()
    except confuse.NotFoundError:
        pass
    try:
        config_confuse['RESTORETIMES'] = config['diskover']['other']['restoretimes'].get()
    except confuse.NotFoundError:
        pass
    try:
        config_confuse['ES_HOST'] = config['diskover']['databases']['elasticsearch']['host'].get()
    except confuse.NotFoundError:
        pass
    try:
        config_confuse['ES_PORT'] = config['diskover']['databases']['elasticsearch']['port'].get()
    except confuse.NotFoundError:
        pass
    try:
        config_confuse['ES_USER'] = config['diskover']['databases']['elasticsearch']['user'].get()
        if not config_confuse['ES_USER']:
            config_confuse['ES_USER'] = ""
    except confuse.NotFoundError:
        pass
    try:
        config_confuse['ES_PASS'] = config['diskover']['databases']['elasticsearch']['password'].get()
        if not config_confuse['ES_PASS']:
            config_confuse['ES_PASS'] = ""
    except confuse.NotFoundError:
        pass
    try:
        config_confuse['ES_HTTPS'] = config['diskover']['databases']['elasticsearch']['https'].get()
    except confuse.NotFoundError:
        pass
    try:
        config_confuse['ES_SSLVERIFICATION'] = config['diskover']['databases']['elasticsearch']['sslverification'].get()
    except confuse.NotFoundError:
        pass
    try:
        config_confuse['ES_HTTPCOMPRESS'] = config['diskover']['databases']['elasticsearch']['httpcompress'].get()
    except confuse.NotFoundError:
        pass
    try:
        config_confuse['ES_TIMEOUT'] = config['diskover']['databases']['elasticsearch']['timeout'].get()
    except confuse.NotFoundError:
        pass
    try:
        config_confuse['ES_MAXSIZE'] = config['diskover']['databases']['elasticsearch']['maxsize'].get()
    except confuse.NotFoundError:
        pass
    try:
        config_confuse['ES_MAXRETRIES'] = config['diskover']['databases']['elasticsearch']['maxretries'].get()
    except confuse.NotFoundError:
        pass
    try:
        config_confuse['ES_WAIT'] = config['diskover']['databases']['elasticsearch']['wait'].get()
    except confuse.NotFoundError:
        pass
    try:
        config_confuse['ES_CHUNKSIZE'] = config['diskover']['databases']['elasticsearch']['chunksize'].get()
    except confuse.NotFoundError:
        pass
    try:
        config_confuse['ES_INDEXREFRESH'] = config['diskover']['databases']['elasticsearch']['indexrefresh'].get()
    except confuse.NotFoundError:
        pass
    try:
        config_confuse['ES_TRANSLOGSIZE'] = config['diskover']['databases']['elasticsearch']['translogsize'].get()
    except confuse.NotFoundError:
        pass
    try:
        config_confuse['ES_TRANSLOGSYNCINT'] = config['diskover']['databases']['elasticsearch']['translogsyncint'].get()
    except confuse.NotFoundError:
        pass
    try:
        config_confuse['ES_SCROLLSIZE'] = config['diskover']['databases']['elasticsearch']['scrollsize'].get()
    except confuse.NotFoundError:
        pass
    
    return config_confuse