[![banner](https://raw.githubusercontent.com/oceanprotocol/art/master/github/repo-banner%402x.png)](https://oceanprotocol.com)

# events-handler
Provider's events handler agent dealing with Keeper Contract events


## Features
Monitors ServiceExecutionAgreement events and act as a provider agent to 
grant access and release reward for the publisher/provider. This is a critical 
part in the process of consuming data sets in the Ocean Protocol network. 
Every provider in the network must run some sort of an events-handler to 
be able to fulfill the access condition of an `Access` service in an `SEA` .

This release only supports the `Access` service type that is defined in an 
Ocean `DDO`. More service types will be supported in the events-handler when 
they're added to the Ocean services.

## Prerequisites

Python 3.6

## Running Locally

First, clone this repository:

```bash
git clone git@github.com:oceanprotocol/events-handler.git
cd events-handler/
```

Start a keeper node and other services of the ocean network:

```bash
git clone git@github.com:oceanprotocol/barge.git
cd barge
bash start_ocean.sh --no-events-handler --no-commons --local-spree-node
```

Barge is the repository where all the Ocean Docker Compose files are located. 
We are running the script `start_ocean.sh`: the easy way to have Ocean projects 
up and running. We run without an events-handler instance because we will run it directly.

To learn more about Barge, visit [the Barge repository](https://github.com/oceanprotocol/barge).

Note that it runs an Aquarius instance and an Elasticsearch instance but Aquarius can 
also work with BigchainDB or MongoDB.

Export environment variables `PROVIDER_ADDRESS`, `PROVIDER_PASSWORD`
and `PROVIDER_KEYFILE` (or `PROVIDER_ENCRYPTED_KEY`). Use the values from the `tox.ini` file, or use 
your own.
Instead of using keyfile and password, you can use the private key directly 
by setting the env var `PROVIDER_KEY`.

The most simple way to start is:

```bash
pip install -r requirements_dev.txt
export CONFIG_FILE=config.ini
./scripts/wait_for_migration_and_extract_keeper_artifacts.sh
./start_events_monitor.sh
```

Once the events-handler is running, you can use the Ocean API (Squid library available in python, node, 
and java implementation) to publish an asset and start a consume request. For more details on using the  
Ocean ecosystem please refer to [Ocean API](https://github.com/oceanprotocol/squid-py/#usage) 

To run the events-handler as a provider, you can either run it from source as described above or 
use a docker image `docker pull oceanprotocol/events-handler:latest`. To run the docker image 
please refer to the docker-compose file in barge [events_handler.yml](https://github.com/oceanprotocol/barge/tree/master/compose-files/events_handler.yml)

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
