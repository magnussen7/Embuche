#!/usr/bin/python3
from Hellf import ELF
from hashlib import sha256
from binascii import hexlify
from sys import argv
from struct import unpack, pack

from Crypto.Cipher import AES

e = ELF(argv[1])
surprise = e.get_section_by_name(".fini.")
text = e.get_section_by_name(".text")

timestamp = surprise.data[:8]
timestamp_readable = unpack("<Q", timestamp)[0]

timestamp = timestamp[:4] * 2

text_hash = sha256(text.data).digest()
text_hash_test = sha256(text.data).hexdigest()

key = b"".join([pack("<B", text_hash[i] ^ timestamp[i % 8]) for i in range(len(text_hash))])

# print(hexlify(key))

iv = b"0123456789012345"

c = AES.new(key, AES.MODE_CBC, iv)

print(c.decrypt(surprise.data[16:]))
