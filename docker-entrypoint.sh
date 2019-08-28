#!/bin/sh

export CONFIG_FILE=/ocean_events_handler/config.ini
envsubst < /ocean_events_handler/config.ini.template > /ocean_events_handler/config.ini
if [ "${LOCAL_CONTRACTS}" = "true" ]; then
  echo "Waiting for contracts to be generated..."
  while [ ! -f "/usr/local/keeper-contracts/ready" ]; do
    sleep 2
  done
fi

/bin/cp -up /usr/local/keeper-contracts/* /usr/local/artifacts/ 2>/dev/null || true

/ocean_events_handler/start_events_monitor.sh

tail -f /dev/null
