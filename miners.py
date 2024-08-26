import sys
import os
import datetime
import time
import socket
from threading import Thread, Event, Condition

class Miner:
    def __init__(self, miner_type=0, config=None, profile=None):
        self.type=miner_type
        self.profile = profile
        self.log = self.profile.log
        self.config = config
        self.initialized = False

        self.events = {
                'found': Event(),
                'error': Event(),
                'start': Event(),
                }

        self.target_hex = ''
        self.lz         = 2
        self.dn         = 12345 
        self.rate       = 0
        self.found_nonce_hex = ''

        self.name = self.config.get('name', 'M@') + self.config.get('HOST') + ':' + str(self.config.get('PORT'))

        self.thread = Thread(target=self.loop, args=())
        self.thread.start()

    def get_name(self):
        return self.name

    def get_stats(self):
        return {'rate': self.rate}

    def set_difficulty(self, lz, dn):
        self.lz = lz
        self.dn = dn

    def set_target(self, target_hex):
        self.target_hex = target_hex

    def loop(self):
        HOST = self.config.get('HOST')
        PORT = self.config.get('PORT')

        while True:
            try:
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.connect((HOST, PORT))

                while True:

                    self.events['start'].wait()
                    self.events['start'].clear()

                    found = False
                    while not found:
                        try:
                            self.socket.sendall(f"{self.target_hex} {self.lz} {self.dn}\n".encode('utf-8'))
                            data = self.socket.recv(1024).decode('utf-8').strip()
                            if data.startswith('.'):
                                self.rate = float(data.split(' ')[1])
                            else:
                                self.found_nonce_hex = data[8:8+16*2]
                                self.events['found'].set()
                                with self.cond:
                                    self.cond.notify()
                                found = True
                        except Exception as e:
                            self.log(f"<x1b[31merror: invalid response from mining core: {data}<x1b[0m {e}")
                            self.socket.close()
                            time.sleep(2)
                            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                            time.sleep(2)
                            self.socket.connect((HOST, PORT))
                            self.rate = 0
            except Exception as e:
                #self.log(f"<x1b[93mcould not connect to miner {self.get_name()}<x1b[0m")
                self.rate = 0
                time.sleep(10)

class MinerManager:
    def __init__(self, profile):
        self.profile = profile
        self.miners = []
        self.cond = Condition()

    def add(self, config):
        new_miner = Miner(config=config, profile=self.profile)
        new_miner.cond = self.cond
        self.miners.append(new_miner)

    def set_difficulty(self, lz, dn):
        for m in self.miners:
            m.set_difficulty(lz, dn)

    def set_target(self, target_hex):
        for m in self.miners:
            m.set_target(target_hex)

    def wait(self, timeout=15):
        result = None

        for m in self.miners:
            m.events['start'].set()

        with self.cond:
            self.cond.wait(timeout)

        for m in self.miners:
            if m.events['found'].is_set():
                result = m.found_nonce_hex
                break
        for m in self.miners:
            m.events['found'].clear()

        return result

    def get_stats(self):
        return {m.get_name(): m.get_stats() for m in self.miners}

    def __len__(self):
        return len(self.miners)

def format_hashrate(h):
    if h < 10000:
        return f"{h:.0f} H/s"
    elif h < 100000:
        return f"{(h/1000):.1f} kH/s"
    elif h < 1e6:
        return f"{(h/1000):.0f} kH/s"
    elif h < 1e7:
        return f"{(h/1e6):.2f} MH/s"
    elif h < 1e8:
        return f"{(h/1e6):.1f} MH/s"
    elif h < 1e9:
        return f"{(h/1e6):.0f} MH/s"
    elif h < 1e10:
        return f"{(h/1e9):.2f} GH/s"
    elif h < 1e11:
        return f"{(h/1e9):.1f} GH/s"
    else:
        return f"{(h/1e9):.0f} GH/s"
