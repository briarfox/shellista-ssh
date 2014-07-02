######################
#Monkeypatch for Paramiko
######################
import paramiko
import base64
from binascii import hexlify, unhexlify
import os
from hashlib import md5
from Crypto.Cipher import DES3, AES
from paramiko import util
from paramiko.common import o600, zero_byte
from paramiko.py3compat import u, encodebytes, decodebytes, b
from paramiko.ssh_exception import SSHException, PasswordRequiredException

#monkeypatch paramiko.util.generate_key_bytes

def generate_key_bytes(hash_alg, salt, key, nbytes):
    keydata = bytes()
    digest = bytes()
    if len(salt) > 8:
        salt = salt[:8]
    while nbytes > 0:
        hash_obj = hash_alg()
        if len(digest) > 0:
            hash_obj.update(digest)
        hash_obj.update(b(key))
        hash_obj.update(salt)
        digest = hash_obj.digest()
        size = min(nbytes, len(digest))
        keydata += digest[:size]
        nbytes -= size
    return keydata
    

def _write_private_key(self, tag, f, data, password=None):
    f.write('-----BEGIN %s PRIVATE KEY-----\n' % tag)
    if password is not None:
        # since we only support one cipher here, use it
        cipher_name = list(self._CIPHER_TABLE.keys())[1]
        #cipher_name = 'AES-128-CBC'
        cipher = self._CIPHER_TABLE[cipher_name]['cipher']
        keysize = self._CIPHER_TABLE[cipher_name]['keysize']
        blocksize = self._CIPHER_TABLE[cipher_name]['blocksize']
        mode = self._CIPHER_TABLE[cipher_name]['mode']
        salt = os.urandom(16)
        key = generate_key_bytes(md5, salt, password, keysize)
        if len(data) % blocksize != 0:
            n = blocksize - len(data) % blocksize
            #data += os.urandom(n)
            # that would make more sense ^, but it confuses openssh.
            data += zero_byte * n
        data = cipher.new(key, mode, salt).encrypt(data)
        f.write('Proc-Type: 4,ENCRYPTED\n')
        f.write('DEK-Info: %s,%s\n' % (cipher_name, u(hexlify(salt)).upper()))
        f.write('\n')
    s = u(encodebytes(data))
    # re-wrap to 64-char lines
    s = ''.join(s.split('\n'))
    s = '\n'.join([s[i: i + 64] for i in range(0, len(s), 64)])
    f.write(s)
    f.write('\n')
    f.write('-----END %s PRIVATE KEY-----\n' % tag)
        
paramiko.PKey._write_private_key = _write_private_key



######################################
