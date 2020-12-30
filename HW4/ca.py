import sys
import socket
import datetime
from cryptography.hazmat.primitives.asymmetric import dsa, rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from cryptography.hazmat.primitives import hashes
from cryptography import x509
from cryptography.hazmat.primitives import serialization
from cryptography.x509.oid import NameOID
import pem

# Generates RSA private and public key pair (skCA, pkCA)
private_key_ca = rsa.generate_private_key(
	public_exponent=65537,
	key_size=2048,
	)
public_key_ca = private_key_ca.public_key()

# Generate PEM
private_key_ca_pem = private_key_ca.private_bytes(
	encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.TraditionalOpenSSL,
	encryption_algorithm=serialization.NoEncryption()
).decode("utf-8") 
public_key_ca_pem = public_key_ca.public_bytes(
    encoding=serialization.Encoding.PEM,
	format=serialization.PublicFormat.SubjectPublicKeyInfo
).decode("utf-8") 

# Creates a self-signed certificate that is valid for 1 month
certificate_authority = issuer = x509.Name([
    x509.NameAttribute(NameOID.COUNTRY_NAME, u"US"),
    x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, u"California"),
    x509.NameAttribute(NameOID.LOCALITY_NAME, u"Los Angeles"),
    x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"USC"),
    x509.NameAttribute(NameOID.COMMON_NAME, u"Trusted CA"),
])

cert_ca = x509.CertificateBuilder().subject_name(
    certificate_authority
).issuer_name(
    issuer
).public_key(
	# sign certificate for this public key
    public_key_ca
).serial_number(
    x509.random_serial_number()
).not_valid_before(
    datetime.datetime.utcnow()
).not_valid_after(
    # Our certificate will be valid for 30 days
    datetime.datetime.utcnow() + datetime.timedelta(days=30)
).add_extension(
    x509.SubjectAlternativeName([x509.DNSName(u"localhost")]),
    critical=False,
# Sign CA's certificate with our private key
).sign(private_key_ca, hashes.SHA256())

# Take in arguments
if len(sys.argv) == 1:
	print("Please enter in format of 'Python3 ca.py -p portno'", flush=True)
	exit()
elif len(sys.argv) == 3:
	try:
		UDP_PORT = int(sys.argv[2])	# Global Var
	except ValueError:
		print("Port number must be an Integer.", flush=True)
else:
	print("Please eneter in exact format of 'Python3 ca.py -p portno'", flush=True)
	exit()

# Start Socket
UDP_IP = "127.0.0.1"
sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
closed = False
# UDP CA does not build an actual connections with its client, it only binds to a specific (ip, port)
try:
	sock.bind((UDP_IP, UDP_PORT))
except OSError:
	print("The port is unavailable. Please try another port number.", flush=True)
	exit()

print("ca started on 127.0.0.1 at port", UDP_PORT, "\n", flush=True)
print("ca public key:\n", public_key_ca_pem, flush=True)
print("ca private key:\n", private_key_ca_pem, flush=True)
print("ca certificate:", cert_ca.subject.rfc4514_string(), "\n", flush=True)
#print("ca certificate: US, California, Los Angeles, USC, Trusted CA", flush=True)
#public_key_ca = cert_ca.public_key()
#print((public_key_ca.public_numbers().e, public_key_ca.public_numbers().n))

# Global Var
clientFlag = False
serverFlag = False

clientPubKey = ''
serverPubKey = ''
cert_client = ''
cert_server = ''
clientAddr = ''
serverAddr = ''

