
#  Copyright 2018 Ocean Protocol Foundation
#  SPDX-License-Identifier: Apache-2.0

import logging
import time

from ocean_keeper.keeper import Keeper
from ocean_keeper.utils import process_fulfill_condition
from ocean_keeper.web3_provider import Web3Provider

logger = logging.getLogger(__name__)


def fulfill_escrow_reward_condition(event, agreement_id, service_agreement, price, consumer_address,
                                    publisher_account, condition_ids, escrow_condition_id):
    """

    :param event: AttributeDict with the event data.
    :param agreement_id: id of the agreement, hex str
    :param service_agreement: ServiceAgreement instance
    :param price: Asset price, int
    :param consumer_address: ethereum account address of consumer, hex str
    :param publisher_account: Account instance of the publisher
    :param condition_ids: is a list of bytes32 content-addressed Condition IDs, bytes32
    :param escrow_condition_id: hex str the id of escrow reward condition at this `agreement_id`
    :return:
    """
    if not event:
        logger.warning(f'`fulfill_escrow_reward_condition` got empty event: '
                       f'event listener timed out.')
        return

    keeper = Keeper.get_instance()
    if keeper.condition_manager.get_condition_state(escrow_condition_id) > 1:
        logger.debug(
            f'escrow reward condition already fulfilled/aborted: '
            f'agreementId={agreement_id}, escrow reward conditionId={escrow_condition_id}'
        )
        return

    logger.debug(f"release reward (agreement {agreement_id}) after event {event}.")
    lock_id, access_id = condition_ids[:2]
    logger.debug(f'fulfill_escrow_reward_condition: '
                 f'agreementId={agreement_id}'
                 f'price={price}, {type(price)}'
                 f'consumer={consumer_address},'
                 f'publisher={publisher_account.address},'
                 f'conditionIds={condition_ids}')
    assert price == service_agreement.get_price(), 'price mismatch.'
    assert isinstance(price, int), f'price expected to be int type, got type "{type(price)}"'
    time.sleep(5)
    keeper = Keeper.get_instance()
    did_owner = keeper.agreement_manager.get_agreement_did_owner(agreement_id)
    args = (
        agreement_id,
        price,
        Web3Provider.get_web3().toChecksumAddress(did_owner),
        consumer_address,
        lock_id,
        access_id,
        publisher_account
    )
    process_fulfill_condition(args, keeper.escrow_reward_condition, escrow_condition_id, logger, keeper, 10)


fulfillEscrowRewardCondition = fulfill_escrow_reward_condition
