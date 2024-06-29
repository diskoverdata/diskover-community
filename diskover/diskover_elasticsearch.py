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

import sys
import os
import requests
import logging
import elasticsearch
from elasticsearch import helpers

from diskover_helpers import config, load_plugins


logger = logging.getLogger(__name__)

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
    # Check for env vars
    if os.getenv('ES_HTTPS') is not None:
        config['ES_HTTPS'] = os.getenv('ES_HTTPS').lower() in ('true', '1')
    if os.getenv('ES_HOST') is not None:
        config['ES_HOST'] = os.getenv('ES_HOST')
    if os.getenv('ES_PORT') is not None:
        config['ES_PORT'] = os.getenv('ES_PORT')
    if os.getenv('ES_USER') is not None:
        config['ES_USER'] = os.getenv('ES_USER')
    if os.getenv('ES_PASS') is not None:
        config['ES_PASS'] = os.getenv('ES_PASS')
    if os.getenv('ES_SSLVERIFICATION') is not None:
        config['ES_SSLVERIFICATION'] = os.getenv('ES_SSLVERIFICATION').lower() in ('true', '1')
    
    if config['ES_USER'] is None:
        config['ES_USER'] = ""
    if config['ES_PASS'] is None:
        config['ES_PASS'] = ""

    # Check if we are using HTTP TLS/SSL
    if os.getenv('ES_HTTPS') == 'true' or config['ES_HTTPS']:
        es = elasticsearch.Elasticsearch(
            hosts=config['ES_HOST'],
            port=config['ES_PORT'],
            http_auth=(config['ES_USER'], config['ES_PASS']),
            scheme="https", use_ssl=True, verify_certs=config['ES_SSLVERIFICATION'],
            timeout=config['ES_TIMEOUT'], maxsize=config['ES_MAXSIZE'],
            max_retries=config['ES_MAXRETRIES'], retry_on_timeout=True, http_compress=config['ES_HTTPCOMPRESS'])
    # Local connection to es
    else:
        es = elasticsearch.Elasticsearch(
            hosts=config['ES_HOST'],
            port=config['ES_PORT'],
            http_auth=(config['ES_USER'], config['ES_PASS']),
            scheme="http", use_ssl=False, verify_certs=False,
            timeout=config['ES_TIMEOUT'], maxsize=config['ES_MAXSIZE'],
            max_retries=config['ES_MAXRETRIES'], retry_on_timeout=True, http_compress=config['ES_HTTPCOMPRESS'])
    
    if not es.ping():
        print('Failed to connect to Elasticsearch.')
        sys.exit(1)
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
                            'word_filter',
                            'lowercase'
                        ]
                    },
                    'path_analyzer': {
                        'tokenizer': 'path_tokenizer',
                        'filter': [
                            'word_filter',
                            'lowercase'
                        ]
                    }
                },
                'filter': {
                    'word_filter': {
                        'type': 'word_delimiter_graph',
                        'generate_number_parts': 'false',
                        'stem_english_possessive': 'false',
                        'split_on_numerics': 'false',
                        'catenate_all': 'true',
                        'preserve_original': 'true'
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
                'free_percent': {
                    'type': 'float'
                },
                'available': {
                    'type': 'long'
                },
                'available_percent': {
                    'type': 'float'
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
    if config['ES_WAIT']:
        # wait for es health to be at least yellow
        es.cluster.health(wait_for_status='yellow', request_timeout=config['ES_TIMEOUT'])

    # bulk load data to Elasticsearch index
    helpers.bulk(es, docs, index=indexname,
                    chunk_size=config['ES_CHUNKSIZE'], request_timeout=config['ES_TIMEOUT'], stats_only=True)


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
            "refresh_interval": config['ES_INDEXREFRESH'],
            "number_of_replicas": 0,
            "translog.flush_threshold_size": config['ES_TRANSLOGSIZE'],
            "translog.durability": "async",
            "translog.sync_interval": config['ES_TRANSLOGSYNCINT']
        }
    }
    if not defaults:
        logger.info("Tuning index settings for crawl")
        es.indices.put_settings(index=indexname, body=tuned_settings,
                                request_timeout=config['ES_TIMEOUT'])
    else:
        logger.info("Setting index settings back to defaults")
        es.indices.put_settings(index=indexname, body=default_settings,
                                request_timeout=config['ES_TIMEOUT'])