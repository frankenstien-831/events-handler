from ocean_events_handler.provider_events_monitor import ProviderEventsMonitor
from ocean_utils.keeper.web3_provider import Web3Provider


def test_init_events_monitor(keeper, storage_path, provider_account):
    events_monitor = ProviderEventsMonitor(keeper, storage_path, provider_account)
    assert events_monitor.last_n_blocks == events_monitor.LAST_N_BLOCKS
    assert events_monitor.latest_block == Web3Provider.get_web3().eth.blockNumber
    assert events_monitor.last_processed_block == 0


def test_process_pending_agreements(keeper, storage_path, provider_account):
    events_monitor = ProviderEventsMonitor(keeper, storage_path, provider_account)
    start_time = 0
    urls = 'encrypted_urls'
    did = 'did:op:1234123412341234'
    consumer = '0x01'
    block_number = 10000
    pending_agreements = {
        '0x0': [
            did, 1, '20000000000000', urls, start_time,
            consumer, block_number, 'Access'
        ],
        '0x1': [
            did, 1, '28000000000000', urls, start_time+3000,
            consumer, block_number + 200, 'Access'
        ],
        '0x2': [
            did, 1, '40000000000000', urls, start_time+10000,
            consumer, block_number + 500, 'Access'
        ]

    }
    conditions = {
        '0x0': {'accessSecretStore': 1, 'lockReward': 2, 'escrowReward': 1},
        '0x1': {'accessSecretStore': 1, 'lockReward': 1, 'escrowReward': 1},
        '0x2': {'accessSecretStore': 2, 'lockReward': 2, 'escrowReward': 2}
    }
    events_monitor.process_pending_agreements(pending_agreements, conditions)



def test_get_next_block_range():
    pass


def test_do_first_check():
    pass


def test_get_agreement_events():
    pass


def test__handle_agreement_created_event():
    pass


def test_process_condition_events():
    pass


def test_monitor_thread():
    pass

