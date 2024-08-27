# bigeye miner

requirements:
- Python >=3.8
- **Ogmios 6.6.*, connected to a Cardano node**

tested with local Ogmios/node, demeter should also work

## setup

### install requirements

clone code
````
git clone https://github.com/nullhashpixel/bigeye.git
cd bigeye
````

Recommendation: install requirements in a virtual requirement.

````
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
````

### build miner cores

go to `miners/cpu` and run
````
make
````
or similarly for other miners.


### wallet

- create a new wallet and put the seed phrase in a file named `wallet.txt` in `config/mainnet/` (or similarly for other profiles)
- fund the wallet with a few (t)ADA (at least 10 (t)ADA are needed, a single UTxO is enough)
- for security reasons don't re-use existing wallets and only keep little amounts in the wallet used to mine

### configuration

- run the miner, upon first launch it will ask for missing config values (e.g. Ogmios URL)
- or change them manually in `config/mainnet/config.json`

## profiles

profiles are used to organize mining for different versions of $TUNA (possible future forks), mine with different settings or mine on one of the testnets.
The default profile is called `mainnet`.

The **config file** for this profile is located at `config/mainnet/config.json`.
If the `config.json` file does not exist, it will be created during the first start of the miner.


## important note

bigeye runs transaction building and hash computation in different processes to let users run them on different machines.
Communication between is via low-level TCP sockets and requires open ports on the machine running the hash computations.
The machine running the transaction building (holding private keys for the wallet etc.) does not need to be accessible from the outside and can also run behind a NAT (router, firewall).

In a simple setup, transaction building and hash computation can run on the same machine.
The `config.json` offers a simple way to start the miner cores (which perform hash computation) automatically with the
````
    "AUTO_SPAWN_MINERS": true,
````
setting.
````
    "MINER_EXECUTABLE": "miners/cpu/cpu-sha256",
    "MINERS": "127.0.0.1:2023-2034",
````
define which executable to spawn and the range `2023-2034` specifies 12 processes to be spawned, which each will listen on the ports in this range.

If the miner cores run on other machines, an example configuration could look like this:
````
    "AUTO_SPAWN_MINERS": false,
    "MINERS": "192.168.0.100:2023,192.168.0.100:2024,192.168.0.101:2023",
````

The `simple` miner core is a pure Python implementation, which should be much slower on most systems.


## mine
````
./mine.py mainnet
````

