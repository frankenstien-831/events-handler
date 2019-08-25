import os

from ocean_keeper import Keeper
from ocean_keeper.web3_provider import Web3Provider

from ocean_events_handler.config import Config


def get_config():
    return Config(filename=os.getenv('CONFIG_FILE', 'config.ini'))


def get_storage_path(config):
    return config.get('resources', 'storage.path', fallback='./provider-events-monitor.db')


def get_keeper_path(config):
    path = config.keeper_path
    if not path or not os.path.exists(path) and os.getenv('VIRTUAL_ENV'):
        path = os.path.join(os.getenv('VIRTUAL_ENV'), 'artifacts')

    return path


def keeper_instance():
    return Keeper.get_instance(get_keeper_path(get_config()))


def web3():
    return Web3Provider.get_web3(get_config().keeper_url)


