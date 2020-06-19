from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

key = b"01234567890123456789012345678901"
iv = b"0123456789012345"

c = AES.new(key, AES.MODE_CBC, iv)
c.encrypt(pad(b"A" * 128, 16))
binascii.hexlify(_)
