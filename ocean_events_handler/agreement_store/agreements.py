#  Copyright 2018 Ocean Protocol Foundation
#  SPDX-License-Identifier: Apache-2.0
import collections
import logging

from ocean_utils.data_store.storage_base import StorageBase

logger = logging.getLogger(__name__)


class DatabaseSchema:
    agreement_table = f'''
        CREATE TABLE IF NOT EXISTS agreement
            (agreement_id VARCHAR(70) PRIMARY KEY, did VARCHAR, service_index INTEGER, 
             price VARCHAR, urls VARCHAR, consumer VARCHAR(70), start_time INTEGER, 
             block_number INTEGER, type VARCHAR(100));
    '''

    agreement_condition_table = f'''
        CREATE TABLE IF NOT EXISTS agreement_condition
            (agreement_id VARCHAR(70),
             condition_name VARCHAR(100),
             status INTEGER,
             PRIMARY KEY (agreement_id, condition_name));
    '''

    SCHEMA = {
        'agreement': agreement_table,
        'agreement_condition': agreement_condition_table
    }


class AgreementsStorage(StorageBase):
    """
    Provide storage for SEA service agreements in an sqlite3 database.
    """

    def create_tables(self):
        for create_table_query in DatabaseSchema.SCHEMA.values():
            self._run_query(create_table_query)

    def record_service_agreement(self, agreement_id, did, service_index, price,
                                 urls, consumer, start_time, block_number,
                                 agreement_type, conditions):
        """
        Records the given pending service agreement.

        :param agreement_id: hex str the id of the service agreement used as primary key
        :param did: DID, str in the format `did:op:0xXXX`
        :param service_index: identifier of the service inside the asset DDO, str
        :param price: Asset price, int
        :param urls: hex str encrypted urls list
        :param start_time: str timestamp capturing the time this agreement was initiated
        :param block_number: int
        :param agreement_type: str type of agreement such as 'Access`, `Compute`, ...
        :param conditions: list of str represent names of conditions associated with this agreement
        :return:
        """
        logger.debug(f'Recording agreement info to `service_agreements` storage: '
                     f'agreementId={agreement_id}, did={did},'
                     f'service_index={service_index}, price={price}')
        self._run_query(
            'INSERT OR REPLACE INTO '
            'agreement(agreement_id, did, service_index, price, urls, consumer, '
            '          start_time, block_number, type) '
            'VALUES (?,?,?,?,?,?,?,?,?) ',
            (agreement_id, did, service_index,
             str(price), urls, consumer, start_time, block_number, agreement_type),
        )
        for cond in conditions:
            self._run_query(
                'INSERT OR REPLACE INTO '
                'agreement_condition(agreement_id, condition_name, status) '
                'VALUES(?,?,?) ',
                (agreement_id, cond, 1)
            )

    def update_condition_status(self, agreement_id, condition_name, status):
        """
        Update the service agreement status.

        :param agreement_id: hex str the id of the service agreement used as primary key
        :param condition_name: str name of agreement condition to update its status
        :param status: int status of condition (0 Uninitialized, 1 Unfulfilled, 2 Fulfilled, 3 Aborted)
        :return:
        """
        assert 1 <= status <= 3

        logger.debug(f'Updating agreement {agreement_id} status to {status}')
        self._run_query(
            f'UPDATE agreement_condition '
            f'SET status=? '
            f'WHERE agreement_id=? AND condition_name=?',
            (status, agreement_id, condition_name),
        )

    def get_agreements(self, since_block_number=0):
        """
        Get service agreements matching the given status.

        :param since_block_number: int
        :return:
        """
        agreements = collections.defaultdict(list)
        conditions = collections.defaultdict(dict)
        query = f'''
            SELECT a.agreement_id, did, service_index, price, urls, consumer, start_time, 
                block_number, type, ac.condition_name, ac.status 

            FROM agreement AS a, agreement_condition AS ac
            WHERE a.block_number>=?;
        '''

        for row in self._run_query(query, (since_block_number,)):
            agreements[row[0]] = row[1:8]
            conditions[row[0]][row[9]] = row[10]

        return agreements, conditions

    def get_completed_agreement_ids(self, since_block_number=0):
        query = '''
            SELECT a.agreement_id 
            FROM agreement AS a, agreement_condition AS ac 
            WHERE a.agreement_id = ac.agreement_id 
              AND block_number>=? 
              AND status>=2
        '''
        agreement_ids = {row[0] for row in self._run_query(query, (since_block_number,))}
        return agreement_ids

    def get_pending_agreements(self, since_block_number=0):
        """
        Get service agreements matching the given status.

        :param since_block_number: int
        :return:
        """
        agreements = collections.defaultdict(list)
        conditions = collections.defaultdict(dict)
        try:
            query = f'''
                SELECT a.agreement_id, did, service_index, price, urls, start_time, 
                    consumer, block_number, type, ac.condition_name, ac.status 

                FROM agreement AS a, agreement_condition AS ac
                WHERE a.agreement_id = ac.agreement_id 
                  AND a.block_number>=? 
                  AND ac.status<2;
            '''

            for row in self._run_query(query, (since_block_number,)):
                agreements[row[0]] = row[1:8]
                conditions[row[0]][row[9]] = row[10]
        except Exception as e:
            logger.debug(f'error processing pending agreements query: {e}')

        return agreements, conditions

    def get_agreement_ids(self, since_block_number=0):
        """Return all known agreement ids.

        :param since_block_number: int include all agreements with block number >= to this block number
        """
        try:
            query = '''
                SELECT agreement_id 
                FROM agreement 
                WHERE block_number>=? '''
            agreement_ids = {row[0] for row in self._run_query(query, (since_block_number,))}
            return agreement_ids
        except Exception as e:
            logger.warning(f'db error getting agreement ids: {e}')
            return set()

    def get_agreement_ids_with_condition_status(self):
        try:
            agr_id_to_conditions = collections.defaultdict(dict)
            query = '''
                SELECT agreement_id, condition_name, status 
                FROM agreement_condition
            '''

            for row in self._run_query(query, ()):
                agr_id_to_conditions[row[0]][row[8]] = row[9]

            return agr_id_to_conditions
        except Exception as e:
            logger.warning(f'db error getting agreement conditions status: {e}')
            return {}

    def get_latest_block_number(self):
        try:
            query = '''
                SELECT MAX(block_number) 
                FROM agreement
            '''
            result = self._run_query(query, ())
            return list(result)[0][0]
        except Exception as e:
            logger.debug(f'error finding latest block number from db: {e}')

    def get_agreement_count(self):
        try:
            result = self._run_query('SELECT COUNT(agreement_id) FROM agreement ')
            return list(result)[0][0]
        except Exception as e:
            logger.debug(f'error counting agreements: {e}')
            return 0
