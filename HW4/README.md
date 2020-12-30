# Assignment 4
## Certificate Management & Confidential Communication
## Denny Shen
## dennyshe@usc.edu
## 2491547502

# Instruction
## Commands Example
### py ca.py -p 10000
### py server.py -p 5050 -ss 127.0.0.1 -pp 10000 -m ServerMessage
### py client.py -s 127.0.0.1 -p 5050 -ss 127.0.0.1 -pp 10000 -m ClientMessage
## Notice
### pip install cryptography
### The PEM of the keys are printed to the console since the key itself is an RSA key object.
### CA, Server, and Client will all be running on 127.0.0.1 for clearness
### Because all the three python scripts utilizes UDP connection, sending ports will be random, recving ports will be used as declared.
### Since the client doesn't take in an argument for its port, it will send on a random port and does not need to bind to an address. The console log will just print client started on 127.0.0.1 at port 50505 to fit the desired console format (though it has nothing to do with the actual port).
### rfc4514_string() function is used to get rid of angle brackets of the certificate information.
### initialization_vector iv is set to be the same for both client and server for AES encryption under CTR mode
### public_key.verify() is used to check if the signature matches with the hash decrypted message.