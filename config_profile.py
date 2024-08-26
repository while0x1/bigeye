import json
import datetime
import os
import cbor2
import time
import copy
import sys, traceback
import pycardano
import re

def prepare_config_file(config_filename):
    if not os.path.isfile(config_filename):
        default_filename = config_filename.rsplit(".", 1)[0] + ".default"
        if os.path.isfile(default_filename):
            with open(default_filename, 'r') as f:
                default_content = f.read()
            print("press [enter] for default value")
            print("-"*80)
            print("\x1b[91mconfig file is incomplete\x1b[0m: ", config_filename)
            print("-"*80)
            blanks = re.findall(r"{(.+?)}", default_content)
            for blank in blanks:
                blank_parts = blank.split('|')
                if len(blank_parts) == 1:
                    print(f"enter value for \x1b[92m{blank}\x1b[0m >")
                    blank_value = input()
                    default_content = default_content.replace("{" + blank + "}", blank_value)
                else:
                    print(f"enter value for \x1b[92m{blank_parts[0]}\x1b[0m (default: {blank_parts[1]})>")
                    blank_value = input()
                    default_content = default_content.replace("{" + blank + "}", blank_parts[1] if len(blank_value.strip()) < 1 else blank_value)
            with open(config_filename, 'w') as f:
                f.write(default_content)
            print("-"*80)
            print("done.")
            print("-"*80)
            return True
    else:
        raise Exception("config file already exists, delete config file first to run prepare step again.")


class Profile:
    def __init__(self, profile_name):
        self.log_prefix = ''
        self.name = profile_name
        self.load_config()

        self.TUNA_STATE_PREFIX_HEX    = self.config.get('TUNA_STATE_PREFIX', 'TUNA').encode('utf-8').hex()
        self.TUNA_COUNTER_PREFIX_HEX  = self.config.get('TUNA_COUNTER_PREFIX','COUNTER').encode('utf-8').hex()
        self.TUNA_POLICY_HEX          = self.config['POLICY']
        self.TUNA_STATE_ASSETNAME_HEX = self.TUNA_STATE_PREFIX_HEX + self.config.get('SPEND_SCRIPT')
        self.TUNA_ASSETNAME_HEX       = self.config.get('TUNA_ASSETNAME').encode('utf-8').hex() 
        self.CONTRACT_ADDRESS         = self.config.get('CONTRACT_ADDRESS')

    def log(self, s):
        full_s = f"{datetime.datetime.now().isoformat()} [{self.log_prefix}] {s}"
        full_s = full_s.replace("<x1b","\x1b") + "\x1b[0m"
        print(full_s)

    def load_config(self):
        config_filename = f'./config/{self.name}/config.json'
        if not os.path.isfile(config_filename):
            prepared_config = prepare_config_file(config_filename)
            if prepared_config is None:
                raise Exception(f"FileNotFound: {config_filename}")
        with open(config_filename, 'r') as cf:
            self.config = json.load(cf)
        self.profile_dir = f'./config/{self.name}/'
        self.log_prefix = self.config.get('PREFIX', 'general')
        self.log(f"using profile: <x1b[32m{self.name}<x1b[0m")

        wallet_filename = f'./config/{self.name}/wallet.txt'
        if not os.path.isfile(wallet_filename):
            raise Exception(f"wallet seed phrase text file not found: {wallet_filename}")

        with open(wallet_filename, 'r') as wf:
            seed = wf.read().strip()

        self.PAYMENT_DERIV = self.config.get('PAYMENT_DERIV', "m/1852'/1815'/0'/0/0")
        self.STAKING_DERIV = self.config.get('STAKING_DERIV', "m/1852'/1815'/0'/2/0")

        w = pycardano.crypto.bip32.HDWallet.from_mnemonic(seed)
        cw = w.derive_from_path(self.PAYMENT_DERIV)
        cws = w.derive_from_path(self.STAKING_DERIV)

        network_name = self.config.get('NETWORK', 'mainnet').lower()
        self.wallet_is_enterprise_address = self.config.get('ENTERPRISE_ADDRESS', False)
        staking_part = None if self.wallet_is_enterprise_address else pycardano.key.VerificationKey(cws.public_key).hash()
        network      = pycardano.Network.MAINNET if (network_name == 'mainnet') else pycardano.Network.TESTNET

        wallet_address = pycardano.address.Address(
                pycardano.key.VerificationKey(cw.public_key).hash(),
                staking_part=staking_part,
                network=network)

        self.wallet_vkey = pycardano.key.VerificationKey(cw.public_key)
        self.wallet_skey = pycardano.key.ExtendedSigningKey(cw.xprivate_key)
        self.wallet_pkh = pycardano.key.VerificationKey(cw.public_key).hash()
        self.wallet = str(wallet_address).strip()
        self.wallet_utxos = []

        self.contract_utxos = []

