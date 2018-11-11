#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""diskover - Elasticsearch file system crawler
diskover is a file system crawler that index's
your file metadata into Elasticsearch.
See README.md or https://github.com/shirosaidev/diskover
for more information.

Copyright (C) Chris Park 2017-2018
diskover is released under the Apache 2.0 license. See
LICENSE for the full license text.
"""

from diskover import dir_excluded, q_crawl, adaptive_batch, config, get_time
from diskover_bot_module import scrape_tree_meta
import socket
import subprocess
try:
    import queue as Queue
except ImportError:
    import Queue
import threading
import uuid
import json
import time
import sys
import os
import pickle
import struct


# dict to hold socket tasks
socket_tasks = {}
# list of socket client
clientlist = []
# lists to hold rq jobs proxy objects and their results
jobs = []
# dict to hold dirsizes from rq job results
dirsizes = {}

excdircount = 0


def socket_thread_handler(threadnum, q, cliargs, logger):
    """This is the socket thread handler function.
    It runs the command msg sent from client.
    """

    BUFF = 1024

    while True:

        try:
            c = q.get()
            clientsock, addr = c
            logger.debug(clientsock)
            logger.debug(addr)
            data = clientsock.recv(BUFF)
            data = data.decode('utf-8')
            logger.debug('received data: %s' % data)
            if not data:
                q.task_done()
                # close connection to client
                clientsock.close()
                logger.info("[thread-%s]: %s closed connection" % (threadnum, str(addr)))
                continue

            # check if ping msg
            if data == 'ping':
                logger.info("[thread-%s]: Got ping from %s" % (threadnum, str(addr)))
                # send pong reply
                message = b'pong'
                clientsock.send(message)
                logger.debug('sending data: %s' % message)
            else:
                # strip away any headers sent by curl
                data = data.split('\r\n')[-1]
                logger.info("[thread-%s]: Got command from %s" % (threadnum, str(addr)))
                # load json and store in dict
                command_dict = json.loads(data)
                logger.debug(command_dict)
                # run command from json data
                run_command(threadnum, command_dict, clientsock, cliargs, logger)

            q.task_done()
            # close connection to client
            clientsock.close()
            logger.info("[thread-%s]: %s closed connection" % (threadnum, str(addr)))

        except (ValueError, TypeError) as e:
            q.task_done()
            logger.error("[thread-%s]: Invalid JSON from %s: (%s)" % (threadnum, str(addr), e))
            message = b'{"msg": "error", "error": ' + e + b'}\n'
            clientsock.send(message)
            logger.debug(message)
            # close connection to client
            clientsock.close()
            logger.info("[thread-%s]: %s closed connection" % (threadnum, str(addr)))
            pass

        except socket.error as e:
            q.task_done()
            logger.error("[thread-%s]: Socket error (%s)" % (threadnum, e))
            # close connection to client
            clientsock.close()
            logger.info("[thread-%s]: %s closed connection" % (threadnum, str(addr)))
            pass


def recvall(sock, count):
    buf = b''
    while count:
        newbuf = sock.recv(count)
        if not newbuf: return None
        buf += newbuf
        count -= len(newbuf)
    return buf


def recv_one_message(sock):
    lengthbuf = recvall(sock, 4)
    if not lengthbuf:
        return None
    length, = struct.unpack('!I', lengthbuf)
    return recvall(sock, length)


def socket_thread_handler_twc(threadnum, q, q_kill, lock, rootdir, num_sep, level,
                              batchsize, cliargs, logger, reindex_dict):
    """This is the socket thread handler tree walk client function.
    Stream of directory listings (pickle) from diskover treewalk
    client connections are enqueued to redis rq queue.
    """
    global jobs
    global dirsizes
    global excdircount

    while True:

        try:

            c = q.get()
            clientsock, addr = c
            logger.debug(clientsock)
            logger.debug(addr)

            while True:
                data = recv_one_message(clientsock)
                #logger.debug(data)

                if not data:
                    break

                if data == b'SIGKILL' or data == 'SIGKILL':
                    q_kill.put(b'SIGKILL')
                    break

                data_decoded = pickle.loads(data)
                logger.debug(data_decoded)

                # enqueue to redis
                batch = []
                for root, dirs, files in data_decoded:
                    if len(dirs) == 0 and len(files) == 0 and not cliargs['indexemptydirs']:
                        lock.acquire(True)
                        excdircount += 1
                        lock.release()
                        continue
                    batch.append((root, dirs, files))
                    batch_len = len(batch)
                    if batch_len >= batchsize:
                        job = q_crawl.enqueue(scrape_tree_meta, args=(batch, cliargs, reindex_dict,))
                        lock.acquire(True)
                        jobs.append(job)
                        lock.release()
                        del batch[:]
                        if cliargs['adaptivebatch']:
                            batchsize = adaptive_batch(q_crawl, cliargs, batchsize)

                    # check if any jobs have returned results and store in dirsizes dict
                    jobs_temp = jobs[:]
                    for j in jobs_temp:
                        if j.result:
                            lock.acquire(True)
                            for path, size in j.result.items():
                                dirsizes[path] = size
                            try:
                                jobs.remove(j)
                            except ValueError:
                                pass
                            lock.release()

                if len(batch) > 0:
                    # add any remaining in batch to queue
                    job = q_crawl.enqueue(scrape_tree_meta, args=(batch, cliargs, reindex_dict,))
                    lock.acquire(True)
                    jobs.append(job)
                    lock.release()
                    del batch[:]

            # close connection to client
            clientsock.close()
            logger.info("[thread-%s]: %s closed connection" % (threadnum, str(addr)))
            q.task_done()

        except socket.error as e:
            logger.error("[thread-%s]: Socket error (%s)" % (threadnum, e))


def start_socket_server(cliargs, logger):
    """This is the start socket server function.
    It opens a socket and waits for remote commands.
    """
    global clientlist

    # set thread/connection limit
    max_connections = config['listener_maxconnections']

    # Queue for socket threads
    q = Queue.Queue(maxsize=max_connections)

    try:
        # create TCP socket object
        serversock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serversock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        host = config['listener_host']  # default is localhost
        port = config['listener_port']  # default is 9999
        # bind to port
        serversock.bind((host, port))
        # start listener
        serversock.listen(max_connections)

        # set up the threads and start them
        for i in range(max_connections):
            # create thread
            t = threading.Thread(target=socket_thread_handler, args=(i, q, cliargs, logger,))
            t.daemon = True
            t.start()

        while True:
            logger.info("Waiting for connection, listening on %s port %s TCP (ctrl-c to shutdown)"
                        % (str(host), str(port)))
            # establish connection
            clientsock, addr = serversock.accept()
            logger.debug(clientsock)
            logger.debug(addr)
            logger.info("Got a connection from %s" % str(addr))
            # add client to list
            client = [clientsock, addr]
            clientlist.append(client)
            # add task to Queue
            q.put(client)

    except socket.error as e:
        serversock.close()
        logger.error("Error opening socket (%s)" % e)
        sys.exit(1)

    except KeyboardInterrupt:
        print('\nCtrl-c keyboard interrupt received, shutting down...')
        q.join()
        serversock.close()
        sys.exit(0)


def start_socket_server_twc(rootdir_path, num_sep, level, batchsize, cliargs, logger, reindex_dict):
    """This is the start socket server function.
    It opens a socket and waits for remote commands.
    """
    global clientlist
    global jobs
    global dirsizes
    global excdircount

    # set thread/connection limit
    max_connections = config['listener_maxconnections']

    # Queue for socket threads
    q = Queue.Queue(maxsize=max_connections)
    q_kill = Queue.Queue()
    lock = threading.Lock()

    try:
        # create TCP socket object
        serversock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serversock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        host = config['listener_host']  # default is localhost
        port = config['listener_twcport']  # default is 9998
        # bind to port
        serversock.bind((host, port))

        # start listener
        serversock.listen(max_connections)

        # set up the threads and start them
        for i in range(max_connections):
            # create thread
            t = threading.Thread(target=socket_thread_handler_twc, args=(i, q, q_kill, lock, rootdir_path, num_sep,
                                                                     level, batchsize, cliargs, logger, reindex_dict,))
            t.daemon = True
            t.start()

        while True:
            if q_kill.qsize() > 0:
                logger.info("Received signal to shutdown socket server")
                q.join()
                serversock.close()
                # get jobs returned results and store in dirsizes dict
                for j in jobs:
                    while not j.result:
                        time.sleep(1)
                    for path, size in j.result.items():
                        dirsizes[path] = size
                return starttime, excdircount, dirsizes
            logger.info("Waiting for connection, listening on %s port %s TCP (ctrl-c to shutdown)"
                        % (str(host), str(port)))
            # establish connection
            clientsock, addr = serversock.accept()
            logger.debug(clientsock)
            logger.debug(addr)
            logger.info("Got a connection from %s" % str(addr))
            # add client to list
            client = [clientsock, addr]
            clientlist.append(client)
            # set start time to first connection
            if len(clientlist) == 1:
                starttime = time.time()
            # add task to Queue
            q.put(client)


    except socket.error as e:
        serversock.close()
        logger.error("Error opening socket (%s)" % e)
        sys.exit(1)

    except KeyboardInterrupt:
        print('\nCtrl-c keyboard interrupt received, shutting down...')
        serversock.close()
        sys.exit(0)


def run_command(threadnum, command_dict, clientsock, cliargs, logger):
    """This is the run command function.
    It runs commands from the listener socket
    using values in command_dict.
    """
    global socket_tasks
    global clientlist

    # try to get index name from command or use from diskover config file
    try:
        index = str(command_dict['index'])
    except KeyError:
        index = str(config['index'])
        pass
    # try to get worker batch size from command or use default
    try:
        batchsize = str(command_dict['batchsize'])
    except KeyError:
        batchsize = str(cliargs['batchsize'])
        pass
    # try to get adaptive batch option from command or use default
    try:
        adaptivebatch = str(command_dict['adaptivebatch'])
    except KeyError:
        adaptivebatch = str(cliargs['adaptivebatch'])
        pass

    try:
        action = command_dict['action']
        pythonpath = config['python_path']
        diskoverpath = config['diskover_path']

        # set up command for different action
        if action == 'crawl':
            path = command_dict['path']
            cmd = [pythonpath, diskoverpath, '-b', batchsize,
                   '-i', index, '-d', path, '-q']

        elif action == 'finddupes':
            cmd = [pythonpath, diskoverpath, '-b', batchsize,
                   '-i', index, '--finddupes', '-q']

        elif action == 'hotdirs':
            index2 = str(command_dict['index2'])
            cmd = [pythonpath, diskoverpath, '-b', batchsize,
                   '-i', index, '--hotdirs', index2, '-q']

        elif action == 'reindex':
            try:
                recursive = command_dict['recursive']
            except KeyError:
                recursive = 'false'
                pass
            path = command_dict['path']
            if recursive == 'true':
                cmd = [pythonpath, diskoverpath, '-b', batchsize,
                    '-i', index, '-d', path, '-R', '-q']
            else:
                cmd = [pythonpath, diskoverpath, '-b', batchsize,
                    '-i', index, '-d', path, '-r', '-q']

        elif action == 'kill':
            taskid = command_dict['taskid']
            logger.info("[thread-%s]: Kill task message received! (taskid:%s)",
                        threadnum, taskid)
            # do something here to kill task (future)
            message = b'{"msg": "taskkilled"}\n'
            clientsock.send(message)
            return

        else:
            logger.warning("Unknown action")
            message = b'{"error": "unknown action"}\n'
            clientsock.send(message)
            return

        # add adaptive batch
        if (adaptivebatch == "True" or adaptivebatch == "true"):
            cmd.append('-a')

        # run command using subprocess
        starttime = time.time()
        taskid = str(uuid.uuid4()).encode('utf-8')

        # start process
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # add process to socket_tasks dict
        socket_tasks[taskid] = process

        message = b'{"msg": "taskstart", "taskid": "' + taskid + b'"}\n'
        clientsock.send(message)

        logger.info("[thread-%s]: Running command (taskid:%s)",
                    threadnum, taskid.decode('utf-8'))
        logger.info(cmd)

        output, error = process.communicate()

        # send exit msg to client
        exitcode = str(process.returncode).encode('utf-8')
        logger.debug('Command output:')
        logger.debug(output.decode('utf-8'))
        logger.debug('Command error:')
        logger.debug(error.decode('utf-8'))
        elapsedtime = str(get_time(time.time() - starttime)).encode('utf-8')
        logger.info("Finished command (taskid:%s), exit code: %s, elapsed time: %s"
                    % (taskid.decode('utf-8'), exitcode.decode('utf-8'), elapsedtime.decode('utf-8')))
        message = b'{"msg": "taskfinish", "taskid": "%s", "exitcode": %s, "elapsedtime": "%s"}\n' \
                  % (taskid, exitcode, elapsedtime)
        clientsock.send(message)

    except ValueError:
        logger.warning("Value error")
        message = b'{"error": "value error"}\n'
        clientsock.send(message)
        pass

    except socket.error as e:
        logger.error("[thread-%s]: Socket error (%s)" % (threadnum, e))
        pass
