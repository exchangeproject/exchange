
"""Default test suite for the Skycoin Lykke integration.
"""

import logging
import os.path
import uuid
from .service_manager import *


TestSetupError = RuntimeError

StopServices = True
StartSkycoinNode = False

def setup():
    """Setup integration tests
    """
    try:
        skycoin_data_path = os.path.join(
                os.path.dirname(os.path.realpath(__file__)),
                *('data/skycoin'.split('/')))
        testservice_name = testrun_service_name()
        testsuite_id = str(uuid.uuid1()).replace('-', '')
        log.info('Starting test run %s' % (testservice_name,))
        services_started[testservice_name] = (testsuite_id, False)
        log.info('Initializing service : mongo')
        init_service('mongo',           '3.6.4-jessie', 27017)

        log.info('Initializing service : redis')
        init_service('redis',           '3.0.7-alpine', 6379)
        log.info('Initializing service : skycoin')
        skycoin_params = " -enable-wallet-api=true" \
                         " -db-path=/data/test/blockchain-180.db" \
                         " -download-peerlist=false" \
                         " -rpc-interface=true" \
                         " -db-read-only=true" \
                         " -disable-networking=true" \
                         " -web-interface-port=6420"
        init_service('skycoin/skycoin', 'develop',      6420, command=skycoin_params,
            volumes={skycoin_data_path: {'bind':'/data/test', 'mode' : 'rw'}})
        if StartSkycoinNode:
            skycoin_params = " -enable-wallet-api=true" \
                         " -db-path=/data/test/data.db" \
                         " -download-peerlist=false" \
                         " -rpc-interface=true" \
                         " -db-read-only=false" \
                         " -disable-networking=false" \
                         " -web-interface-port=6421"
            init_service('skycoin/skycoin', 'develop',      6421, command=skycoin_params,
                volumes={skycoin_data_path: {'bind':'/data/test', 'mode' : 'rw'}})
    except:
        log.error('Error found in test suite setup')
        raise
    finally:
        wait_for_all(services_started)


def teardown():
    """Unload launched services if no test suite is running.
    """
    if StopServices:
        testservice_name = testrun_service_name()
        log.info('Clean up after test run %s' % (testservice_name,))
        for service_id, (_, launched) in services_started.items():
            if service_id.startswith('_'.join((service_prefix, testrun_id()))) and launched:
                docker_dispose(service_id)
        del services_started[testservice_name]
