#  Copyright 2018 Ocean Protocol Foundation
#  SPDX-License-Identifier: Apache-2.0

from ocean_events_handler.event_handlers import (
    accessSecretStore,
    escrowRewardCondition,
    lockRewardCondition
)

event_handlers_map = {
    'accessSecretStore': accessSecretStore,
    'escrowRewardCondition': escrowRewardCondition,
    'lockRewardCondition': lockRewardCondition
}