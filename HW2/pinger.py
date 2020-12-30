import socket
import sys
import signal
from _thread import *
import threading
import time
import struct
#from checksum import checksum 
import random
import select

# global var
payload = ''
count = 0
recv_count = 0
dest = ''

seq_count = 0

ret_info = []
ret_size = 0
ret_addr = 0
ret_ttl = 0
ret_time = []

# global class for returned data stats
# returned Class
class returned:
	def __init__(self, size, seq, ttl, time, addr):
		self.size = size
		self.seq = seq
		self.ttl = ttl
		self.time = time
		self.addr = addr

RETURN = []

# class
ICMP_STRUCTURE_FMT = 'BBHHH'
ICMP_ECHO_REQUEST = 8 # Seems to be the same on Solaris.

ICMP_CODE = socket.getprotobyname('icmp')
ERROR_DESCR = {
	1: ' - Note that ICMP messages can only be '
	   'sent from processes running as root.',
	10013: ' - Note that ICMP messages can only be sent by'
		   ' users or processes with administrator rights.'
}
class ICMPPacket:
	def __init__(self,
		icmp_type = ICMP_ECHO_REQUEST,
		icmp_code = 0,
		icmp_chks = 0,
		icmp_id   = 1,
		icmp_seq  = 1,
		data      = '' ,
		):

		self.icmp_type = icmp_type
		self.icmp_code = icmp_code
		self.icmp_chks = icmp_chks
		self.icmp_id   = icmp_id
		self.icmp_seq  = icmp_seq
		self.data      = data
		self.raw = None
		self.complete = None
		self.create_icmp_field()

	def create_icmp_field(self):
		# dummy hearder
		self.raw = struct.pack(ICMP_STRUCTURE_FMT,
			self.icmp_type,
			self.icmp_code,
			self.icmp_chks,
			self.icmp_id,
			self.icmp_seq,
			)
		
		self.data = bytes(self.data.encode('utf-8'))
		# calculate checksum
		
		self.icmp_chks = self.chksum(self.raw + self.data)	#

		# real header
		self.raw = struct.pack(ICMP_STRUCTURE_FMT,
			self.icmp_type,
			self.icmp_code,
			self.icmp_chks,
			self.icmp_id,
			self.icmp_seq,
			)
		
		self.complete = self.raw + self.data
		return 

	def chksum(self, msg):
		s = 0
		
		# loop taking 2 characters at a time
		if len(msg) % 2:  # if the total length is odd, padding with one octet of zeros for computing the checksum
			msg += b'\x00'
		for i in range(0, len(msg), 2):
			w = (msg[i]) + ((msg[i+1]) << 8 )
			s = s + w
		
		s = (s>>16) + (s & 0xffff);
		s = s + (s >> 16);
		
		#complement and mask to 4 byte short
		s = ~s & 0xffff
		
		return s


# ICMP HEADER Extraction
def ext_icmp_header(icmp):
	icmph=struct.unpack(ICMP_STRUCTURE_FMT, icmp[:8])
	data=icmp[8:]

	ret_icmp={
	'type'  :   icmph[0],
	"code"  :   icmph[1],
	"checksum": icmph[2],
	'id'    :   icmph[3],
	'seq'   :   icmph[4],
	'data'	:	data.decode('utf-8'),
	}
	return ret_icmp

# functions
def catch_ping_reply(s, ID, time_sent, timeout=1):
	global recv_count
	global ret_info
	global ret_size
	global ret_addr
	global ret_ttl

	# create while loop
	while True:
		starting_time = time.time()     # Record Starting Time

		# to handle timeout function of socket
		process = select.select([s], [], [], timeout)
		
		# check if timeout
		if process[0] == []:
			return

		# receive packet
		rec_packet, rec_addr = s.recvfrom(1024)

		ret_size = str(sys.getsizeof(rec_packet))
		ret_addr = rec_addr
		# extract ttl from ip header
		ret_ttl = rec_packet[8]

		# extract icmp packet from received packet 
		# starts from 20 to skip IP header! wow!
		icmp_header = rec_packet[20:28]
		icmp = rec_packet[20:]

		# extract information from icmp packet
		_id = ext_icmp_header(icmp)['id']

		# store returned packet in array {type, code, chksum, id, seq, data}
		ret_info.clear()
		ret_info = ext_icmp_header(icmp)

		# check identification (catch the reply with the same ID sent)
		if _id == ID:
			# found returned packet
			recv_count += 1
			return ext_icmp_header(icmp)
	return -1


#  
def single_ping_request(s, addr=None, payload=None):
	global seq_count
	# Random Packet Id
	pkt_id = random.randrange(0,10000)
	# auto increment Seq
	seq_count += 1
	# Create ICMP Packet
	packet = ICMPPacket(icmp_id=pkt_id, data=payload, icmp_seq=seq_count).complete

	# Send ICMP Packet
	while packet:
		sent = s.sendto(packet, (addr, 1))
		packet = packet[sent:]

	return pkt_id



