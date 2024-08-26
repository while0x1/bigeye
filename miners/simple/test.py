#!/usr/bin/env python
import socket
HOST = '127.0.0.1'
PORT = 2023
socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
socket.connect((HOST, PORT))
socket.sendall("d8799f50337f78286ff62b8d884b0f67e4135609582003eec62fbd6253b2a67ea57d010015201c0d820bd1baf56da46ebf9a032c1ace1906625820000000001ec401cfa35f2efe5b2a1f0f56d4883803b332935f080bc68099864a0819acc41a00bbd5f0ff 4 65535\n".encode('utf-8'))
data = socket.recv(1024).decode('utf-8').strip()
socket.sendall("d8799f50337f78286ff62b8d884b0f67e4135609582003eec62fbd6253b2a67ea57d010015201c0d820bd1baf56da46ebf9a032c1ace1906625820000000001ec401cfa35f2efe5b2a1f0f56d4883803b332935f080bc68099864a0819acc41a00bbd5f0ff 4 65535\n".encode('utf-8'))
print(data)
