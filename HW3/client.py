# client.py -s <serverAddress> -p <serverPort> -m <clientPort> -n clientName -l logfile
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
			recv_IP = recvFromMsg[1][0]
			recv_PORT = recvFromMsg[1][1]
			# Received message
			print("recvfrom ", printMsg, flush=True, sep ='', end='')
			# Write to log
			#writeLine = "recvfrom " + str(recv_IP) + "," + str(recv_PORT) + " " + printMsg + "\n"
			#logfile.write(writeLine) 
			#ogfile.flush()						# keep same with the example, don't write recv to log 

			# Reset recvFromMsg
			recvFromMsg = ''
		except Exception:
			break
		

# client.py -s <serverAddress> -p <serverPort> -m <clientPort> -n <clientName> -l <logfile>
# sys.argv = ['server.py', '-s', '<serverAddr>', '-p', 'portNumber', '-m', 'clientPort', '-n', 'clientName', l , 'logfile']
if len(sys.argv) == 1:
	print("Please eneter information in format of 'Python3 client.py -s <serverAddress> -p <serverPort> -m <clientPort> -n <clientName> -l <logfile>'", flush=True)
	exit()
elif len(sys.argv) == 11:
	try:
		UDP_IP = str(sys.argv[2])
		UDP_PORT = int(sys.argv[4])
		clientPort = int(sys.argv[6])
		clientName = str(sys.argv[8])
		LOG_FILE = str(sys.argv[10])
		if LOG_FILE.find('.txt') != (len(LOG_FILE) - 4):
			print("Log file must be a text file that ends in .txt format", flush=True)
			exit()
		else :
			logfile = open(LOG_FILE,"w+")
	except ValueError:
		print("Please enter the information in its correct format.", flush=True)
		print("Please eneter information in format of 'Python3 client.py -s <serverAddress> -p <serverPort> -m <clientPort> -n <clientName> -l <logfile>'", flush=True)
		exit()
else:
	print("Please eneter information in format of 'Python3 client.py -s <serverAddress> -p <serverPort> -m <clientPort> -n <clientName> -l <logfile>'", flush=True)
	exit()

# Start Socket
sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
sock.bind(('127.0.0.1', clientPort))
serverAddressPort = (UDP_IP, UDP_PORT)

closed = False

try:
	# Connecting
	print("connected to server and registered", clientName, flush=True)	# same as hw1
	# print("connecting to the server", UDP_IP, "at port", UDP_PORT, flush=True)
	# Write to log
	writeLine = "connecting to the server " + str(UDP_IP) + " at port " + str(UDP_PORT) + "\n"
	logfile.write(writeLine) 
	logfile.flush() 
	# Register
	regMsg = "register " + clientName
	sock.sendto(regMsg.encode(), serverAddressPort)
	regRet = sock.recv(1024).decode()
	# Write to log
	writeLine = "sending register message " + clientName + "\n"
	logfile.write(writeLine) 
	logfile.flush() 

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
		elif sendtoMsg.find('sendto') == 0:
			# Legit Message, Send to Server
			sock.sendto(sendtoMsg.encode(), serverAddressPort)
			# Write to log
			writeLine = "sending " + str(UDP_IP) + "," + str(UDP_PORT) + " " + sendtoMsg[7:]
			logfile.write(writeLine) 
			logfile.flush() 

except ConnectionResetError:
	# server not up
	closed = True
	print("server on this port has not been started!", flush=True)
	print("terminating client...", flush=True)
	sock.close()

except KeyboardInterrupt:
	# ctrl + c
	logfile.close()
	closed = True
	print("terminating client...", flush=True)
	sock.close()

finally:
	logfile.close()
	if not closed:
		print("terminating client...", flush=True)
		sock.close()