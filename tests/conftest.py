#  Copyright 2018 Ocean Protocol Foundation
#  SPDX-License-Identifier: Apache-2.0

import pytest
from ocean_keeper import Keeper
from ocean_keeper.contract_handler import ContractHandler
from ocean_keeper.utils import get_account
from ocean_keeper.web3_provider import Web3Provider

from ocean_events_handler.util import get_config, get_keeper_path, get_storage_path, init_account_envvars


@pytest.fixture(autouse=True)
def setup_all():
    config = get_config()
    keeper_url = config.keeper_url
    Web3Provider.get_web3(keeper_url)
    ContractHandler.artifacts_path = get_keeper_path(config)
    init_account_envvars()


@pytest.fixture
def provider_account():
    return get_publisher_account()


@pytest.fixture
def web3():
    return Web3Provider.get_web3(get_config().keeper_url)


@pytest.fixture
def keeper():
    return Keeper.get_instance(get_keeper_path(get_config()))


@pytest.fixture
def storage_path():
    return get_storage_path(get_config())


def get_publisher_account():
    return get_account(0)


def get_consumer_account():
    return get_account(0)
