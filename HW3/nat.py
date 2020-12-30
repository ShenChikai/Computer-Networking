# nat.py -m myPort -d destinationIP -p destinationPort -l logfile
import socket
import sys
import signal
from _thread import *
import threading
import time
import random

print_lock = threading.Lock()
sock_lock = threading.Lock()

# Client Class
class Client:
	def __init__(self, name, ip, port, newip, newport):
		self.name = name
		self.ip = ip
		self.port = port
		self.newip = newip
		self.newport = newport

clientDatabase = []

# Sending Info needs to be global for the threads to constantly check on
toClientFrom = ''
toClientTo = ''
toClientMsg = ''
randNum = 6000 + random.randint(0, 2999)

# nat.py -m myPort -d destinationIP -p destinationPort -l logfile
# sys.argv = ['server.py', '-m', 'myPort', '-d', destinationIP, '-p', 'destinationPort', '-l' , 'logfile.txt']

if len(sys.argv) == 1:
	print("Please enter in format of 'Python3 nat.py -m myPort -d destinationIP -p destinationPort -l logfile'", flush=True)
	exit()
elif len(sys.argv) == 9:
	try:
		UDP_PORT = int(sys.argv[2])	# Global Var
		destinationIP = str(sys.argv[4])
		destinationPort = int(sys.argv[6])
		serverAddr = (destinationIP, destinationPort)
	except ValueError:
		print("Note: Port number must be an Integer.", flush=True)
		exit()
	try:
		LOG_FILE = str(sys.argv[8])	# Global Var 
		if LOG_FILE.find('.txt') != (len(LOG_FILE) - 4):
			print("Log file must be a text file that ends in .txt format", flush=True)
			exit()
		else :
			logfile = open(LOG_FILE,"w+")
	except ValueError:
		print("Please enter a correct file name.", flush=True)
		exit()
else:
	print("Please eneter in format of 'Python3 nat.py -m myPort -d destinationIP -p destinationPort -l logfile'", flush=True)
	exit()

# Start Socket
UDP_IP = "127.0.0.1"
sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)

# UDP server does not build an actual connections with its client, it only binds to a specific (ip, port)
try:
	sock.bind((UDP_IP, UDP_PORT))
except OSError:
	print("The port is unavailable. Please try another port number.", flush=True)
	exit()

print("NAT server started on 127.0.0.1 at port", UDP_PORT)

closed = False

try:
	while True:
		# Register:
		# Recv and Parse
		regMsg = sock.recvfrom(1024)
		regMsgMsg = regMsg[0].decode()	# Message
		regMsgAddr = regMsg[1]			# Addr,Port
		# Check: [register, sendto]
		if regMsgMsg.find('register') == 0 :
			# Register:
			clientName = regMsgMsg[(regMsgMsg.index('register') + 9):]
			clientIP = regMsgAddr[0]
			clientPort = regMsgAddr[1]
			# Find new IP/PORT
			newIP = socket.gethostbyname(socket.gethostname())
			newPort = randNum
			randNum = 6000 + random.randint(0, 2999)
			# Check in database??
			exist = False
			for c in clientDatabase:
				if c.port == clientPort:
					exist = True
			# Store in clientDatabase if not existed yet
			if not exist:
				newClient = Client(clientName, clientIP, clientPort, newIP, newPort)
				clientDatabase.append(newClient)
				# Write to log
				writeLine = clientName + ' | ' + str(clientIP) + ', ' + str(clientPort) + ' | ' + str(newIP) + ', ' + str(newPort) + "\n"
				logfile.write(writeLine)
				logfile.flush()  
				# Send reply
				regRet = "Welcome, " + clientName + ". You have registered with NAT."
				sock_lock.acquire()
				sock.sendto(regRet.encode(),regMsgAddr)
				sock_lock.release()
				# Print finish register
				print_lock.acquire()
				print(clientName, "registered from host", clientIP, "port", clientPort,"to NAT" ,flush=True)
				print_lock.release()
			else:
				print(clientName, "have already registered",flush=True)
			# Start a thread for this client
			#start_new_thread(threaded, (clientName, clientIP, clientPort, sock))
		elif regMsgMsg.find('sendto') == 0:
			# Recv Message from Client to be forwarded to Server
			clientIP = regMsgAddr[0]
			clientPort = regMsgAddr[1]
			regMsgMsg = regMsgMsg[7:]
			# Find this client using its port
			for c in clientDatabase:
				if c.port == clientPort:
					newAddr = (c.newip, c.newport)
					print("forwarding message for Client: ", regMsgMsg, sep='', flush=True, end='')
					regMsgMsg = str(newAddr[0]) + ',' + str(newAddr[1]) + ' ' + regMsgMsg
					# Send this Message back to the Sender
					sock.sendto(regMsgMsg.encode(),serverAddr)
		elif regMsgMsg.find('[BACK] ') == 0:
			# Recv Message from Client to be forwarded to Server
			serverIP = regMsgAddr[0]
			serverPort = regMsgAddr[1]
			regMsgMsg = regMsgMsg[7:]
			portIndex = regMsgMsg.find(',') + 1	
			clientFakePort = ''
			for i in range(4):
				clientFakePort = str(clientFakePort) + str(regMsgMsg[portIndex + i])
			for c in clientDatabase:
				if c.newport == int(clientFakePort):
					clientRealAddr = (c.ip, c.port)
					# Re-format Message
					regMsgMsg = regMsgMsg[regMsgMsg.find(',') + 6:]
					print("forwarding message for Server: ", regMsgMsg, sep='', flush=True, end='')
					regMsgMsg = str(serverIP) + ','+ str(serverPort) + " " +regMsgMsg
					# Send back to Client
					sock.sendto(regMsgMsg.encode(),clientRealAddr)


except KeyboardInterrupt:
	# ctrl + c
	logfile.close()
	closed = True
	print_lock.acquire()
	print("terminating server...", flush=True)
	print_lock.release()
	sock.close()

finally:
	logfile.close()
	if not closed:
		print_lock.acquire()
		print("terminating server...", flush=True)
		print_lock.release()
		sock.close()