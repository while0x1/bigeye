#!/usr/bin/env python3
import hashlib
import sys
print(hashlib.sha256(hashlib.sha256(bytes.fromhex(sys.argv[1])).digest()).hexdigest())
