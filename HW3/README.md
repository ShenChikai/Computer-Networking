# Assignment 3
# Denny Shen
# dennyshe@usc.edu

# Compile Instruction

## The three python scripts tested under windows environment using terminal commands (example):
### >py server.py -p 5051 -l server.txt
### >py nat.py -m 5077 -d 127.0.0.1 -p 5051 -l nat.txt
### >py client.py -s 127.0.0.1 -p 5077 -m 6069 -n denny3 -l client3.txt
## When sending message from Client, 'sendto ' must be the prefix of the message
## The Client would connect to the NAT server, and the NAT server would have the address of the actual server
## The Client info table is kept in a list of Client class
## The Server must be started for the Client to send anything through NAT
## The random port is generated using '6000 + random.randint(0, 2999)'
## 'open' function is called to further write to the text files, the text file would be generated or overwritten if not existed
