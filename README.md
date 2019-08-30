[![banner](https://raw.githubusercontent.com/oceanprotocol/art/master/github/repo-banner%402x.png)](https://oceanprotocol.com)

# events-handler-py
Publisher events handler agent dealing with Keeper Contract events


## Features


## Prerequisites

Python 3.6

## Running Locally, for Dev and Test

First, clone this repository:

```bash
git clone git@github.com:oceanprotocol/events-handler-py.git
cd events-handler-py/
```

Start a keeper node and other services of the ocean network:

```bash
git clone git@github.com:oceanprotocol/barge.git
cd barge
bash start_ocean.sh --no-events-handler --no-pleuston --local-spree-node
```

Barge is the repository where all the Ocean Docker Compose files are located. 
We are running the script `start_ocean.sh`: the easy way to have Ocean projects 
up and running. We run without an events-handler instance because we will run it directly.

To learn more about Barge, visit [the Barge repository](https://github.com/oceanprotocol/barge).

Note that it runs an Aquarius instance and an Elasticsearch instance but Aquarius can 
also work with BigchainDB or MongoDB.

Export environment variables `PROVIDER_ADDRESS`, `PROVIDER_PASSWORD`
and `PROVIDER_KEYFILE`. Use the values from the `tox.ini` file, or use 
your own.

The most simple way to start is:

```bash
pip install -r requirements_dev.txt
export CONFIG_FILE=config.ini
./scripts/wait_for_migration_and_extract_keeper_artifacts.sh
./start_events_monitor.sh
```
 
#### Code style

The information about code style in python is documented in this two links [python-developer-guide](https://github.com/oceanprotocol/dev-ocean/blob/master/doc/development/python-developer-guide.md)
and [python-style-guide](https://github.com/oceanprotocol/dev-ocean/blob/master/doc/development/python-style-guide.md).

#### Testing

Automatic tests are setup via Travis, executing `tox`.
Our test use pytest framework.

## License

```
Copyright 2018 Ocean Protocol Foundation Ltd.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
