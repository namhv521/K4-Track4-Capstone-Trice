"""Create a private local test CA/server cert. Never installs trust or changes firewall."""
import argparse
from datetime import datetime,timedelta,timezone
import ipaddress
from pathlib import Path
from cryptography import x509
from cryptography.hazmat.primitives import hashes,serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
ROOT=Path(__file__).resolve().parents[1]

def create_local_tls(address,out_dir):
    ip=ipaddress.ip_address(address)
    nets=[ipaddress.ip_network(x) for x in ['10.0.0.0/8','172.16.0.0/12','192.168.0.0/16']]
    if not any(ip in n for n in nets):raise ValueError('Use an RFC1918 LAN IPv4 address, not a public/VPN endpoint')
    folder=Path(out_dir).resolve()
    if not folder.is_relative_to(ROOT):raise ValueError('TLS files must remain inside Trice')
    paths={k:folder/v for k,v in {'ca':'trice-local-ca.crt','ca_key':'ca-key.pem','cert':'server-cert.pem','key':'server-key.pem'}.items()}
    if any(p.exists() for p in paths.values()):raise FileExistsError('TLS files already exist; use a new directory to avoid replacing trusted certificates')
    folder.mkdir(parents=True,exist_ok=True)
    now=datetime.now(timezone.utc)
    ca_key=rsa.generate_private_key(public_exponent=65537,key_size=2048)
    ca_name=x509.Name([x509.NameAttribute(NameOID.COMMON_NAME,'Trice local demo CA')])
    ca=(x509.CertificateBuilder().subject_name(ca_name).issuer_name(ca_name).public_key(ca_key.public_key())
        .serial_number(x509.random_serial_number()).not_valid_before(now-timedelta(minutes=5)).not_valid_after(now+timedelta(days=365))
        .add_extension(x509.BasicConstraints(ca=True,path_length=0),critical=True)
        .add_extension(x509.KeyUsage(digital_signature=True,key_encipherment=False,content_commitment=False,data_encipherment=False,key_agreement=False,key_cert_sign=True,crl_sign=True,encipher_only=False,decipher_only=False),critical=True).sign(ca_key,hashes.SHA256()))
    key=rsa.generate_private_key(public_exponent=65537,key_size=2048)
    cert=(x509.CertificateBuilder().subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME,'Trice local camera')]))
        .issuer_name(ca_name).public_key(key.public_key()).serial_number(x509.random_serial_number())
        .not_valid_before(now-timedelta(minutes=5)).not_valid_after(now+timedelta(days=30))
        .add_extension(x509.BasicConstraints(ca=False,path_length=None),critical=True)
        .add_extension(x509.SubjectAlternativeName([x509.DNSName('localhost'),x509.IPAddress(ip),x509.IPAddress(ipaddress.ip_address('127.0.0.1'))]),critical=False)
        .add_extension(x509.ExtendedKeyUsage([x509.oid.ExtendedKeyUsageOID.SERVER_AUTH]),critical=False).sign(ca_key,hashes.SHA256()))
    paths['ca'].write_bytes(ca.public_bytes(serialization.Encoding.PEM));paths['cert'].write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    for name,k in [('ca_key',ca_key),('key',key)]:
        paths[name].write_bytes(k.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.NoEncryption()))
    return {k:str(v) for k,v in paths.items()}
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--ip',required=True);parser.add_argument('--out',default=str(ROOT/'data/tls'))
    args=parser.parse_args();paths=create_local_tls(args.ip,Path(args.out))
    print('Created local test certificate. You must choose to trust the CA on each test device; no trust/firewall changes were made.')
    print('Public CA certificate (only this file may be copied to phone): '+paths['ca'])
    print('Never share *key.pem files.')
