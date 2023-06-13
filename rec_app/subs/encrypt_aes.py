#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
by Dmitri Yousef Yengej

Description:
AES Encryption of files

Files can hold a RSA encrypted key_length, key and the filesize in the header
if the key is included,

ENCRYPTED FILE HEADER:
FILESIZE: 8Bytes
IV:     16Bytes
(optional only if key included in file)
KEY_LEN: 8 Bytes
KEY:    KEY_LEN Bytes
DATA:   x Bytes

"""
try:
    from subs.log import create_logger
except:
    def create_logger():
        class Logger():
            def __init__(self) -> None: 
                f = lambda *x: print("ENCRYPT AES: ", *x)  # change messenger in whatever script you are importing
                self.warning = self.info = self.critical = self.debug = self.error = f
        return Logger()

logger = create_logger()

def log(message, level="info"):
    getattr(logger, level)("ENCRYPT AES: {}".format(message))  # change RECORDER SAVER IN CLASS NAME


import os
import struct
import Crypto.Cipher.AES as AES

from cryptography import x509    
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes, serialization
from datetime import datetime

class Encryption():
    """
    encryption object
    holds public and private keys loaded from pem file

    start with load_all
    use check_certificates to verify certificates and
    expiration dates
    """
    password = None    # password for private key

    def __init__(self) -> None:
        self.algorithm = hashes.SHA512()
        self.mgf = padding.MGF1(algorithm=self.algorithm)
        self.padding = padding.OAEP(mgf=self.mgf, 
                                    algorithm=self.algorithm, 
                                    label=None)

    def load_all(self, pem_loc, root_cert_loc):
        self.load_public_key(pem_loc)
        self.load_private_key(pem_loc)
        self.load_root_cert(root_cert_loc)

    def load_cert(self, pem_loc):
        pem = self.open_file(pem_loc)
        self.cert = x509.load_pem_x509_certificate(pem, 
                                                   backend=default_backend())
    
    def load_public_key(self, pem_loc):
        pem = self.open_file(pem_loc)
        self.load_cert(pem_loc)
        self.public_key = self.cert.public_key()
    
    def load_private_key(self, pem_loc):
        pem = self.open_file(pem_loc)
        self.private_key = (serialization
                            .load_pem_private_key(pem,
                                                  password=self.password,  
                                                  backend=default_backend()
                                                  )
                            )

    def load_root_cert(self, cert_loc):
        cert = self.open_file(cert_loc)
        self.root_cert = x509.load_pem_x509_certificate(cert, 
                                          backend=default_backend())


    def verify(self):
        self.root_cert.public_key().verify(self.cert.signature,  
                                           self.cert.tbs_certificate_bytes,  
                                           padding.PKCS1v15(), 
                                           hashes.SHA256())
    
    def check_date(self) -> bool:
        return datetime.now() < self.cert.not_valid_after
    
    def encrypt(self, data) -> bytes:
        return self.public_key.encrypt(data, self.padding)
    
    def decrypt(self, data) -> bytes:
        return self.private_key.decrypt(data, self.padding)
    
    def encrypt_file(self, file, key):
        """
        automatically encrypts file with key included. The key
        will be encrypted with the certificates
        """
        enc_key = self.encrypt(key)
        encrypt_file(key, file, key_in_file=enc_key)
    
    def decrypt_file(self, file):
        """
        automatically decrypts file with included key. 
        The key will be decrypted with the certificates
        """
        decrypt_file(None, file, key_in_file=self.decrypt)

    def check_certificates(self):
        self.verify()
        log("Certificate Validated", "info")
        start = self.cert.not_valid_before.strftime("%D %T")
        end = self.cert.not_valid_after.strftime("%D %T")
        if not self.check_date():
            log(f"Certificate Expired on: {end}",
                "critical")
            raise SystemExit()
        
        else: 
            log(f"Certificate Valid from {start} to {end}", 
                "info")
        return True

    def open_file(self, file_loc):
        with open(file_loc, "rb") as file:
            return file.read()


def encrypt_file(key, in_filename, out_filename=None, 
                 chunksize=64*1024, key_in_file=None):
    """ Encrypts a file using AES (CBC mode) with the
        given key.
        key:
            The encryption key - a bytes object that must be
            either 16, 24 or 32 bytes long. Longer keys
            are more secure.
        in_filename:
            Name of the input file
        out_filename:
            If None, '<in_filename>.enc' will be used.
        chunksize:
            Sets the size of the chunk which the function
            uses to read and encrypt the file. Larger chunk
            sizes can be faster for some files and machines.
            chunksize must be divisible by 16.
        key_in_file:
            is the RSA encrypted key included in the file. if None, no key will be
            included in the file. 
    """
    if not out_filename:
        out_filename = in_filename + '.enc'

    iv = os.urandom(16)
    encryptor = AES.new(key, AES.MODE_CBC, iv)
    filesize = os.path.getsize(in_filename)

    with open(in_filename, 'rb') as infile:
        with open(out_filename, 'wb') as outfile:
            outfile.write(struct.pack('<Q', filesize))
            outfile.write(iv)

            if key_in_file is not None:
                len_key = len(key_in_file)
                outfile.write(struct.pack("<Q", len_key))
                print(f"save key in file, key length: {len_key}")
                outfile.write(key_in_file)

            while True:
                chunk = infile.read(chunksize)
                if len(chunk) == 0:
                    break
                elif len(chunk) % 16 != 0:
                    chunk += b' ' * (16 - len(chunk) % 16)

                outfile.write(encryptor.encrypt(chunk))
    return out_filename


def decrypt_file(key, in_filename, out_filename=None, 
                 chunksize=24*1024, key_in_file=False):
    """ Decrypts a file using AES (CBC mode) with the
        given key. Parameters are similar to encrypt_file,
        with one difference: out_filename, if not supplied
        will be in_filename without its last extension
        (i.e. if in_filename is 'aaa.zip.enc' then
        out_filename will be 'aaa.zip',
        key_in_file:
            or function to decrypt the key in the format lambda enc_key: decrypt(enc_key)
            if False or None, no key is included in the file)
    """
    if not out_filename:
        out_filename = os.path.splitext(in_filename)[0] + ".dec"

    with open(in_filename, 'rb') as infile:
        origsize = struct.unpack('<Q', infile.read(struct.calcsize('Q')))[0]
        iv = infile.read(16)
        if key_in_file not in {False, None}:
            key_len = struct.unpack('<Q', infile.read(struct.calcsize('Q')))[0]
            print(f"extracting {key_len} long key from file")
            key = infile.read(key_len)
            key = key_in_file(key)           # decrypt key

        # create decryptor
        decryptor = AES.new(key, AES.MODE_CBC, iv)

        with open(out_filename, 'wb') as outfile:
            while True:
                chunk = infile.read(chunksize)
                if len(chunk) == 0:
                    break
                outfile.write(decryptor.decrypt(chunk))

            outfile.truncate(origsize)
    return out_filename


if __name__ == "__main__":
    file = ""
    key = os.urandom(32)
    RSA_encrypt = Encryption()
    try:
        RSA_encrypt.load_public_key("./update_server_side.cer")
        encrypted_key = RSA_encrypt.encrypt(key)
        RSA_encrypt.encrypt_file(file, key)
    except Exception as e:
        print(e)
        
    try:
        RSA_encrypt.load_private_key("./update_client_side.key")
        RSA_encrypt.decrypt_file(file + ".enc")
    except Exception as e:
        print(e)

    # ofname = encrypt_file(key, infile, out_filename=infile+'.enc')
    # print('Encrypted to', ofname)
    # ofname = decrypt_file(key, infile, out_filename=infile+'.dec')
    # print('Decrypted to', ofname)
