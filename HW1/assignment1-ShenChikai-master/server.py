import socket
import sys
import signal
from _thread import *
import threading

print_lock = threading.Lock()
sock_lock = threading.Lock()

# Client Class
class Client:
	def __init__(self, name, ip, port):
		self.name = name
		self.ip = ip
		self.port = port

clientDatabase = []

# Overlay Server
class OverlayServer:
	def __init__(self, connection, OverlayServerAddr):
		self.connection = connection
		self.OverlayServerAddr = OverlayServerAddr

overlayServerDatabase = []

# Sending Info needs to be global for the threads to constantly check on
toClientFrom = ''
toClientTo = ''
toClientMsg = ''

# Thread for connections to clients
def threaded(name, ip, port, sock):
	toClientAddr = (ip, port)
	global toClientFrom
	global toClientTo
	global toClientMsg
	while True: 
		# Send?
		if toClientTo == name:
			toMsg = toClientFrom + ": " + toClientMsg
			sock_lock.acquire()
			sock.sendto(toMsg.encode(),toClientAddr)
			sock_lock.release()
			# Reset recepient name
			toClientTo = ''

# Thread for listening and accepting requests from other servers
def listenForConnection(listenSock, listenPort):
	global overlayServerDatabase
	print_lock.acquire()
	print("server overlay started at port", listenPort)
	print_lock.release()
	# Listen for connection request
	listenSock.listen()
	while True:
		connection, OverlayServerAddr = listenSock.accept()
		# add the received server to the database
		newOverlayServer = OverlayServer(connection, OverlayServerAddr)
		overlayServerDatabase.append(newOverlayServer)
		print_lock.acquire()
		print("server overlay connection from host", OverlayServerAddr[0], "port", OverlayServerAddr[1])
		print_lock.release()
		# Start a new thread for this overlay server
		start_new_thread(listenForMsg, (connection, listenSock))

# Thread for listening for messages from other servers
def listenForMsg(connection, listenSock):
	global clientDatabase
	global overlayServerDatabase
	global sockRequest
	while True:
		try:
			OverlayServerMsg = connection.recv(1024).decode()
			print_lock.acquire()
			print("Received from overlay server:", OverlayServerMsg)
			print_lock.release()
			# If toClienTo is not registered here, redirect msg
			splited = OverlayServerMsg.split(" ", 3)
			toClientFrom = splited[0]
			toClienTo = splited[2]
			inClientDB = False
			for c in clientDatabase:
				if c.name == toClienTo:
					inClientDB = True
					toClientAddr = (c.ip, c.port)
					break
			if inClientDB:
				# Registered
				newMsg = toClientFrom + ' ' + OverlayServerMsg[OverlayServerMsg.index(':') :]
				sock_lock.acquire()
				sock.sendto(newMsg.encode(), toClientAddr)
				sock_lock.release()
			else:
				# Not Registered, redirect to overlay servers
				print_lock.acquire()
				print(toClienTo, "is not registered with server")
				print("Sending message to overlay server:", OverlayServerMsg)
				print_lock.release()
				for s in overlayServerDatabase:
					s.connection.sendall(OverlayServerMsg.encode())
				if overlayServer:
					sockRequest.sendall(OverlayServerMsg.encode())
		except ConnectionResetError:
			sock_lock.acquire()
			print("Lost connection from a received overlay server")
			break
			sock_lock.release()

# recvOnRequestedServer
def recvOnRequestedServer(sockRequest):
	global clientDatabase
	global overlayServerDatabase
	while True:
		try:
			RequestedServerMsg = sockRequest.recv(1024).decode()
			print("Received from overlay server:", RequestedServerMsg)
			# If toClienTo is not registered here, redirect msg
			splited = RequestedServerMsg.split(" ", 3)
			toClientFrom = splited[0]
			toClienTo = splited[2]
			inClientDB = False
			for c in clientDatabase:
				if c.name == toClienTo:
					inClientDB = True
					toClientAddr = (c.ip, c.port)
					break
			if inClientDB:
				# Registered
				newMsg = toClientFrom + ' ' + RequestedServerMsg[RequestedServerMsg.index(':') :]
				sock_lock.acquire()
				sock.sendto(newMsg.encode(), toClientAddr)
				sock_lock.release()
			else:
				# Not Registered, redirect to overlay servers
				print_lock.acquire()
				print(toClienTo, "is not registered with server")
				print("Sending message to overlay server:", RequestedServerMsg)
				print_lock.release()
				for s in overlayServerDatabase:
					s.connection.sendall(RequestedServerMsg.encode())
				if overlayServer:
					sockRequest.sendall(RequestedServerMsg.encode())
		except ConnectionResetError:
			sock_lock.acquire()
			print("Lost connection from the requested overlay server")
			break
			sock_lock.release()

# Get Port Number from 'server.py -p <portNumber>'
# sys.argv = ['server.py', '-p', 'portNumber', '-s', overlayServerIP, '-t', overlayServerPort, '-o', overlayListeningPort]