# Listen for requests
try:
	while True:
		# Register:
		# Recv and Parse
		recv = sock.recvfrom(1024)
		recvMsg = recv[0].decode()
		recvAddr = recv[1]
		#--------------------------------------------------------------------CLIENT------------------------------------------------------------------
		# Check: [client request, sendto]   request format: "client xxx pk: xxxxxxxxx"
		if recvMsg.find('client') == 0 :
			# Request from client:
			clientName = recvMsg[(recvMsg.index('client') + 7):(recvMsg.index('pk:') - 1)]
			clientPubKeyPEM = recvMsg[(recvMsg.index('pk:') + 4):]
			clientAddr = recvAddr
			clientIP = recvAddr[0]
			clientPort = recvAddr[1]
			# Print Request
			print("received certificate request from Client host", clientName, "port", clientPort, flush=True)
			#######################
			# Generate cert_cient #
			#######################
			# Parse key
			clientPubKey = serialization.load_pem_public_key(clientPubKeyPEM.encode("utf-8"))
			# Attach attributes to object
			certificate_client = issuer = x509.Name([
			    x509.NameAttribute(NameOID.COUNTRY_NAME, u"US"),
			    x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, u"California"),
			    x509.NameAttribute(NameOID.LOCALITY_NAME, u"Los Angeles"),
			    x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"USC"),
			    x509.NameAttribute(NameOID.COMMON_NAME, u"Client"),
			])
			# Generate cert
			cert_client = x509.CertificateBuilder().subject_name(
			    certificate_client
			).issuer_name(
			    issuer
			).public_key(
				# sign certificate for this public key
			    clientPubKey
			).serial_number(
			    x509.random_serial_number()
			).not_valid_before(
			    datetime.datetime.utcnow()
			).not_valid_after(
			    # Our certificate will be valid for 5 days
			    datetime.datetime.utcnow() + datetime.timedelta(days=5)
			).add_extension(
			    x509.SubjectAlternativeName([x509.DNSName(u"localhost")]),
			    critical=False,
			# Sign CA's certificate with our private key
			).sign(private_key_ca, hashes.SHA256())
			# Mark client flag as received
			clientFlag = True
		#--------------------------------------------------------------------SERVER------------------------------------------------------------------
		# Check: [server request, sendto]   request format: "server xxx pk: xxxxxxxxx"
		if recvMsg.find('server') == 0 :
			# Request from server:
			serverName = recvMsg[(recvMsg.index('server') + 7):(recvMsg.index('pk:') - 1)]
			serverPubKeyPEM = recvMsg[(recvMsg.index('pk:') + 4):]
			serverAddr = recvAddr
			serverIP = recvAddr[0]
			serverPort = recvAddr[1]
			# Print Request
			print("received certificate request from Server host", serverName, "port", serverPort, flush=True)
			#######################
			# Generate cert_cient #
			#######################	
			# Parse key
			serverPubKey = serialization.load_pem_public_key(serverPubKeyPEM.encode("utf-8"))
			# Attach attributes to object
			certificate_server = issuer = x509.Name([
			    x509.NameAttribute(NameOID.COUNTRY_NAME, u"US"),
			    x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, u"California"),
			    x509.NameAttribute(NameOID.LOCALITY_NAME, u"Los Angeles"),
			    x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"USC"),
			    x509.NameAttribute(NameOID.COMMON_NAME, u"Server"),
			])
			# Generate cert
			cert_server = x509.CertificateBuilder().subject_name(
			    certificate_server
			).issuer_name(
			    issuer
			).public_key(
				# sign certificate for this public key
			    serverPubKey
			).serial_number(
			    x509.random_serial_number()
			).not_valid_before(
			    datetime.datetime.utcnow()
			).not_valid_after(
			    # Our certificate will be valid for 5 days
			    datetime.datetime.utcnow() + datetime.timedelta(days=5)
			).add_extension(
			    x509.SubjectAlternativeName([x509.DNSName(u"localhost")]),
			    critical=False,
			# Sign CA's certificate with our private key
			).sign(private_key_ca, hashes.SHA256())
			# Mark server flag as received
			serverFlag = True
		#------------------------------------------------------------------BOTH_RECEIVED--------------------------------------------------------------
		# CrossSend the cert as replies | just send the cert since pk could be generate from cert in reverse: cert.public_key()
		if (clientFlag and serverFlag) :
			print("sending certificate to Client", flush=True)
			print("sending certificate to Server", flush=True)
			# Export cert
			cert_client_PEM = cert_client.public_bytes(serialization.Encoding.PEM)
			cert_server_PEM = cert_server.public_bytes(serialization.Encoding.PEM)
			sock.sendto(cert_server_PEM, clientAddr)
			sock.sendto(cert_client_PEM, serverAddr)


except KeyboardInterrupt:
	# ctrl + c
	closed = True
	print("terminating ca...", flush=True)
	sock.close()

finally:
	if not closed:
		print("terminating ca...", flush=True)
		sock.close()