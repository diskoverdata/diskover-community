#!/usr/bin/env python
#
# diskover_aws_es.py
#
# Diskover fs crawler AWS ES helper file
# Chris Park cpark16@gmail.com
# https://github.com/shirosaidev/diskover
#

from elasticsearch import Elasticsearch, helpers, RequestsHttpConnection
import os
import ConfigParser

# Load config file
config = ConfigParser.RawConfigParser()
dir_path = os.path.dirname(os.path.realpath(__file__))
config.read('%s/diskover.cfg'% dir_path)
aws_es_host = config.get('aws_es', 'host')
indexname = config.get('es_index', 'name')

#connect to our aws es cluster
es = Elasticsearch(
 hosts=[{'host': aws_es_host, 'port': 443}],
 use_ssl=True,
 verify_certs=True,
 connection_class=RequestsHttpConnection)

def pingCheck():
    if not es.ping():
        raise ValueError("Connection failed")

def indexCreate():
    #delete index if exists
    print '*** Checking for ES index'
    if es.indices.exists(index=indexname):
        print '*** ES index exists, deleting'
        es.indices.delete(index=indexname, ignore=[400, 404])
    #index mappings
    mappings = {
        "mappings": {
            "file": {
                "properties": {
                    "filename": {
                        "type": "keyword"
                    },
                    "extension": {
                        "type": "keyword"
                    },
                    "path_full": {
                        "type": "keyword"
                    },
                    "path_parent": {
                        "type": "keyword"
                    },
                    "filesize": {
                        "type": "long"
                    },
                    "owner": {
                        "type": "keyword"
                    },
                    "group": {
                        "type": "keyword"
                    },
                    "last_modified": {
                        "type": "date",
                        "format": "epoch_second"
                    },
                    "last_access": {
                        "type": "date",
                        "format": "epoch_second"
                    },
                    "last_change": {
                        "type": "date",
                        "format": "epoch_second"
                    },
                    "hardlinks": {
                        "type": "integer"
                    },
                    "inode": {
                        "type": "integer"
                    },
                    "indexing_date": {
                        "type": "date",
                        "format": "epoch_second"
                    }
                }
            }
        }
    }
    #create index
    print '*** Creating ES index'
    es.indices.create(index=indexname, body=mappings)

def indexAdd(jsondata):
    # bulk load index data
    print '*** Bulk loading to ES index'
    helpers.bulk(es, jsondata, index=indexname, doc_type='file')

if __name__ == '__main__':
    pingCheck()
