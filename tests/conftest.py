#  Copyright 2018 Ocean Protocol Foundation
#  SPDX-License-Identifier: Apache-2.0

import json
import os
import pathlib

import pytest
from ocean_keeper import Keeper
from ocean_keeper.contract_handler import ContractHandler
from ocean_keeper.utils import get_account
from ocean_keeper.web3_provider import Web3Provider

from ocean_events_handler.util import (get_config, get_keeper_path, get_storage_path,
                                       init_account_envvars)


def get_resource_path(dir_name, file_name):
    base = os.path.realpath(__file__).split(os.path.sep)[1:-1]
    if dir_name:
        return pathlib.Path(os.path.join(os.path.sep, *base, dir_name, file_name))
    else:
        return pathlib.Path(os.path.join(os.path.sep, *base, file_name))


@pytest.fixture(autouse=True)
def setup_all():
    config = get_config()
    keeper_url = config.keeper_url
    Web3Provider.init_web3(keeper_url)
    ContractHandler.set_artifacts_path(get_keeper_path(config))
    init_account_envvars()


@pytest.fixture
def provider_account():
    return get_publisher_account()


@pytest.fixture
def web3():
    return Web3Provider.get_web3(get_config().keeper_url)


@pytest.fixture
def keeper():
    return Keeper.get_instance()


@pytest.fixture
def storage_path():
    return get_storage_path(get_config())


def get_publisher_account():
    return get_account(0)


def get_consumer_account():
    return get_account(0)


def get_sample_ddo():
    path = get_resource_path('resources/ddo', 'ddo_sample.json')
    assert path.exists(), f"{path} does not exist!"
    with open(path, 'r') as file_handle:
        metadata = file_handle.read()
    return json.loads(metadata)
