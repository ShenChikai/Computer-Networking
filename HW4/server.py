import os
import sys
import socket
import datetime
import hashlib
from cryptography.hazmat.primitives.asymmetric import dsa, rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from cryptography.hazmat.primitives import hashes
from cryptography import x509
from cryptography.hazmat.primitives import serialization
from cryptography.x509.oid import NameOID
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.asymmetric import utils
from cryptography.exceptions import InvalidSignature

# Generates RSA private and public key pair (skCA, pkCA)
private_key_server = rsa.generate_private_key(
	public_exponent=65537,
	key_size=2048,
	)
public_key_server = private_key_server.public_key()

# Generate PEM
private_key_server_pem = private_key_server.private_bytes(
	encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.TraditionalOpenSSL,
	encryption_algorithm=serialization.NoEncryption()
).decode("utf-8") 
public_key_server_pem = public_key_server.public_bytes(
    encoding=serialization.Encoding.PEM,
	format=serialization.PublicFormat.SubjectPublicKeyInfo
).decode("utf-8") 

Server_PORT = ''
CA_IP = ''
CA_PORT = ''
Message2Client = ''

# Take in arguments Server(p), CA(ss, pp), msg: m
if len(sys.argv) == 1:
	print("Please enter in format of 'Python3 server.py –p portno -ss caIP –pp portno -m msg'", flush=True)
	exit()
elif len(sys.argv) >= 9:
	try:
		Server_PORT = int(sys.argv[2])
		CA_IP = str(sys.argv[4])
		CA_PORT = int(sys.argv[6])
		MessageInput = sys.argv[8:]
	except ValueError:
		print("Enter in exact format 'Python3 server.py –p portno -ss caIP –pp portno -m msg'", flush=True)
else:
	print("Please eneter in exact format of 'Python3 server.py –p portno -ss caIP –pp portno -m msg'", flush=True)
	exit()

# Join the message input
for idx in range(0,len(MessageInput)):
	Message2Client = Message2Client + MessageInput[idx] + ' '

# Start Scoket with CA
sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
CAAddressPort = (CA_IP, CA_PORT)

serverName = "127.0.0.1" #input("Type in Host Name: ")

print("server started on 127.0.0.1 at port", Server_PORT, flush=True)
print("server public key: \n", public_key_server_pem, flush=True)
print("server private key: \n", private_key_server_pem, flush=True)

closed = False
try:
	# Request for Certificate    request format: "client xxx pk: xxxxxxxxx"
	print("sending certificate request to CA:", CA_IP, "port", CA_PORT, flush=True)
	requestMsg = "server " + serverName + " pk: " + str(public_key_server_pem)
	sock.sendto(requestMsg.encode(), CAAddressPort)
	requestRet = sock.recvfrom(10000)
	# Recv cert_client
	cert_client_pem = requestRet[0]
	cert_client = x509.load_pem_x509_certificate(cert_client_pem)
	public_key_client = cert_client.public_key()
	print("received client certificate:", cert_client.subject.rfc4514_string(), flush=True)
	#print("received server certificate:", ?, flush=True)

finally:
	if not closed:
		sock.close()


# Start Socket with Server
Server_IP = "127.0.0.1"
sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
serverAddressPort = (Server_IP, Server_PORT)
# Server needs to bind to a listening address
sock.bind(serverAddressPort)

closed = False
try:
	# Recv and Parse for secretKey_encrypted_pks + message_encrypted_ks + signature_encrypted_ks
	chunk = sock.recvfrom(10000)
	chunkMsg = chunk[0]
	clientAddr = chunk[1]
	secretKey_encrypted_pks = chunkMsg[(chunkMsg.index(b'secretKey_encrypted_pks') + 25):(chunkMsg.index(b'message_encrypted_ks') - 1)]
	message_encrypted_ks = chunkMsg[(chunkMsg.index(b'message_encrypted_ks') + 22):(chunkMsg.index(b'signature_encrypted_ks') - 1)]
	signature_encrypted_ks = chunkMsg[(chunkMsg.index(b'signature_encrypted_ks') + 24):]

	# Uses server private key skS to decrypt and recover KS
	secretKey = private_key_server.decrypt(
	    secretKey_encrypted_pks,
	    padding.OAEP(
	        mgf=padding.MGF1(algorithm=hashes.SHA256()),
	        algorithm=hashes.SHA256(),
	        label=None
	    )
	)
	# Uses KS to decrypt the message to recover σ and m
	iv = b'Uz\xbae\x176\xf8\xa2\xfc\xca\x95\x1a\x07\x06\xf9_'
	cipher = Cipher(algorithms.AES(secretKey), modes.CTR(iv))
	decryptor = cipher.decryptor()
	message = decryptor.update(message_encrypted_ks) + decryptor.finalize()
	# 2 identical ciphers are needed
	cipher2 = Cipher(algorithms.AES(secretKey), modes.CTR(iv))
	decryptor2 = cipher2.decryptor()
	signature = decryptor2.update(signature_encrypted_ks) + decryptor2.finalize()


	# Applies Client’s public key pkC to the signed message digest (Use PSS padding)
	# Computes hash of the message, and Compares the result of step 6 with the hash computed
	# Compare could be done using verify(). If the signature does not match, verify() will raise an InvalidSignature exception.
	try:
		# Calculate Hash of decrypted message
		chosen_hash = hashes.SHA256()
		hasher = hashes.Hash(chosen_hash)
		hasher.update(message)
		digest = hasher.finalize()
		# Verify using public key of client
		public_key_client.verify(
		    signature,
		    digest,
		    padding.PSS(
		        mgf=padding.MGF1(hashes.SHA256()),
		        salt_length=padding.PSS.MAX_LENGTH
		    ),
		    utils.Prehashed(chosen_hash)
		)
	except InvalidSignature:
		print("Exception InvalidSignature: signature does not match.", flush=True)
		exit()

	# decrypt signature with public key?

	# If passed above verification, print msg from client
	print("received message from client:", message.decode(), flush = True)
	# calculated = <content of calculated hash> received = <content of decrypted hash>
	print("integrity check: calculated =", digest, "received =", digest, flush = True)


	retMsg = Message2Client
	# Encrypts the message with KS and sends it to Client (Use cipher created above when decrypting)
	encryptor = cipher.encryptor()
	retMsg_encrypted_ks = encryptor.update(retMsg.encode("utf-8")) + encryptor.finalize()
	print("sending message to client:", Message2Client, flush=True)
	sock.sendto(retMsg_encrypted_ks, clientAddr)

finally:
	if not closed:
		#print("terminating server...", flush=True)
		sock.close()