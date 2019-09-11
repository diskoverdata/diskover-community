from diskover import listen, version, config
from rq import Worker, Connection
from redis import exceptions
from datetime import datetime

import os
import socket
import diskover_bot_module
from diskover_bot_module import redis_conn

def write_heartbeat_file(heartbeat_filename, job_count):
    f = open(heartbeat_filename,"w")
    f.write(str(job_count))
    f.close


if __name__ == "__main__":
    # parse cli arguments into cliargs dictionary
    cliargs_bot = vars(diskover_bot_module.parse_cliargs_bot())
    host_worker_exists = False
    hostname = socket.gethostname()
    heartbeat_filename = 'heartbeat.txt'
    timeout = int(os.getenv('HEALTHCHECK_TIMEOUT', 90))

    with Connection(redis_conn):
        
        workers = Worker.all(redis_conn)

        for worker in workers:
            # Skip any worker that is not running on this host
            worker_host = worker.hostname.decode('UTF-8')
            if hostname == worker_host:
                host_worker_exists = True
                print("Worker exists on this host.")
            else:
                continue            

            # Skip any worker not doing a job
            job = worker.get_current_job_id()
            if job is None:
                continue
            
            job_count = worker.successful_job_count
            # Check heartbeat file exists
            if os.path.isfile(heartbeat_filename):
                # Check last touch of file
                time_since_last_touch = datetime.now().timestamp() - os.path.getmtime(heartbeat_filename)
                f = open(heartbeat_filename,"r")
                last_job_count = int(f.read())
                if (job_count == last_job_count):
                    if (time_since_last_touch > timeout):
                        print("Heatbeat timed out. No response for {}s.".format(timeout))
                        exit(1)
                    else:
                        print("Worker busy for last {}s.".format(time_since_last_touch))
                        exit(0)
                else:
                    # Update job count in heartbeat file
                    write_heartbeat_file(heartbeat_filename, job_count)
            else:
                # Create heartbeat file with job count
                write_heartbeat_file(heartbeat_filename, job_count)

        if not host_worker_exists:
            print("No running workers found on this host.")
            exit(1)
