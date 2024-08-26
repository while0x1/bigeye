#!/usr/bin/env python
import hashlib
import socket
import time
import random
import sys

def calc_diff(b):
    lz = 0
    dn = 0
    i = 0
    while i < len(b):
        if b[i] == 0:
            lz += 2
        elif b[i] < 16:
            lz += 1
            dn = b[i]<<12
            if i < len(b)-1:
                dn += b[i+1]<<4
            if i < len(b)-2:
                dn += b[i+1]>>4
            break
        else:
            dn = b[i]<<8
            if i < len(b)-1:
                dn += b[i+1]
            break
        i += 1
    return lz, dn

if len(sys.argv) == 3:
    HOST = sys.argv[1] 
    PORT = int(sys.argv[2])
elif len(sys.argv) == 2:
    HOST = '127.0.0.1'
    PORT = int(sys.argv[1])
else:
    HOST = '127.0.0.1'
    PORT = 45002 

while True:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((HOST, PORT))
            s.listen(1)
            conn, addr = s.accept()
            with conn:
                while True:
                    data = conn.recv(1024)
                    if not data: 
                        break
                    p = data.decode('utf-8').strip().split(' ')
                    ts = bytes.fromhex(p[0])
                    lz = int(p[1])
                    dn = int(p[2])

                    found = False
                    while True:
                        t0 = time.monotonic()
                        counter = 0
                        while time.monotonic() < t0 + 1:
                            nonce_e = random.getrandbits(128)

                            for i in range(100000):
                                counter += 1
                                nonce = bytes.fromhex(format(nonce_e + counter, 'x').zfill(32))
                                ts = ts[:4] + nonce + ts[20:]

                                dh = hashlib.sha256(hashlib.sha256(ts).digest()).digest()
                                this_lz, this_dn = calc_diff(dh)
                                if (this_lz > lz) or (this_lz == lz and this_dn < dn):
                                    found = True
                                    break
                            if found:
                                break

                        if found:
                            break

                        rate = counter / (time.monotonic() - t0 + 1e-9)
                        conn.sendall(f". {rate}\n".encode('utf-8'))
                    
                    res = f"{ts.hex()}:{dh.hex()}\n"
                    conn.sendall(res.encode('utf-8'))
                    #time.sleep(0.5)

        time.sleep(0.1)
    except Exception as e:
        #print(e)
        time.sleep(1.0)
