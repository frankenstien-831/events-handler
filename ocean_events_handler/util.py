import os
import site

from ocean_keeper import Keeper
from ocean_keeper.web3_provider import Web3Provider

from ocean_events_handler.config import Config


def get_config():
    return Config(filename=os.getenv('CONFIG_FILE', 'config.ini'))


def get_storage_path(config):
    return config.get('resources', 'storage.path', fallback='./provider-events-monitor.db')


def get_keeper_path(config):
    path = config.keeper_path
    if not os.path.exists(path):
        if os.getenv('VIRTUAL_ENV'):
            path = os.path.join(os.getenv('VIRTUAL_ENV'), 'artifacts')
        else:
            path = os.path.join(site.PREFIXES[0], 'artifacts')

    return path


def init_account_envvars():
    os.environ['PARITY_ADDRESS'] = os.getenv('PROVIDER_ADDRESS', '')
    os.environ['PARITY_PASSWORD'] = os.getenv('PROVIDER_PASSWORD', '')
    os.environ['PARITY_KEY'] = os.getenv('PROVIDER_KEY', '')
    os.environ['PARITY_KEYFILE'] = os.getenv('PROVIDER_KEYFILE', '')
    os.environ['PARITY_ENCRYPTED_KEY'] = os.getenv('PROVIDER_ENCRYPTED_KEY', '')


def keeper_instance():
    return Keeper.get_instance()


def web3():
    return Web3Provider.get_web3(get_config().keeper_url)
