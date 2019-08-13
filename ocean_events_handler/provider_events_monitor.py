#  Copyright 2018 Ocean Protocol Foundation
#  SPDX-License-Identifier: Apache-2.0

import logging
import os
import time
from datetime import datetime
from threading import Thread

import sys

from ocean_keeper.contract_handler import ContractHandler
from ocean_keeper.utils import get_account
from ocean_utils.agreements.service_agreement import ServiceAgreement
from ocean_utils.agreements.service_agreement_template import ServiceAgreementTemplate
from ocean_utils.agreements.service_types import ServiceTypes
from ocean_utils.agreements.utils import get_sla_template
from ocean_utils.did import id_to_did
from ocean_utils.did_resolver.did_resolver import DIDResolver
from ocean_keeper.web3_provider import Web3Provider
from ocean_events_handler.agreement_store.agreements import AgreementsStorage
from ocean_events_handler.event_handlers import accessSecretStore, lockRewardCondition
from ocean_events_handler.keeper import Keeper

logger = logging.getLogger(__name__)


class ProviderEventsMonitor:
    """Manage the main keeper events listeners necessary for processing service agreements.

    The entry point for processing an agreement's events is the `AgreementCreated` event.
    All other events (related to conditions) follow after the `AgreementCreated` event.

    This events Monitor is meant to handle generic agreements as described in the service section
    of a DDO. A DDO service must contain the agreement and conditions definitions that describe
    events of each condition including the contract name that emits the event.

    on init
        if not db or not db schema -> create db and schema
        determine LAST_N_BLOCKS (allow setting from outside using an env var)
        read agreements from local database since LAST_N_BLOCKS
            keep set of completed/fulfilled (all conditions fulfilled) agreements to avoid reprocessing during event processing
            process events for unfulfilled agreements

    in watcher loop
        get AgreementCreated events since LAST_N_BLOCKS or LAST_PROCESSED_BLOCK whichever is larger
            try to overlap LAST_PROCESSED_BLOCK when grabbing events so we don't miss any events

    on new agreement (AgreementCreated event)
        save agreement to db
        init agreement conditions with unfulfilled status
        watch condition events
            on each condition event
                update agreement condition status


    """
    _instance = None

    EVENT_WAIT_TIMEOUT = 3600
    LAST_N_BLOCKS = 400

    def __init__(self, keeper, storage_path, account):
        self._keeper = keeper
        self._storage_path = storage_path
        self._account = account
        self._web3 = Web3Provider.get_web3()
        self._db = AgreementsStorage(self._storage_path)

        self.known_agreement_ids = set()
        self.completed_ids = set()
        self.other_agreement_ids = set()

        # prepare condition names and events arguments dict
        sla_template = ServiceAgreementTemplate(template_json=get_sla_template())
        self.condition_names = [cond.name for cond in sla_template.conditions]
        self.event_to_arg_names = sla_template.get_event_to_args_map(self._keeper.contract_name_to_instance)

        db = self.db
        db.create_tables()
        # get largest block_number from db or `latest` if db has no data
        self.last_n_blocks = os.getenv('OCN_EVENTS_MONITOR_LAST_N_BLOCKS', self.LAST_N_BLOCKS)
        self.latest_block = self._web3.eth.blockNumber
        db_latest = db.get_latest_block_number() or self.latest_block
        self.latest_block = min(db_latest, self.latest_block)
        self.last_processed_block = 0
        logger.debug(f'starting events monitor: latest block number {self.latest_block}')

        self._monitor_is_on = False
        try:
            self._monitor_sleep_time = os.getenv('OCN_EVENTS_MONITOR_QUITE_TIME', 3)
        except ValueError:
            self._monitor_sleep_time = 3

        self._monitor_sleep_time = max(self._monitor_sleep_time, 3)

    @staticmethod
    def get_instance(keeper, storage_path, account):
        if not ProviderEventsMonitor._instance or ProviderEventsMonitor._instance.provider_account != account:
            ProviderEventsMonitor._instance = ProviderEventsMonitor(keeper, storage_path, account)

        return ProviderEventsMonitor._instance

    @property
    def db(self):
        return AgreementsStorage(self._storage_path)

    @property
    def provider_account(self):
        return self._account

    @property
    def is_monitor_running(self):
        return self._monitor_is_on

    def start_agreement_events_monitor(self):
        if self._monitor_is_on:
            return

        logger.debug(f'Starting the agreement events monitor.')
        t = Thread(
            target=self.run_monitor,
            daemon=True,
        )
        self._monitor_is_on = True
        t.start()
        logger.debug('started the agreement events monitor')

    def stop_monitor(self):
        self._monitor_is_on = False

    def process_pending_agreements(self, pending_agreements, conditions):
        logger.debug(f'processing pending agreements, there is {len(pending_agreements)} agreements to process.')
        for agreement_id in pending_agreements.keys():
            data = pending_agreements[agreement_id]
            did = data[0]
            consumer_address = data[5]
            block_number = data[6]
            unfulfilled_conditions = conditions[agreement_id].keys()
            self.process_condition_events(
                agreement_id,
                unfulfilled_conditions,
                did,
                consumer_address,
                block_number,
                new_agreement=False
            )

    def get_next_block_range(self):
        to_block = self._web3.eth.blockNumber
        if self.last_processed_block:
            block_range = self.last_processed_block - 1, to_block
        else:
            block_num = self.db.get_latest_block_number() or 0
            if block_num > to_block:
                block_num = to_block - self.last_n_blocks
            from_block = max(to_block - self.last_n_blocks, block_num)
            block_range = from_block, to_block

        logger.debug(f'next block range = {block_range}, latest block number: {to_block}')
        return block_range

    def do_first_check(self):
        db = self.db
        if not db.get_agreement_count():
            return

        block_num = db.get_latest_block_number()
        agreements, conditions = db.get_pending_agreements(block_num - self.last_n_blocks)
        self.process_pending_agreements(agreements, conditions)

    def run_monitor(self):
        self.do_first_check()
        while True:
            try:
                if not self._monitor_is_on:
                    return

                _from, _to = self.get_next_block_range()
                for event_log in self.get_agreement_events(_from, _to):
                    self._handle_agreement_created_event(event_log)

                self.last_processed_block = _to

            except Exception as e:
                logger.debug(f'Error processing event: {str(e)}')

            time.sleep(self._monitor_sleep_time)

    def get_agreement_events(self, from_block, to_block):
        event_filter = self._keeper.escrow_access_secretstore_template.get_event_filter_for_agreement_created(
            self._account.address, from_block, to_block)
        logger.debug(f'getting event logs in range {from_block} to {to_block} for provider address {self._account.address}')
        logs = event_filter.get_all_entries(max_tries=5)
        # event_filter.uninstall()
        return logs

    def _handle_agreement_created_event(self, event, *_):
        if not event or not event.args:
            return

        if self._account.address != event.args["_accessProvider"]:
            logger.debug(f'agreement event not for my address {self._account.address}, event provider address {event.args["_accessProvider"]}')
            return
        agreement_id = None
        try:
            agreement_id = self._web3.toHex(event.args["_agreementId"])
            ids = self.db.get_agreement_ids()
            if ids:
                # logger.info(f'got agreement ids: #{agreement_id}#, ##{ids}##, \nid in ids: {agreement_id in ids}')
                if agreement_id in ids:
                    logger.debug(f'handle_agreement_created: skipping service agreement {agreement_id} '
                                 f'because it already been processed before.')
                    return

            logger.debug(f'Start handle_agreement_created (agreementId {agreement_id}): event_args={event.args}')

            did = id_to_did(event.args["_did"])

            unfulfilled_conditions = ['lockReward', 'accessSecretStore', 'escrowReward']
            self.process_condition_events(
                agreement_id, unfulfilled_conditions, did, event.args['_accessConsumer'],
                event.blockNumber, new_agreement=True
            )

            logger.debug(f'handle_agreement_created()  (agreementId {agreement_id}) -- '
                         f'done registering event listeners.')
        except Exception as e:
            logger.error(f'Error in handle_agreement_created (agreementId {agreement_id}): {e}', exc_info=1)

    def _last_condition_fulfilled(self, _, agreement_id, cond_name_to_id):
        # update db, escrow reward status to fulfilled
        # log the success of this transaction
        db = self.db
        for cond, _id in cond_name_to_id.items():
            state = self._keeper.condition_manager.get_condition_state(_id)
            db.update_condition_status(agreement_id, cond, state)

        logger.info(f'Agreement {agreement_id} is completed, all conditions are fulfilled.')

    def process_condition_events(self, agreement_id, conditions, did,
                                 consumer_address, block_number, new_agreement=True):

        ddo = DIDResolver(self._keeper.did_registry).resolve(did)
        service_agreement = ServiceAgreement.from_ddo(ServiceTypes.ASSET_ACCESS, ddo)
        condition_def_dict = service_agreement.condition_by_name
        price = service_agreement.get_price()
        if new_agreement:
            start_time = int(datetime.now().timestamp())
            self.db.record_service_agreement(
                agreement_id, ddo.did, service_agreement.service_definition_id, price,
                ddo.metadata['base'].get('encryptedFiles'), consumer_address, start_time,
                block_number, ServiceTypes.ASSET_ACCESS,
                service_agreement.condition_by_name.keys()
            )

        condition_ids = service_agreement.generate_agreement_condition_ids(
            agreement_id=agreement_id,
            asset_id=ddo.asset_id,
            consumer_address=consumer_address,
            publisher_address=ddo.publisher,
            keeper=self._keeper
        )
        cond_order = ['accessSecretStore', 'lockReward', 'escrowReward']
        cond_to_id = {cond_order[i]: _id for i, _id in enumerate(condition_ids)}
        for cond in conditions:

            if cond == 'lockReward':
                self._keeper.lock_reward_condition.subscribe_condition_fulfilled(
                    agreement_id,
                    max(condition_def_dict['lockReward'].timeout, self.EVENT_WAIT_TIMEOUT),
                    lockRewardCondition.fulfillAccessSecretStoreCondition,
                    (agreement_id, ddo.did, service_agreement, consumer_address,
                     self._account, condition_ids[0]),
                    from_block=block_number
                )
            elif cond == 'accessSecretStore':
                self._keeper.access_secret_store_condition.subscribe_condition_fulfilled(
                    agreement_id,
                    max(condition_def_dict['accessSecretStore'].timeout, self.EVENT_WAIT_TIMEOUT),
                    accessSecretStore.fulfillEscrowRewardCondition,
                    (agreement_id, service_agreement, price, consumer_address, self._account,
                     condition_ids, condition_ids[2]),
                    from_block=block_number
                )
            elif cond == 'escrowReward':
                self._keeper.escrow_reward_condition.subscribe_condition_fulfilled(
                    agreement_id,
                    max(condition_def_dict['escrowReward'].timeout, self.EVENT_WAIT_TIMEOUT),
                    self._last_condition_fulfilled,
                    (agreement_id, cond_to_id),
                    from_block=block_number
                )


if __name__ == '__main__':
    if len(sys.argv) < 4:
        print(f'provider-events-monitor requires 3 arguments, found {len(sys.argv)-1} arguments.\n'
              f'The required arguments are: \n'
              f'  keeper_url [http url pointing to the keeper node]'
              f'  artifacts_path [local folder that has the keeper contracts artifacts (abi files)]'
              f'  storage_path [path to save agreements data locally in a database file.]')

        sys.exit(-1)

    keeper_url = sys.argv[1]
    artifacts_path = os.path.expanduser(os.path.expandvars(sys.argv[2]))
    storage_path = os.path.expanduser(os.path.expandvars(sys.argv[3]))

    ContractHandler.artifacts_path = artifacts_path
    Web3Provider.get_web3(keeper_url)
    keeper = Keeper.get_instance(artifacts_path)
    account = get_account(0)
    monitor = ProviderEventsMonitor(keeper, storage_path, account)
    monitor.start_agreement_events_monitor()
    while True:
        time.sleep(5)
