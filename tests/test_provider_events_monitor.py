import time

from ocean_keeper.web3_provider import Web3Provider
from ocean_utils.agreements.service_agreement import ServiceAgreement

from ocean_events_handler.provider_events_monitor import ProviderEventsMonitor
from tests.conftest import get_consumer_account
from tests.resources.keeper_helpers import (get_conditions_status, get_registered_ddo, grant_access,
                                            lock_reward, place_order)


def test_init_events_monitor(keeper, web3, storage_path, provider_account):
    events_monitor = ProviderEventsMonitor(keeper, web3, storage_path, provider_account)
    assert events_monitor.last_n_blocks == events_monitor.LAST_N_BLOCKS
    assert (Web3Provider.get_web3().eth.blockNumber - events_monitor.latest_block) < 5
    assert events_monitor.last_processed_block == 0


def test_process_pending_agreements(keeper, web3, storage_path, provider_account):
    start_time = 0
    ddo = get_registered_ddo(provider_account, providers=[provider_account.address])
    did = ddo.did
    consumer = get_consumer_account()
    block_number = web3.eth.blockNumber
    block_number = block_number - 10 if block_number > 10 else block_number
    metadata = ddo.metadata
    encrypted_files = metadata['encryptedFiles']
    sa = ServiceAgreement.from_ddo('access', ddo)
    agr_1 = place_order(provider_account, ddo, consumer)
    agr_2 = place_order(provider_account, ddo, consumer)
    agr_3 = place_order(provider_account, ddo, consumer)
    pending_agreements = {
        agr_1: [
            did, 3, sa.get_price(), encrypted_files, start_time,
            consumer.address, block_number, 'access'
        ],
        agr_2: [
            did, 3, sa.get_price(), encrypted_files, start_time + 3000,
            consumer.address, block_number, 'access'
        ],
        agr_3: [
            did, 3, sa.get_price(), encrypted_files, start_time + 10000,
            consumer.address, block_number, 'access'
        ]

    }
    conditions = {
        agr_1: {'accessSecretStore': 1, 'lockReward': 2, 'escrowReward': 1},
        agr_2: {'accessSecretStore': 1, 'lockReward': 1, 'escrowReward': 1},
        agr_3: {'accessSecretStore': 2, 'lockReward': 2, 'escrowReward': 1}
    }
    balance = keeper.token.get_token_balance(consumer.address) / (2 ** 18)
    if balance < 20:
        keeper.dispenser.request_tokens(100, consumer)

    lock_reward(agr_1, sa, consumer)
    lock_reward(agr_3, sa, consumer)
    grant_access(agr_3, ddo, consumer, provider_account)
    event = keeper.access_secret_store_condition.subscribe_condition_fulfilled(
        agr_3, 35, None, (), wait=True
    )
    if not event:
        # check status
        cond_to_status = get_conditions_status(agr_3)
        print(f'agr_3 condition status: {cond_to_status}')
        if cond_to_status['accessSecretStore'] != 2:
            raise AssertionError(f'grant access failed for agreement {agr_3}')

    events_monitor = ProviderEventsMonitor(keeper, web3, storage_path, provider_account)
    events_monitor.process_pending_agreements(pending_agreements, conditions)

    keeper.access_secret_store_condition.subscribe_condition_fulfilled(
        agr_1, 15, None, (), wait=True
    )
    keeper.escrow_reward_condition.subscribe_condition_fulfilled(
        agr_1, 15, None, (), wait=True
    )
    keeper.escrow_reward_condition.subscribe_condition_fulfilled(
        agr_3, 15, None, (), wait=True
    )

    # check status of all agreements
    for agr_id in (agr_1, agr_3):
        cond_to_status = get_conditions_status(agr_1)
        assert [2, 2, 2] == list(cond_to_status.values()), \
            f'agr_id {agr_id}: some conditions were not fulfilled or ' \
            f'do not match the expected status. Conditions status are: {cond_to_status}'

    events_monitor.start_agreement_events_monitor()
    lock_reward(agr_2, sa, consumer)
    keeper.access_secret_store_condition.subscribe_condition_fulfilled(
        agr_2, 15, None, (), wait=True
    )
    keeper.escrow_reward_condition.subscribe_condition_fulfilled(
        agr_2, 15, None, (), wait=True
    )
    cond_to_status = get_conditions_status(agr_2)
    assert [2, 2, 2] == list(cond_to_status.values()), \
        f'agr_id {agr_id}: some conditions were not fulfilled or ' \
        f'do not match the expected status. Conditions status are: {cond_to_status}'

    events_monitor.stop_monitor()
    time.sleep(2)
