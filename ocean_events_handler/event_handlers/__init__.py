#  Copyright 2018 Ocean Protocol Foundation
#  SPDX-License-Identifier: Apache-2.0

from ocean_events_handler.event_handlers import (
    accessSecretStore,
    escrowAccessSecretStoreTemplate,
    escrowRewardCondition,
    lockRewardCondition
)

event_handlers_map = {
    'accessSecretStore': accessSecretStore,
    'escrowAccessSecretStoreTemplate': escrowAccessSecretStoreTemplate,
    'escrowRewardCondition': escrowRewardCondition,
    'lockRewardCondition': lockRewardCondition
}