# Assignment 1 
## Denny Shen
## dennyshe@usc.edu

### This assignment should contain two python files, server.py and client.py
### The programs are tested under windows environment
### Example commands on windows:
- For server: py server.py -p 5055 -o 20000 -s 127.0.0.1 -t 20002
- For client: py client.py -s 127.0.0.1 -p 5055 -n Trojan

### Notice:
- If a message to a unkown client was sent, the message would be redirected back and forth between the servers since such client is unregistered with any of them. This looping message could be potentially solved by attaching a lifespan to each message redirected.
- Connection between server and client uses UDP which technically does not establish an actual connection
- Connection between server and server uses TCP which establishes stable connection, and one server would be informed if another server went done
- 