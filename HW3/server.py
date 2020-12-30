# server.py -p <portno> -l <logfile>
import socket
import sys
import signal
from _thread import *
import threading
import time

print_lock = threading.Lock()
sock_lock = threading.Lock()

# Client Class
class Client:
	def __init__(self, name, ip, port):
		self.name = name
		self.ip = ip
		self.port = port

clientDatabase = []


# Sending Info needs to be global for the threads to constantly check on
toClientFrom = ''
toClientTo = ''
toClientMsg = ''

# server.py -p <portno> -l <logfile>
# sys.argv = ['server.py', '-p', 'portNumber', '-l', logfile.txt]

if len(sys.argv) == 1:
	print("Please enter in format of 'Python3 server.py -p portno -l logfile'", flush=True)
	exit()
elif len(sys.argv) == 5:
	try:
		UDP_PORT = int(sys.argv[2])	# Global Var
	except ValueError:
		print("Port number must be an Integer.", flush=True)

	try:
		LOG_FILE = str(sys.argv[4])	# Global Var 
		if LOG_FILE.find('.txt') != (len(LOG_FILE) - 4):
			print("Log file must be a text file that ends in .txt format", flush=True)
			exit()
		else :
			logfile = open(LOG_FILE,"w+")
	except ValueError:
		print("Please enter a correct file name.", flush=True)
else:
	print("Please eneter in format of 'Python3 server.py -p portno -l logfile'", flush=True)
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

print("server started on 127.0.0.1 at port", UDP_PORT)
# Write to log
writeLine = "server started on " + str(UDP_IP) + " at port " + str(UDP_PORT) + "..." + '\n'
logfile.write(writeLine)
logfile.flush() 

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
			# Store in clientDatabase
			newClient = Client(clientName, clientIP, clientPort)
			clientDatabase.append(newClient)
			# Send reply
			regRet = "Welcome " + clientName
			sock_lock.acquire()
			sock.sendto(regRet.encode(),regMsgAddr)
			sock_lock.release()
			# Print finish register
			print_lock.acquire()
			print(clientName, "registered from host", clientIP, "port", clientPort, flush=True)
			print_lock.release()
			# Start a thread for this client
			# start_new_thread(threaded, (clientName, clientIP, clientPort, sock))
		else:
			# Recv Message
			clientIP = regMsgAddr[0]
			clientPort = regMsgAddr[1]
			print("recvfrom ", regMsgMsg, sep='', flush=True, end='')
			# Write to log
			writeLine = "recvfrom " + regMsgMsg
			logfile.write(writeLine)
			logfile.flush()  
			# Send this Message back to the Sender
			regMsgMsg = "[BACK] " + regMsgMsg
			sock.sendto(regMsgMsg.encode(),regMsgAddr)
			

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