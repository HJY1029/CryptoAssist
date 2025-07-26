from Crypto.Cipher import AES
from base64 import b64encode

key = b'1234567890abcdef'
data = b'hello world12345'
cipher = AES.new(key, AES.MODE_ECB)
encrypted = cipher.encrypt(data)
print("密文:", b64encode(encrypted).decode())
