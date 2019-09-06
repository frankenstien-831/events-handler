import json
import logging
import uuid

from eth_utils import remove_0x_prefix
from ocean_utils.agreements.service_agreement import ServiceAgreement
from ocean_utils.agreements.service_factory import ServiceDescriptor, ServiceFactory
from ocean_utils.agreements.service_types import ServiceTypes
from ocean_utils.aquarius.aquarius import Aquarius
from ocean_utils.ddo.ddo import DDO
from ocean_utils.ddo.metadata import MetadataMain
from ocean_utils.ddo.public_key_rsa import PUBLIC_KEY_TYPE_RSA
from ocean_utils.did import DID, did_to_id, did_to_id_bytes
from ocean_utils.utils.utilities import checksum
from secret_store_client.client import Client as SecretStore

from ocean_events_handler.util import get_config, keeper_instance, web3
from tests.conftest import get_sample_ddo


def get_registered_ddo(account, providers=None):
    keeper = keeper_instance()
    aqua = Aquarius('http://localhost:5000')
    metadata = get_sample_ddo()['service'][0]['attributes']
    metadata['main']['files'][0]['checksum'] = str(uuid.uuid4())
    ddo = DDO()
    ddo_service_endpoint = aqua.get_service_endpoint()

    metadata_service_desc = ServiceDescriptor.metadata_service_descriptor(metadata,
                                                                          ddo_service_endpoint)

    access_service_attributes = {"main": {
        "name": "dataAssetAccessServiceAgreement",
        "creator": account.address,
        "price": metadata[MetadataMain.KEY]['price'],
        "timeout": 3600,
        "datePublished": metadata[MetadataMain.KEY]['dateCreated']
    }}

    service_descriptors = [ServiceDescriptor.authorization_service_descriptor(
        'http://localhost:12001')]
    service_descriptors += [ServiceDescriptor.access_service_descriptor(
        access_service_attributes,
        'http://localhost:8030'
    )]

    service_descriptors = [metadata_service_desc] + service_descriptors

    services = ServiceFactory.build_services(service_descriptors)
    checksums = dict()
    for service in services:
        checksums[str(service.index)] = checksum(service.main)

    # Adding proof to the ddo.
    ddo.add_proof(checksums, account)

    did = ddo.assign_did(DID.did(ddo.proof['checksum']))

    access_service = ServiceFactory.complete_access_service(did,
                                                            'http://localhost:8030',
                                                            access_service_attributes,
                                                            keeper.escrow_access_secretstore_template.address,
                                                            keeper.escrow_reward_condition.address)
    for service in services:
        if service.type == 'access':
            ddo.add_service(access_service)
        else:
            ddo.add_service(service)

    ddo.proof['signatureValue'] = keeper.sign_hash(did_to_id_bytes(did), account)

    ddo.add_public_key(did, account.address)

    ddo.add_authentication(did, PUBLIC_KEY_TYPE_RSA)

    encrypted_files = do_secret_store_encrypt(
        remove_0x_prefix(ddo.asset_id),
        json.dumps(metadata['main']['files']),
        account,
        get_config()
    )
    _files = metadata['main']['files']
    # only assign if the encryption worked
    if encrypted_files:
        index = 0
        for file in metadata['main']['files']:
            file['index'] = index
            index = index + 1
            del file['url']
        metadata['encryptedFiles'] = encrypted_files

    keeper_instance().did_registry.register(
        ddo.asset_id,
        checksum=web3().toBytes(hexstr=ddo.asset_id),
        url=ddo_service_endpoint,
        account=account,
        providers=providers
    )
    aqua.publish_asset_ddo(ddo)
    return ddo


def get_secret_store_client(account, config=None):
    config = get_config() if not config else config
    return SecretStore(
        config.secret_store_url,
        config.parity_url,
        account.address,
        account.password
    )


def do_secret_store_encrypt(did_id, document, provider_acc, config):
    secret_store = SecretStore(
        config.secret_store_url,
        config.parity_url,
        provider_acc.address,
        provider_acc.password
    )
    encrypted_document = secret_store.publish_document(did_id, document)
    return encrypted_document


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


def place_order(publisher_account, ddo, consumer_account):
    keeper = keeper_instance()
    agreement_id = ServiceAgreement.create_new_agreement_id()
    agreement_template = keeper.escrow_access_secretstore_template
    publisher_address = publisher_account.address
    service_agreement = ServiceAgreement.from_ddo(ServiceTypes.ASSET_ACCESS, ddo)
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
