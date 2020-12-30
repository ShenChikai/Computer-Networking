import socket
import sys, os
import signal
from _thread import *
import threading

# Thread for recv from server
def threaded(sock):
	recvFromMsg = ''
	while True:
		try: 
			recvFromMsg = sock.recvfrom(1024)
			printMsg = recvFromMsg[0].decode()
			# Received message
			print(printMsg, flush=True, end='')
			# Reset recvFromMsg
			recvFromMsg = ''
		except Exception:
			break
		

# Get Port Number from 'server.py -s <serverAddr> -p <serverPort> -n <clientName>'
# sys.argv = ['server.py', '-s', '<serverAddr>', '-p', 'portNumber', '-n', 'clientName']
if len(sys.argv) == 1:
	print("Please eneter information in format of 'server.py -s <serverAddr> -p <serverPort> -n <clientName>'. \nPlease include the whitespace.", flush=True)
	exit()
elif len(sys.argv) >= 6:
	try:
		UDP_IP = str(sys.argv[2])
		UDP_PORT = int(sys.argv[4])
		clientName = ""
		for i in range(6, len(sys.argv)):
			if i > 6:
				clientName += ' '
			clientName += str(sys.argv[i])
	except ValueError:
		print("Please enter the information in its correct format.", flush=True)
		print("Please eneter information in format of 'server.py -s <serverAddr> -p <serverPort> -n <clientName>'. \nPlease include the whitespace.", flush=True)
else:
	print("Please eneter information in format of 'server.py -s <serverAddr> -p <serverPort> -n <clientName>'. \nPlease include the whitespace.", flush=True)
	exit()

# Start Socket
sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
serverAddressPort = (UDP_IP, UDP_PORT)

closed = False

try:
	# Register
	regMsg = "register " + clientName
	sock.sendto(regMsg.encode(), serverAddressPort)
	regRet = sock.recv(1024).decode()
	print("connected to server and registered", clientName, flush=True)

	# Registerd
	# Start a thread listening on msg from server
	start_new_thread(threaded, (sock,))
	# Send msg to someone thru server
	while True:
		# Send message
		sendtoMsg = sys.stdin.readline()
		# 'Exit'?
		if sendtoMsg.lower() == "exit\n":
			print("terminating client...", flush=True)
			sock.close()
			os._exit(0)
			break
		else: 
			sock.sendto(sendtoMsg.encode(), serverAddressPort)

except ConnectionResetError:
	# server not up
	closed = True
	print("server on this port has not been started!", flush=True)
	print("terminating client...", flush=True)
	sock.close()

except KeyboardInterrupt:
	# ctrl + c
	closed = True
	print("terminating client...", flush=True)
	sock.close()

finally:
	if not closed:
		print("terminating client...", flush=True)
		sock.close()