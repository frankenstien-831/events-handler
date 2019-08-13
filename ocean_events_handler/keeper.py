import logging

from ocean_keeper import Keeper as OcnKeeper, DIDRegistry
from ocean_keeper.agreements import AgreementStoreManager
from ocean_keeper.conditions import LockRewardCondition, EscrowRewardCondition, AccessSecretStoreCondition
from ocean_keeper.conditions.condition_manager import ConditionStoreManager
from ocean_keeper.templates import EscrowAccessSecretStoreTemplate


class Keeper(OcnKeeper):
    def __init__(self, artifacts_path):
        OcnKeeper.__init__(self, artifacts_path)

        self.did_registry = DIDRegistry.get_instance()
        self.escrow_access_secretstore_template = EscrowAccessSecretStoreTemplate.get_instance()
        self.agreement_manager = AgreementStoreManager.get_instance()
        self.condition_manager = ConditionStoreManager.get_instance()
        self.lock_reward_condition = LockRewardCondition.get_instance()
        self.escrow_reward_condition = EscrowRewardCondition.get_instance()
        self.access_secret_store_condition = AccessSecretStoreCondition.get_instance()
        contracts = [
            self.did_registry,
            self.escrow_access_secretstore_template,
            self.agreement_manager,
            self.condition_manager,
            self.lock_reward_condition,
            self.escrow_reward_condition,
            self.access_secret_store_condition,
        ]
        self._contract_name_to_instance = {contract.name: contract
                                           for contract in contracts if contract}

    @staticmethod
    def get_instance(artifacts_path=None, contract_names=None):
        return Keeper(artifacts_path)

    def get_condition_name_by_address(self, address):
        """Return the condition name for a given address."""
        if self.lock_reward_condition.address == address:
            return 'lockReward'
        elif self.access_secret_store_condition.address == address:
            return 'accessSecretStore'
        elif self.escrow_reward_condition.address == address:
            return 'escrowReward'
        else:
            logging.error(f'The current address {address} is not a condition address')