def print_ping_stats(payload, count, dest):
	global recv_count

	global ret_info
	global ret_size
	global ret_addr
	global ret_ttl
	global ret_time
	global RETURN
	# main - raw socket
	s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)

	print("PING ", dest, ": ", str(sys.getsizeof(payload)), " data bytes", sep='', flush=True)

	for i in range(count):
		# Set timer & Request sent
		start_time = time.time()
		ID = single_ping_request(s, dest, payload)

		# Catch Reply & Stop timer
		reply = catch_ping_reply(s, ID, time.time())
		elapsed_time = (time.time() - start_time) * 1000 	# convert to ms

		if reply == -1:
			# reply not received
			# store stats
			#newReturn = returned(ret_size, ret_info['seq'], ret_ttl, elapsed_time, ret_addr) # ret_info = {type, code, chksum, id, seq, data}
			RETURN.append(-1)
		elif reply:
			# store stats
			newReturn = returned(ret_size, ret_info['seq'], ret_ttl, elapsed_time, ret_addr) # ret_info = {type, code, chksum, id, seq, data}
			RETURN.append(newReturn)
			ret_time.append(elapsed_time)
				# 64 bytes from 172.217.4.174: icmp_seq=0 ttl=56 time=6.966 ms
			print(ret_size, " bytes from ", ret_addr[0], ":icmp_seq=", ret_info['seq'], " ttl=", ret_ttl, " time=", round(elapsed_time, 3), "ms", sep='', flush=True)
				
	# close socket
	s.close()

	print("---", dest, "ping statistics ---", flush=True)
		# 4 packets transmitted, 4 packets received, 0.0% packet loss
	print(count ," packets transmitted, ", recv_count, " packets received, ", round((1-(recv_count/count))*100,1) , "% packet loss", sep='', flush=True)

	if ret_time:
		# calculate stats
		Min = round(min(ret_time), 3)
		Max = round(max(ret_time), 3)
		Avg = round(sum(ret_time) / len(ret_time), 3)
		variance = sum([((x - Avg) ** 2) for x in ret_time]) / len(ret_time) 
		Stddev = round(variance ** 0.5, 3)
			# round-trip min/avg/max/stddev = 3.668/5.025/6.966/1.363 ms
		print("round-trip min/avg/max/stddev = ", Min, "/", Avg, "/", Max, "/", Stddev, " ms", sep='', flush=True)
			# <min>,<max>,<avg>
		print(str(Min) + ',' + str(Max) + ','+ str(Avg))
		return (str(Min) + ',' + str(Max) + ','+ str(Avg))
	else:
		print("round-trip min/avg/max/stddev = N/A / N/A / N/A / N/A ms", sep='', flush=True)
		return 'N/A,N/A,N/A'

def main():
	# main - parse:	
	destBool = False
	payloadBool = False

	if len(sys.argv) == 1:
		print("---------------------------------------Usage Instructions-----------------------------------------", flush=True)
		print("Please eneter in format of 'python3 pinger.py -p <payload> -c <count> -d <destination>'", flush=True)
		print("Payload has to be a string surounded by double quotes", flush=True)
		print("Count has a default 10 (number of packets used to compute RTT)", flush=True)
		exit()

	elif len(sys.argv) == 7 or len(sys.argv) == 5:
		if '-p' in sys.argv:
			payloadBool = True
			payload = str(sys.argv[sys.argv.index('-p') + 1])
			
		if '-c' in sys.argv:
			try:
				count = int(sys.argv[sys.argv.index('-c') + 1])
			except ValueError:
				print("Count must be an Integer.", flush=True)
		else:
			count = 10

		if '-d' in sys.argv:
			try:
				dest = str(sys.argv[sys.argv.index('-d') + 1])
				destBool = True
			except ValueError:
				print("Count must be an Integer.", flush=True)

		if not payloadBool or not destBool:
			print("---------------------------------------Usage Instructions-----------------------------------------", flush=True)
			print("Please eneter in format of 'python3 pinger.py -p <payload> -c <count> -d <destination>'", flush=True)
			print("payload has to be a string surounded by double quotes", flush=True)
			print("count has a default 10 (number of packets used to compute RTT)", flush=True)
			exit()
	else:
		print("---------------------------------------Usage Instructions-----------------------------------------", flush=True)
		print("Please eneter in format of 'python3 pinger.py -p <payload> -c <count> -d <destination>'", flush=True)
		print("payload has to be a string surounded by double quotes", flush=True)
		print("count has a default 10 (number of packets used to compute RTT)", flush=True)
		exit()

	# this should call to send & receive ICMP packets and calculate stats and print out all terminal outputs aside form this instructions
	print_ping_stats(payload, count, dest)

	return

if __name__=='__main__':
	main()