listenForServer = False
listenPort = int

overlayServer = False
overlayServerIP = ''
overlayServerPort = int

if len(sys.argv) == 1:
	print("Please enter in format of 'server.py -p <portNumber> -s <overlayServerIP> -t < overlayServerPort> -o <overlayListeningPort>'.")
	print("'-p' is the only required argument, and please include the whitespace.")
	exit()
elif len(sys.argv) == 3:
	try:
		UDP_PORT = int(sys.argv[2])
	except ValueError:
		print("Port number must be an Integer.")
elif len(sys.argv) > 3 and len(sys.argv) < 10:
	# get port first
	try:
		UDP_PORT = int(sys.argv[2])
	except ValueError:
		print("Port number must be an Integer.")
	# Listen -o
	if '-o' in sys.argv:
		try:
			listenPort = int(sys.argv[sys.argv.index('-o') + 1])
			listenForServer = True
		except ValueError:
			print("Port number which the server listens for must be an Integer.")
	# Overlay -s -t
	if '-s' in sys.argv and '-t' in sys.argv:
		try:
			overlayServerIP = str(sys.argv[sys.argv.index('-s') + 1])
			overlayServerPort = int(sys.argv[sys.argv.index('-t') + 1])
			overlayServer = True
		except ValueError:
			print("Port number to request for must be an Integer.")
else:
	print("Please eneter in format of 'server.py -p <portNumber> -s <overlayServerIP> -t < overlayServerPort> -o <overlayListeningPort>'.")
	print("'-p' is the only required argument, and please include the whitespace.")
	exit()

# Start Socket
UDP_IP = "127.0.0.1"
sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)

# UDP server does not build an actual connections with its client, it only binds to a specific (ip, port)
try:
	sock.bind((UDP_IP, UDP_PORT))
except OSError:
	print("The port is unavailable. Please try another port number.")
	exit()

print("server started on 127.0.0.1 at port", UDP_PORT)

closed = False

# Overlay Server?
if overlayServer:
	# Connect to the target server
	sockRequest = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sockRequest.connect((overlayServerIP, overlayServerPort))
	print("connected to overlay server at", overlayServerIP, "port", overlayServerPort)
	start_new_thread(recvOnRequestedServer, (sockRequest,))

# Listen Server?
if listenForServer:
	# Start a new TCP socket for listening
	# Start Socket
	listenSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	try:
		listenSock.bind(('127.0.0.1', listenPort))
		# Start a new thread to connect
		start_new_thread(listenForConnection, (listenSock, listenPort))
	except OSError:
		print("The port is unavailable for listening. Please try another port number.")
		exit()

try:
	while True:
		# Register:
		# Recv and Parse
		regMsg = sock.recvfrom(1024)
		regMsgMsg = regMsg[0].decode()
		regMsgAddr = regMsg[1]
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
			print(clientName, "registered from host", clientIP, "port", clientPort)
			print_lock.release()
			# Start a thread for this client
			start_new_thread(threaded, (clientName, clientIP, clientPort, sock))
		elif regMsgMsg.find('sendto') == 0:
			# Sendto:
			splited = regMsgMsg.split(" ", 2)
			toClientToTemp = splited[1]
			toClientMsg = splited[2]
			# Check who send this
			clientIP = regMsgAddr[0]
			clientPort = regMsgAddr[1]
			for c in clientDatabase:
				if c.ip == clientIP and c.port == clientPort:
					toClientFrom = c.name
					break
			# Check send to who
			inClientDB = False
			for c in clientDatabase:
				if c.name == toClientToTemp:
					inClientDB = True
					break
			# Send?
			if inClientDB:
				# Update toClientTo to inform the thread
				toClientTo = toClientToTemp
				# Print send info
				print_lock.acquire()
				print(toClientFrom, "to", toClientToTemp, ":", toClientMsg)
				print_lock.release()
			else:
				print_lock.acquire()
				print(toClientFrom, "to", toClientToTemp, ":", toClientMsg)
				print(toClientToTemp, "is not registered with server")
				print("Sending message to overlay server:", toClientFrom, "to", toClientToTemp, ":", toClientMsg)
				print_lock.release()
				# Not Registered, redirect to overlay servers (requested + listened)
				overlayMsg = toClientFrom + " to " + toClientToTemp + " : " + toClientMsg
				for s in overlayServerDatabase:
					s.connection.sendall(overlayMsg.encode())
				if overlayServer:
					sockRequest.sendall(overlayMsg.encode())
				

			# Reset inClientDB
			inClientDB = False

except KeyboardInterrupt:
	# ctrl + c
	closed = True
	print_lock.acquire()
	print("terminating server...")
	print_lock.release()
	sock.close()

finally:
	if not closed:
		print_lock.acquire()
		print("terminating server...")
		print_lock.release()
		sock.close()