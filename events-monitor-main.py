import time

from ocean_keeper.contract_handler import ContractHandler
from ocean_keeper.utils import get_account
from ocean_keeper.web3_provider import Web3Provider
from ocean_keeper.keeper import Keeper

from ocean_events_handler.provider_events_monitor import ProviderEventsMonitor
from ocean_events_handler.util import get_config, get_keeper_path


def run_events_monitor():
    config = get_config()
    keeper_url = config.keeper_url
    artifacts_path = get_keeper_path(config)
    storage_path = config.get('resources', 'storage.path', fallback='./provider-events-monitor.db')

    ContractHandler.artifacts_path = artifacts_path
    web3 = Web3Provider.get_web3(keeper_url)
    keeper = Keeper.get_instance(artifacts_path)
    account = get_account(0)
    monitor = ProviderEventsMonitor(keeper, web3, storage_path, account)
    monitor.start_agreement_events_monitor()
    while True:
        time.sleep(5)


if __name__ == '__main__':
    run_events_monitor()
