import json
import logging
import os
import pathlib

from ocean_utils.agreements.service_factory import ServiceDescriptor, ServiceFactory
from ocean_utils.ddo.metadata import MetadataBase
from ocean_utils.ddo.public_key_rsa import PUBLIC_KEY_TYPE_RSA
from secret_store_client.client import Client as SecretStore
from ocean_utils.agreements.service_agreement import ServiceAgreement
from ocean_utils.ddo.ddo import DDO
from ocean_utils.did import DID, did_to_id

from ocean_events_handler.util import keeper_instance, web3, get_config
from tests.resources.mocks.aquarius import AquariusMock


def new_ddo(metadata, account, keeper):
    did = DID.did()
    ddo_service_endpoint = AquariusMock.get_service_endpoint(did)
    _ddo = DDO(did)
    _ddo.add_public_key(did, account.address)
    _ddo.add_authentication(did, PUBLIC_KEY_TYPE_RSA)

    metadata['base']['checksum'] = _ddo.generate_checksum(did, metadata)
    checksum = metadata['base']['checksum']
    _ddo.add_proof(checksum, account, keeper.sign_hash(checksum, account))

    encrypted_files = secret_store_encrypt(did, json.dumps(metadata['base']['files']), account)
    index = 0
    for file in metadata['base']['files']:
        file['index'] = index
        index = index + 1
        del file['url']
    metadata['base']['encryptedFiles'] = encrypted_files

    service_descriptors = [
        ServiceDescriptor.metadata_service_descriptor(
            metadata, ddo_service_endpoint),
        ServiceDescriptor.authorization_service_descriptor(
            get_config().secret_store_url),
        ServiceDescriptor.access_service_descriptor(
            metadata[MetadataBase.KEY]['price'],
            'http://localhost:3030',
            'http://localhost:3030',
            3600,
            keeper.escrow_access_secretstore_template.address,
            keeper.escrow_reward_condition.address)
    ]
    for service in ServiceFactory.build_services(did, service_descriptors):
        _ddo.add_service(service)

    return _ddo


def get_registered_ddo(account, providers=None):
    keeper = keeper_instance()
    # _ddo = new_ddo(Metadata.get_example(), account, keeper)
    base = os.path.realpath(__file__).split(os.path.sep)[1:-1]
    path = pathlib.Path(os.path.join(os.path.sep, *base, 'data', 'ddo_sample.json'))
    with open(path, 'r') as file_handle:
        json_text = file_handle.read()

    did = DID.did()
    replacement_dict = {
        'owner_address': account.address,
        'did_id': did_to_id(did),
        'agreement_template_id': keeper.escrow_access_secretstore_template.address
    }
    json_text = json_text % replacement_dict
    _ddo = DDO(json_text=json_text)
    ddo_service_endpoint = AquariusMock.get_service_endpoint(did)

    text_for_sha3 = _ddo.metadata['base']['checksum'][2:]
    keeper.did_registry.register(
        _ddo.asset_id,
        checksum=web3().sha3(text=f'{text_for_sha3}'),
        url=ddo_service_endpoint,
        account=account,
        providers=providers
    )
    AquariusMock.publish_asset_ddo(_ddo)

    return _ddo


def get_secret_store_client(account, config=None):
    config = get_config() if not config else config
    return SecretStore(
        config.secret_store_url,
        config.parity_url,
        account.address,
        account.password
    )


def secret_store_encrypt(did, document, account):
    return get_secret_store_client(account).publish_document(
        did_to_id(did),
        document
    )


def secret_store_decrypt(did, encrypted_document, account):
    return get_secret_store_client(account).decrypt_document(
        did_to_id(did),
        encrypted_document
    )


def place_order(publisher_account, service_definition_id, ddo, consumer_account):
    keeper = keeper_instance()
    agreement_id = ServiceAgreement.create_new_agreement_id()
    agreement_template = keeper.escrow_access_secretstore_template
    publisher_address = publisher_account.address
    service_agreement = ServiceAgreement.from_ddo(service_definition_id, ddo)
    condition_ids = service_agreement.generate_agreement_condition_ids(
        agreement_id, ddo.asset_id, consumer_account.address, publisher_address, keeper)
    time_locks = service_agreement.conditions_timelocks
    time_outs = service_agreement.conditions_timeouts
    agreement_template.create_agreement(
        agreement_id,
        ddo.asset_id,
        condition_ids,
        time_locks,
        time_outs,
        consumer_account.address,
        consumer_account
    )

    return agreement_id


def lock_reward(agreement_id, service_agreement, consumer_account):
    keeper = keeper_instance()
    price = service_agreement.get_price()
    keeper.token.token_approve(keeper.lock_reward_condition.address, price, consumer_account)
    tx_hash = keeper.lock_reward_condition.fulfill(
        agreement_id, keeper.escrow_reward_condition.address, price, consumer_account)
    keeper.lock_reward_condition.get_tx_receipt(tx_hash)


def grant_access(agreement_id, ddo, consumer_account, publisher_account):
    keeper = keeper_instance()
    tx_hash = keeper.access_secret_store_condition.fulfill(
        agreement_id, ddo.asset_id, consumer_account.address, publisher_account
    )
    keeper.access_secret_store_condition.get_tx_receipt(tx_hash)


def get_condition_name(keeper, address):
    if keeper.lock_reward_condition.address == address:
        return 'lockReward'
    elif keeper.access_secret_store_condition.address == address:
        return 'accessSecretStore'
    elif keeper.escrow_reward_condition.address == address:
        return 'escrowReward'
    else:
        logging.error(f'The current address {address} is not a condition address')


def get_conditions_status(agreement_id):
    keeper = keeper_instance()
    condition_ids = keeper.agreement_manager.get_agreement(agreement_id).condition_ids
    conditions = dict()
    for i in condition_ids:
        name = get_condition_name(
            keeper,
            keeper.condition_manager.get_condition(i).type_ref
        )
        conditions[name] = keeper.condition_manager.get_condition_state(i)
    return conditions
