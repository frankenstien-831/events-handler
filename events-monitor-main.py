import os
import sys
import time

from ocean_keeper.contract_handler import ContractHandler
from ocean_keeper.utils import get_account
from ocean_keeper.web3_provider import Web3Provider

from ocean_events_handler.keeper import Keeper
from ocean_events_handler.provider_events_monitor import ProviderEventsMonitor


def run_events_monitor():
    if len(sys.argv) < 4:
        print(f'provider-events-monitor requires 3 arguments, found {len(sys.argv)-1} arguments.\n'
              f'The required arguments are: \n'
              f'  keeper_url [http url pointing to the keeper node]'
              f'  artifacts_path [local folder that has the keeper contracts artifacts (abi files)]'
              f'  storage_path [path to save agreements data locally in a database file.]')

        sys.exit(-1)

    keeper_url = sys.argv[1]
    artifacts_path = os.path.expanduser(os.path.expandvars(sys.argv[2]))
    storage_path = os.path.expanduser(os.path.expandvars(sys.argv[3]))

    ContractHandler.artifacts_path = artifacts_path
    Web3Provider.get_web3(keeper_url)
    keeper = Keeper.get_instance(artifacts_path)
    account = get_account(0)
    monitor = ProviderEventsMonitor(keeper, storage_path, account)
    monitor.start_agreement_events_monitor()
    while True:
        time.sleep(5)


if __name__ == '__main__':
    run_events_monitor()
