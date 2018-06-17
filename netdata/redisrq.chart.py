# -*- coding: utf-8 -*-
# Description: redis rq-dashboard netdata python.d module
# Author: Chris Park (shirosai)
# SPDX-License-Identifier: GPL-3.0+

from collections import namedtuple
from json import loads
from socket import gethostbyname, gaierror
from threading import Thread
try:
        from queue import Queue
except ImportError:
        from Queue import Queue

from bases.FrameworkServices.UrlService import UrlService

# default module values (can be overridden per job in `config`)
#update_every = 1
priority = 60000
retries = 60

METHODS = namedtuple('METHODS', ['get_data', 'url'])

ORDER = ['jobs', 'workers']

CHARTS = {
    'jobs': {
        'options': [None, 'RQ Jobs', 'count', 'jobs', 'redisrq.jobs', 'line'],
        'lines': [
            ['queued_jobs', 'queued', 'absolute'],
            ['failed_jobs', 'failed', 'absolute']
        ]},
    'workers': {
        'options': [None, 'RQ Workers', 'count', 'workers', 'redisrq.workers', 'area'],
        'lines': [
            ['worker_busy_count', 'busy', 'absolute'],
            ['worker_idle_count', 'idle', 'absolute'],
            ['worker_unknown_count', 'unknown', 'absolute']
        ]}
}


class Service(UrlService):
    def __init__(self, configuration=None, name=None):
        UrlService.__init__(self, configuration=configuration, name=name)
        self.order = ORDER
        self.definitions = CHARTS
        self.host = self.configuration.get('host', '127.0.0.1')
        self.port = self.configuration.get('port', 9181)
        self.scheme = self.configuration.get('scheme', 'http')

    def check(self):
        # We can't start if <host> AND <port> not specified
        if not (self.host and self.port):
            self.error('Host is not defined in the module configuration file')
            return False

        # Hostname -> ip address
        try:
            self.host = gethostbyname(self.host)
        except gaierror as error:
            self.error(str(error))
            return False

        # Add handlers (auth, self signed cert accept)
        self.url = '{scheme}://{host}:{port}'.format(scheme=self.scheme,
                                                         host=self.host,
                                                         port=self.port)
        # Add methods
        api_workers = self.url + '/workers.json'
        api_queues = self.url + '/queues.json'
        self.methods = [METHODS(get_data=self._get_overview_stats,
                                url=api_queues),
                        METHODS(get_data=self._get_overview_stats,
                                url=api_workers)
                        ]
        return UrlService.check(self)

    def _get_data(self):
        threads = list()
        queue = Queue()
        result = dict()

        for method in self.methods:
            th = Thread(target=method.get_data,
                        args=(queue, method.url))
            th.start()
            threads.append(th)

        for thread in threads:
            thread.join()
            result.update(queue.get())

        return result or None

    def _get_overview_stats(self, queue, url):
        """
        Format data received from http request
        :return: dict
        """

        raw_data = self._get_raw_data(url)

        if not raw_data:
            return queue.put(dict())
        data = loads(raw_data)
        data = data[0] if isinstance(data, list) else data

        to_netdata = fetch_data(raw_data=data)
        return queue.put(to_netdata)


def fetch_data(raw_data):
    data = dict()
    value = raw_data
    queue_count = 0
    queue_failed_count = 0
    worker_state_busy = 0
    worker_state_idle = 0
    worker_state_unknown = 0

    try:
        for queue in value['queues']:
            if queue['name'] == 'failed':
                queue_failed_count += queue['count']
            else:
                queue_count += queue['count']
            data['queued_jobs'] = queue_count
            data['failed_jobs'] = queue_failed_count
    except KeyError:
        pass

    try:
        for worker in value['workers']:
            if worker['state'] == 'busy':
                worker_state_busy += 1
            elif worker['state'] == 'idle':
                worker_state_idle += 1
            else:
                worker_state_unknown += 1
        data['worker_busy_count'] = worker_state_busy
        data['worker_idle_count'] = worker_state_idle
        data['worker_unknown_count'] = worker_state_unknown
    except KeyError:
        pass

    return data
