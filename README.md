# bigeye miner

requirements: 
- Python >=3.8
- **Ogmios, connected to a Cardano node**

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

## mine
````
./mine.py mainnet
````

