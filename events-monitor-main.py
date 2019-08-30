import time

from ocean_keeper.contract_handler import ContractHandler
from ocean_keeper.utils import get_account
from ocean_keeper.web3_provider import Web3Provider
from ocean_keeper.keeper import Keeper

from ocean_events_handler.log import setup_logging
from ocean_events_handler.provider_events_monitor import ProviderEventsMonitor
from ocean_events_handler.util import get_config, get_keeper_path, init_account_envvars


def run_events_monitor():
    setup_logging()
    config = get_config()
    keeper_url = config.keeper_url
    artifacts_path = get_keeper_path(config)
    storage_path = config.get('resources', 'storage.path', fallback='./provider-events-monitor.db')

    ContractHandler.artifacts_path = artifacts_path
    web3 = Web3Provider.get_web3(keeper_url)
    keeper = Keeper.get_instance(artifacts_path)
    init_account_envvars()

    account = get_account(0)
    if account is None:
        raise AssertionError(f'Provider events monitor cannot run without a valid '
                             f'ethereum account. Account address was not found in the environment'
                             f'variable `PROVIDER_ADDRESS`. Please set the following evnironment '
                             f'variables and try again: `PROVIDER_ADDRESS`, `PROVIDER_PASSWORD`, '
                             f'and `PROVIDER_KEYFILE`.')
    if not account.password or not account.key_file:
        raise AssertionError(f'Provider events monitor cannot run without a valid '
                             f'ethereum account with a password and keyfile. Current account '
                             f'has password {account.password} and keyfile {account.key_file}.')

    monitor = ProviderEventsMonitor(keeper, web3, storage_path, account)
    monitor.start_agreement_events_monitor()
    while True:
        time.sleep(5)


if __name__ == '__main__':
    run_events_monitor()
