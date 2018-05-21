"""
Default test suite for the Skycoin Lykke integration.
"""

import docker
import logging
import os
import uuid
import socket
import errno
import time

service_prefix = 'lykke_sky'
services_started = dict()

logging.basicConfig()
log = logging.getLogger(service_prefix)


def setup():
    """
    Setup integration tests
    """
    testservice_name = testrun_service_name()
    testsuite_id = str(uuid.uuid1()).replace('-', '')
    services_started[testservice_name] = (testsuite_id, False)
    log.info('Initializing service : mongo')
    init_service('mongo', 'latest', 27017)
    log.info('Initializing service : redis')
    init_service('redis', '3.0.7-alpine', 6379)
    log.info('Initializing service : skycoin')
    skycoin_cmd_path = None
    gopath = os.getenv('GOPATH', None)
    if gopath:
        skycoin_cmd_path = os.path.join(
            gopath, *('src/github.com/skycoin/skycoin'.split('/'))
        )
    if skycoin_cmd_path is not None:
        init_service('skycoin/skycoin', 'develop', 6420)
    wait_for_all(services_started)


def teardown():
    """
    Unload launched services if no test suite is running.
    """
    del services_started[testrun_service_name()]
    if all(not key.startswith(service_prefix)
            for key in services_started):
        for service_name, (_, launched) in services_started.items():
            if launched:
                docker_dispose(service_name)


def testrun_service_name():
    """Name to register this test run as a service.

    Depends on operating-system process ID.
    """
    return '%s_%d' % (service_prefix, os.getpid())


def testrun_id():
    """
    Global identifier of this test run.
    """
    return services_started[test_run_service_name()][0]


def init_service(service_name, version, default_port, *args):
    """
    Ensure service is running. If not available run it with Docker.

    service_name : The name of the official Docker image used to run
                   the target service.
    default_port : Default service port. Usually matches the value
                   EXPOSE'd in Dockerfile.
    """
    try:
        port = int(os.getenv('PORT_' + service_name.upper(), default_port))
    except ValueError:
        port = default_port

    launched = False
    if not is_listening_at(port):
        args['ports']
        docker_run(
            service_name,
            tag=version,
            name=docker_service_name(),
            ports={'%s/tcp' % (defaultPort,): port}
        )
        launched = True
    services_started[service_name] = (port, launched)


def docker_service_name(service_name):
    """Name of the container running a service used by this test run, if any.
    """
    return '_'.join((service_prefix, testrun_id(), service_name))


def docker_run(service_name, name, **docker_options):
    """
    Run service in a Docker container.
    """
    client = docker.from_env()

    image_tag = docker_options.get('tag', 'latest')
    client.images.pull(service_name, image_tag)
    client.containers.run(
        '%s:%s' % (service_name, image_tag),
        detach=True,
        name=name,
        ports=docker_options.get('ports', dict())
    )


def docker_dispose(service_name):
    """
    Remove container used to run service
    """
    client = docker.from_env()
    container = client.containers.get(docker_service_name(service_name))
    container.stop()
    container.wait()
    container.remove()


def wait_for_all(services_started, max_retries=5):
    """
    Wait for all services to be available.
    """
    log.info(
        'Waiting for services started: %s',
        ', '.join(key for key, (_, launched) in services_started.items() if launched)
    )
    step = max_retries
    pending = services_started.keys()
    timeout = 0.01
    # FIXME: Signal instead of busy wait
    while step > 0 and len(pending) > 0:
        time.sleep(timeout)
        pending = [(service_name, port) for service_name, (port, launched) in services_started.items() if launched and not is_listening_at(port)]
        timeout = 3
        step -= 1
    if len(pending) > 0:
        log.warning(
            'Some services could not be started: %s',
            ', '.join('%s at %s' % entry for entry in pending)
        )
        return False
    log.info('All services started')
    return True


def is_listening_at(port):
    """
    Check whether there's a service listening at given port.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(("127.0.0.1", port))
    except socket.error as e:
        if e.errno == errno.EADDRINUSE:
            log.info("Listening ")
        else:
            # something else raised the socket.error exception
            print(e)
    s.close()
