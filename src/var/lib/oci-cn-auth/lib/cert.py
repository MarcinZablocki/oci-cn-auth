""" Certificate operations helpers """
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from OpenSSL import crypto

class Cert():
    """ X509 Certificate """

    def __init__(self, cert):
        try:
            self.cert = x509.load_pem_x509_certificate(
                bytes(cert.encode('utf-8')), default_backend()
                )
        except ValueError:
            print('Incorrect certificate')
            return None

    @property
    def not_valid_after(self):
        """ Returns not_valid_after field from certificate """
        return self.cert.not_valid_after

    def get_san(self):
        """
          Return object of SAN information or None if missing
        """

        try:
            self.cert.extensions.get_extension_for_oid(
                x509.oid.ExtensionOID.SUBJECT_ALTERNATIVE_NAME
                )
            return True

        except x509.ExtensionNotFound:
            return False

class CertBundle():
    """ PKCS12 bundle """
    #def __init__(self, bundle, keypass):
        #self.bundle = crypto.load_pkcs12(bundle, passphrase=keypass)
        #self.cert = self.bundle.get_certificate()
        #self.key = self.bundle.get_privatekey()
        #self.ca = self.bundle.get_ca_certificates()
    def __init__(self) -> None:
        super().__init__()
        self.bundle = None
        self.cert = None
        self.key = None
        self.cacert = None
        self.keypass = None

    def load_from_file(self, bundle, keypass):
        """ Load PKCS12 bundle from file """
        self.bundle = crypto.load_pkcs12(bundle, passphrase=keypass)
        self.cert = self.bundle.get_certificate()
        self.key = self.bundle.get_privatekey()
        self.cacert = self.bundle.get_ca_certificates()
        self.keypass = keypass
        return self

    def create(self, cert, key, keypass, cacert):
        """ Create new PKCS12 bundle from certificate chain and key """
        self.cert = crypto.load_certificate(crypto.FILETYPE_PEM, cert)
        self.keypass = keypass
        self.key = crypto.load_privatekey(
            crypto.FILETYPE_PEM,
            key,
            passphrase=keypass.encode('utf-8')
        )
        self.cacert = crypto.load_certificate(crypto.FILETYPE_PEM, cacert)
        self.bundle = self.export_pkcs12()
        return self

    @property
    def not_valid_after(self):
        """ returns date after which certificate will be invalidated """

        certificate_information = x509.load_pem_x509_certificate(
            bytes(
                crypto.dump_certificate(
                    crypto.FILETYPE_PEM, self.cert)
                    ),
                default_backend()
            )
        return certificate_information.not_valid_after

    @property
    def serial(self):
        """ returns certificate serial number """
        return self.cert.get_serial_number()

    def export_pkcs12(self):
        """" returns PKCS12 bundle """
        pkcs12 = crypto.PKCS12()
        pkcs12.set_certificate(self.cert)
        pkcs12.set_ca_certificates([self.cacert])
        pkcs12.set_privatekey(self.key)
        return pkcs12.export(passphrase=self.keypass.encode('utf-8'))
