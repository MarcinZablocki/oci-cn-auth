#!/usr/bin/python3
from base64 import b64decode
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from OpenSSL import crypto
import json

class Cert(object):

    def __init__(self, cert):
        try:
            self.cert = x509.load_pem_x509_certificate(bytes(cert.encode('utf-8')), default_backend())
        except ValueError:
            print('Incorrect certificate')
            return None

    @property
    def not_valid_after(self):
        return self.cert.not_valid_after

    def get_san(self):
        """
          Return object of SAN information or None if missing
        """

        try:
            self.cert.extensions.get_extension_for_oid(x509.oid.ExtensionOID.SUBJECT_ALTERNATIVE_NAME)
            return True

        except x509.ExtensionNotFound:
            return False

class LoadBundle(object):

    def __init__(self, bundle, keypass):
        self.bundle = crypto.load_pkcs12(bundle, passphrase=keypass)
        self.cert = self.bundle.get_certificate()
        self.key = self.bundle.get_privatekey()
        self.ca = self.bundle.get_ca_certificates()

    @property
    def not_valid_after(self):
        c = x509.load_pem_x509_certificate(bytes(crypto.dump_certificate(crypto.FILETYPE_PEM, self.cert)), default_backend())
        return c.not_valid_after

    @property
    def serial(self):
        return self.cert.get_serial_number()

class NewBundle(object):

    def __init__(self, cert, key, keypass, ca):
        self.cert = crypto.load_certificate(crypto.FILETYPE_PEM, cert)
        self.cert_pem = cert
        self.keypass = keypass
        self.key = crypto.load_privatekey(crypto.FILETYPE_PEM, key, passphrase=keypass.encode('utf-8'))
        self.ca = crypto.load_certificate(crypto.FILETYPE_PEM, ca)

    def export_pkcs12(self):

        pkcs12 = crypto.PKCS12()
        pkcs12.set_certificate(self.cert)
        pkcs12.set_ca_certificates([self.ca])
        pkcs12.set_privatekey(self.key)

        return pkcs12.export(passphrase=self.keypass.encode('utf-8'))

