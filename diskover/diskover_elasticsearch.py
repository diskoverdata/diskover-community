#!/usr/bin/env python3
"""
diskover community edition (ce)
https://github.com/diskoverdata/diskover-community/
https://diskoverdata.com

Copyright 2017-2021 Diskover Data, Inc.
"Community" portion of Diskover made available under the Apache 2.0 License found here:
https://www.diskoverdata.com/apache-license/
 
All other content is subject to the Diskover Data, Inc. end user license agreement found at:
https://www.diskoverdata.com/eula-subscriptions/
  
Diskover Data products and features for all versions found here:
https://www.diskoverdata.com/solutions/

"""

import os
import sys
import confuse
import requests
import logging
import elasticsearch
from elasticsearch import helpers
from elasticsearch.helpers.errors import BulkIndexError

from diskover_helpers import load_plugins


logger = logging.getLogger(__name__)

"""Load yaml config file."""
config = confuse.Configuration('diskover', __name__)

# check for any env vars to override config
try:
    es_host = os.getenv('ES_HOST', config['databases']['elasticsearch']['host'].get())
    es_port = os.getenv('ES_PORT', config['databases']['elasticsearch']['port'].get())
    es_user = os.getenv('ES_USER', config['databases']['elasticsearch']['user'].get())
    if not es_user:
        es_user = ""
    es_password = os.getenv('ES_PASS', config['databases']['elasticsearch']['password'].get())
    if not es_password:
        es_password = ""
    es_https = os.getenv('ES_HTTPS', config['databases']['elasticsearch']['https'].get())
    es_httpcompress = config['databases']['elasticsearch']['httpcompress'].get()
    es_timeout = config['databases']['elasticsearch']['timeout'].get()
    es_maxsize = config['databases']['elasticsearch']['maxsize'].get()
    es_max_retries = config['databases']['elasticsearch']['maxretries'].get()
    es_scrollsize = config['databases']['elasticsearch']['scrollsize'].get()
    es_wait_status_yellow = config['databases']['elasticsearch']['wait'].get()
    es_chunksize = config['databases']['elasticsearch']['chunksize'].get()
    es_translogsize = config['databases']['elasticsearch']['translogsize'].get()
    es_translogsyncint = config['databases']['elasticsearch']['translogsyncint'].get()
    es_indexrefresh = config['databases']['elasticsearch']['indexrefresh'].get()
except confuse.NotFoundError as e:
    print(
        'Config ERROR: {0}, check config for errors or missing settings from default config.'.format(e))
    sys.exit(1)

# load any available plugins
plugins = load_plugins()


def user_prompt(question):
    """Prompt the yes/no-*question* to the user."""
    from distutils.util import strtobool

    while True:
        try:
            user_input = input(question + " [y/n]: ").lower()
            result = strtobool(user_input)
            return result
        except ValueError:
            print("Please use y/n or yes/no.\n")
        except KeyboardInterrupt:
            print("Ctrl-c keyboard interrupt, exiting...")
            sys.exit(0)


def elasticsearch_connection():
    """Connect to Elasticsearch."""
    # Check if Elasticsearch is alive
    if es_https:
        scheme = 'https'
    # Local connection to es
    else:
        scheme = 'http'
    url = scheme + '://' + es_host + ':' + str(es_port)
    try:
        r = requests.get(url, auth=(es_user, es_password))
    except Exception as e:
        print(
            'Error connecting to Elasticsearch, check config and Elasticsearch is running.\n\nError: {0}'.format(e))
        sys.exit(1)

    # Check if we are using HTTP TLS/SSL
    if es_https:
        es = elasticsearch.Elasticsearch(
            hosts=es_host,
            port=es_port,
            http_auth=(es_user, es_password),
            scheme="https", use_ssl=True, verify_certs=True,
            connection_class=elasticsearch.RequestsHttpConnection,
            timeout=es_timeout, maxsize=es_maxsize,
            max_retries=es_max_retries, retry_on_timeout=True, http_compress=es_httpcompress)
    # Local connection to es
    else:
        es = elasticsearch.Elasticsearch(
            hosts=es_host,
            port=es_port,
            http_auth=(es_user, es_password),
            connection_class=elasticsearch.Urllib3HttpConnection,
            timeout=es_timeout, maxsize=es_maxsize,
            max_retries=es_max_retries, retry_on_timeout=True, http_compress=es_httpcompress)

    return es


def check_index_exists(indexname, es):
    """Check if index in Elasticsearch."""
    if es.indices.exists(index=indexname):
        return True
    return False


