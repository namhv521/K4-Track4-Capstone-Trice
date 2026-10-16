import importlib.util
from pathlib import Path
import tempfile
import unittest

class TLSTests(unittest.TestCase):
    def test_cert_ip_san_and_no_overwrite(self):
        from tools.create_local_tls import create_local_tls
        from cryptography import x509
        import ipaddress
        with tempfile.TemporaryDirectory(dir='runs') as folder:
            paths=create_local_tls('192.168.1.20',Path(folder))
            cert=x509.load_pem_x509_certificate(Path(paths['cert']).read_bytes())
            san=cert.extensions.get_extension_for_class(x509.SubjectAlternativeName).value
            self.assertIn(ipaddress.ip_address('192.168.1.20'),san.get_values_for_type(x509.IPAddress))
            with self.assertRaises(FileExistsError):create_local_tls('192.168.1.20',Path(folder))
    def test_outside_and_nonprivate_rejected(self):
        from tools.create_local_tls import create_local_tls
        with tempfile.TemporaryDirectory(dir='runs') as folder:
            with self.assertRaises(ValueError):create_local_tls('8.8.8.8',Path(folder))
        with self.assertRaises(ValueError):create_local_tls('192.168.1.20',Path('../outside-tls'))
