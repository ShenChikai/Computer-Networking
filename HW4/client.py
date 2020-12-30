import os
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
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.asymmetric import utils

# Generates RSA private and public key pair (skCA, pkCA)
private_key_client = rsa.generate_private_key(
	public_exponent=65537,
	key_size=2048,
	)
public_key_client = private_key_client.public_key()

# Generate PEM
private_key_client_pem = private_key_client.private_bytes(
	encoding=serialization.Encoding.PEM,
	format=serialization.PrivateFormat.TraditionalOpenSSL,
	encryption_algorithm=serialization.NoEncryption()
).decode("utf-8") 
public_key_client_pem = public_key_client.public_bytes(
	encoding=serialization.Encoding.PEM,
	format=serialization.PublicFormat.SubjectPublicKeyInfo
).decode("utf-8") 	

Server_IP = ''
Server_PORT = ''
CA_IP = ''
CA_PORT = ''
Message2Server = ''

# Take in arguments Server(s, p), CA(ss, pp), msg: m
if len(sys.argv) == 1:
	print("Please enter in format of 'Python3 client.py –s serverIP –p portno -ss caIP –pp portno -m msg'", flush=True)
	exit()
elif len(sys.argv) >= 11:
	try:
		Server_IP = str(sys.argv[2])
		Server_PORT = int(sys.argv[4])
		CA_IP = str(sys.argv[6])
		CA_PORT = int(sys.argv[8])
		MessageInput = sys.argv[10:]
	except ValueError:
		print("Enter in exact format 'Python3 client.py –s serverIP –p portno -ss caIP –pp portno -m msg'", flush=True)
else:
	print("Please eneter in exact format of 'Python3 client.py –s serverIP –p portno -ss caIP –pp portno -m msg'", flush=True)
	exit()

# Join the message input
for idx in range(0,len(MessageInput)):
	Message2Server = Message2Server + MessageInput[idx] + ' '

# Start Scoket with CA
sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
CAAddressPort = (CA_IP, CA_PORT)

clientName = "127.0.0.1" #input("Type in Host Name: ")

print("client started on 127.0.0.1 at port 50505", flush=True)
print("client public key: \n", public_key_client_pem, flush=True)
print("client private key: \n", private_key_client_pem, flush=True)

closed = False
try:
	# Request for Certificate    request format: "client xxx pk: xxxxxxxxx"
	print("sending certificate request to CA:", CA_IP, "port", CA_PORT, flush=True)
	requestMsg = "client " + clientName + " pk: " + public_key_client_pem
	sock.sendto(requestMsg.encode(), CAAddressPort)
	# Recv cert_server
	requestRet = sock.recvfrom(10000)
	cert_server_pem = requestRet[0]
	cert_server = x509.load_pem_x509_certificate(cert_server_pem)
	public_key_server = cert_server.public_key()
	print("received server certificate:", cert_server.subject.rfc4514_string(), flush=True)
	#print("received server certificate:", ?, flush=True)
	#-------------------check if recv the correct key from server--------------------#
	#public_key_server_pem_check = public_key_server.public_bytes(
	#    encoding=serialization.Encoding.PEM,
	#	format=serialization.PublicFormat.SubjectPublicKeyInfo
	#).decode("utf-8") 
	#print("server pk:", public_key_server_pem_check)
	#------------------------------checked-------------------------------------------#

except ConnectionResetError:
	# server not up
	closed = True
	print("server on this port has not been started!", flush=True)
	print("terminating client...", flush=True)
	sock.close()

finally:
	if not closed:
		sock.close()

# Generate a random 128bits key as the AES-128 Secret Key 
secretKey = os.urandom(16)
print("generated AES key:", secretKey, flush=True)

message = Message2Server

# Creates a message signature σ by hashing the message m using SHA-256 and encrypting
# 	the result with Client private key skC (Use PSS padding for signatures)
signature = private_key_client.sign(
		message.encode("utf-8"),
		padding.PSS(
			mgf=padding.MGF1(hashes.SHA256()),
			salt_length=padding.PSS.MAX_LENGTH
		),
		hashes.SHA256()
	)
print("message signature:", signature, flush=True)

# Encrypts key KS with Server’s public key pkS (Use OAEP paddings for encryption)
secretKey_encrypted_pks = public_key_server.encrypt(
		secretKey,
		padding.OAEP(
			mgf=padding.MGF1(algorithm=hashes.SHA256()),
			algorithm=hashes.SHA256(),
			label=None
		)
	)
  
# Encrypts message and the signature σ using key KS (Use AES encryption with CTR encryption mode)
# iv = os.urandom(16) initialization_vector is set fixed
iv = b'Uz\xbae\x176\xf8\xa2\xfc\xca\x95\x1a\x07\x06\xf9_'
cipher = Cipher(algorithms.AES(secretKey), modes.CTR(iv))
encryptor = cipher.encryptor()
message_encrypted_ks = encryptor.update(message.encode("utf-8")) + encryptor.finalize()
print("encrypted message:", message_encrypted_ks, flush=True)
# 2 identical encryptors are required to avoid 'already finalized' exception, though they take the exactly same constructor
cipher2 = Cipher(algorithms.AES(secretKey), modes.CTR(iv))
encryptor2 = cipher2.encryptor()
signature_encrypted_ks = encryptor2.update(signature) + encryptor2.finalize()

# Creates a new message by concatenating the results of the 3 previous steps: 
#	secretKey_encrypted_pks + message_encrypted_ks + signature_encrypted_ks
finalMessage = "secretKey_encrypted_pks: ".encode("utf-8") + secretKey_encrypted_pks \
				+ " message_encrypted_ks: ".encode("utf-8") + message_encrypted_ks \
					+ " signature_encrypted_ks: ".encode("utf-8") + signature_encrypted_ks
#print(finalMessage)

# Start Socket with Server
sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
serverAddressPort = (Server_IP, Server_PORT)

closed = False
try:
	# Send finalMessage to Server
	print("sending encrypted message to server", flush=True)
	sock.sendto(finalMessage, serverAddressPort)
	# Recv and Decrypt
	Ret = sock.recvfrom(10000)
	msgRet_encrypted_ks = Ret[0]
	# decrypt using cipher created above when encrypting
	decryptor = cipher.decryptor()
	msgRet = decryptor.update(msgRet_encrypted_ks) + decryptor.finalize()
	print("received server response:", msgRet.decode(), flush=True)

except ConnectionResetError:
	# server not up
	closed = True
	print("server on this port has not been started!", flush=True)
	print("terminating client...", flush=True)
	sock.close()

finally:
	if not closed:
		#print("terminating client...", flush=True)
		sock.close()