def create_index(indexname, es):
    """Create index in Elasticsearch."""

    # check for existing es index
    indexexists = check_index_exists(indexname, es)
    if indexexists:
        # delete existing index
        logger.info('ES index {0} already exists, deleting'.format(indexname))
        es.indices.delete(index=indexname, ignore=[400, 404])

    mappings = {
        'settings': {
            'index': {
                'number_of_shards': 1,
                'number_of_replicas': 0
            },
            'analysis': {
                'tokenizer': {
                    'filename_tokenizer': {
                        'type': 'char_group',
                        'tokenize_on_chars': [
                            'whitespace',
                            'punctuation',
                            '-',
                            '_'
                        ]
                    },
                    'path_tokenizer': {
                        'type': 'char_group',
                        'tokenize_on_chars': [
                            'whitespace',
                            'punctuation',
                            '/',
                            '-',
                            '_'
                        ]
                    }
                },
                'analyzer': {
                    'filename_analyzer': {
                        'tokenizer': 'filename_tokenizer',
                        'filter': [
                            'camel_filter',
                            'lowercase'
                        ]
                    },
                    'path_analyzer': {
                        'tokenizer': 'path_tokenizer',
                        'filter': [
                            'camel_filter',
                            'lowercase'
                        ]
                    }
                },
                'filter': {
                    'camel_filter': {
                        'type': 'word_delimiter_graph',
                        'generate_number_parts': 'false',
                        'stem_english_possessive': 'false',
                        'split_on_numerics': 'false'
                    }
                }
            }
        },
        'mappings': {
            'properties': {
                'name': {
                    'type': 'keyword',
                            'fields': {
                                'text': {
                                    'type': 'text',
                                    'analyzer': 'filename_analyzer'
                                }
                            }
                },
                'parent_path': {
                    'type': 'keyword',
                            'fields': {
                                'text': {
                                    'type': 'text',
                                    'analyzer': 'path_analyzer'
                                }
                            }
                },
                'size': {
                    'type': 'long'
                },
                'size_norecurs': {
                    'type': 'long'
                },
                'size_du': {
                    'type': 'long'
                },
                'size_du_norecurs': {
                    'type': 'long'
                },
                'file_count': {
                    'type': 'long'
                },
                'file_count_norecurs': {
                    'type': 'long'
                },
                'dir_count': {
                    'type': 'long'
                },
                'dir_count_norecurs': {
                    'type': 'long'
                },
                'dir_depth': {
                    'type': 'integer'
                },
                'owner': {
                    'type': 'keyword'
                },
                'group': {
                    'type': 'keyword'
                },
                'mtime': {
                    'type': 'date'
                },
                'atime': {
                    'type': 'date'
                },
                'ctime': {
                    'type': 'date'
                },
                'nlink': {
                    'type': 'integer'
                },
                'ino': {
                    'type': 'keyword'
                },
                'extension': {
                    'type': 'keyword'
                },
                'path': {
                    'type': 'keyword'
                },
                'total': {
                    'type': 'long'
                },
                'used': {
                    'type': 'long'
                },
                'free': {
                    'type': 'long'
                },
                'available': {
                    'type': 'long'
                },
                'file_size': {
                    'type': 'long'
                },
                'file_size_du': {
                    'type': 'long'
                },
                'file_count': {
                    'type': 'long'
                },
                'dir_count': {
                    'type': 'long'
                },
                'start_at': {
                    'type': 'date'
                },
                'end_at': {
                    'type': 'date'
                },
                'crawl_time': {
                    'type': 'float'
                },
                'diskover_ver': {
                    'type': 'keyword'
                },
                'type': {
                    'type': 'keyword'
                }
            }
        }
    }

    # check plugins for additional mappings
    for plugin in plugins:
        mappings = (plugin.add_mappings(mappings))

    try:
        es.indices.create(index=indexname, body=mappings)
    except elasticsearch.ConnectionError as e:
        print('ERROR: unable to connect to Elasticsearch! ({})'.format(e))
        sys.exit(1)
    return True


def bulk_upload(es, indexname, docs):
    """Elasticsearch Bulk uploader."""
    if es_wait_status_yellow:
        # wait for es health to be at least yellow
        es.cluster.health(wait_for_status='yellow', request_timeout=es_timeout)

    try:
        # bulk load data to Elasticsearch index
        helpers.bulk(es, docs, index=indexname,
                     chunk_size=es_chunksize, request_timeout=es_timeout)
    except BulkIndexError as e:
        logger.critical(
            'ERROR: Elasticsearch bulk index error! ({})'.format(e))
        raise BulkIndexError(e)


def tune_index(es, indexname, defaults=False):
    """Tune ES index for faster indexing performance."""
    default_settings = {
        "index": {
            "refresh_interval": "1s",
            "number_of_replicas": 0,
            "translog.flush_threshold_size": "512mb",
            "translog.durability": "request",
            "translog.sync_interval": "5s"
        }
    }
    tuned_settings = {
        "index": {
            "refresh_interval": es_indexrefresh,
            "number_of_replicas": 0,
            "translog.flush_threshold_size": es_translogsize,
            "translog.durability": "async",
            "translog.sync_interval": es_translogsyncint
        }
    }
    if not defaults:
        logger.info("Tuning index settings for crawl")
        es.indices.put_settings(index=indexname, body=tuned_settings,
                                request_timeout=es_timeout)
    else:
        logger.info("Setting index settings back to defaults")
        es.indices.put_settings(index=indexname, body=default_settings,
                                request_timeout=es_timeout)