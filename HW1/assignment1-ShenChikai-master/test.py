from subprocess import Popen, PIPE
from unittest import TestCase
import signal
import threading
import random
import logging

# use `sudo lsof -i -P -n` to make sure all processes have been terminated


def get_random_string():
    return "-" + str(random.randrange(0, 100000))


TIME_INTERVAL = 1  # in seconds
testcase = TestCase()
CLIENT1 = "client1" + get_random_string()
CLIENT2 = "client2" + get_random_string()
UNKNOWNCLIENT = "unknownClient" + get_random_string()
MESSAGE1 = "message1" + get_random_string()
MESSAGE2 = "message2" + get_random_string()
CLEANUP_COMMANDS = ["pkill -f python",
                    "pkill -f Python"
                    ]


# constants for test 1
TEST1_SERVER_PORT = str(random.randrange(6600, 9000))
TEST1_COMMANDS = ["python3 server.py -p " + TEST1_SERVER_PORT,
                  "python3 client.py -s 127.0.0.1 -p " + TEST1_SERVER_PORT + " -n " + CLIENT1
                  ]
TEST1_SERVER_INPUTS = []
TEST1_CLIENT_INPUTS = ["exit"]
TEST1_EXPECTED_SERVER_OUTPUTS = ["server started on 127.0.0.1 at port " + TEST1_SERVER_PORT,
                                 CLIENT1 + " registered from host 127.0.0.1 port "
                                 ]
TEST1_EXPECTED_CLIENT_OUTPUTS = ["connected to server and registered " + CLIENT1,
                                 "terminating client..."
                                 ]

# constants for test2
TEST2_SERVER_PORT = str(random.randrange(6600, 9000))
TEST2_COMMANDS = ["python3 server.py -p " + TEST2_SERVER_PORT,
                  "python3 client.py -s 127.0.0.1 -p " + TEST2_SERVER_PORT + " -n " + CLIENT1,
                  "python3 client.py -s 127.0.0.1 -p " + TEST2_SERVER_PORT + " -n " + CLIENT2
                  ]
TEST2_SERVER_INPUTS = []
TEST2_CLIENT1_INPUTS = []
TEST2_CLIENT2_INPUTS = []
TEST2_EXPECTED_SERVER_OUTPUTS = ["server started on 127.0.0.1 at port " + TEST2_SERVER_PORT,
                                 CLIENT1 + " registered from host 127.0.0.1 port ",
                                 CLIENT2 + " registered from host 127.0.0.1 port "
                                 ]
TEST2_EXPECTED_CLIENT1_OUTPUTS = ["connected to server and registered " + CLIENT1
                                 ]
TEST2_EXPECTED_CLIENT2_OUTPUTS = ["connected to server and registered " + CLIENT2
                                 ]

# constants for test3
TEST3_SERVER_PORT = str(random.randrange(6600, 9000))
TEST3_COMMANDS = ["python3 server.py -p " + TEST3_SERVER_PORT,
                  "python3 client.py -s 127.0.0.1 -p " + TEST3_SERVER_PORT + " -n " + CLIENT1,
                  "python3 client.py -s 127.0.0.1 -p " + TEST3_SERVER_PORT + " -n " + CLIENT2
                  ]
TEST3_SERVER_INPUTS = []
TEST3_CLIENT1_INPUTS = ["sendto " + CLIENT2 + " " + MESSAGE1,
                        "sendto " + UNKNOWNCLIENT + " " + MESSAGE2
                        ]
TEST3_CLIENT2_INPUTS = []
TEST3_EXPECTED_SERVER_OUTPUTS = ["server started on 127.0.0.1 at port " + TEST3_SERVER_PORT,
                                 CLIENT1 + " registered from host 127.0.0.1 port ",
                                 CLIENT2 + " registered from host 127.0.0.1 port ",
                                 CLIENT1 + " to " + CLIENT2 + ": " + MESSAGE1,
                                 CLIENT1 + " to " + UNKNOWNCLIENT + ": " + MESSAGE2,
                                 UNKNOWNCLIENT + " is not registered with server"
                                 ]
TEST3_EXPECTED_CLIENT1_OUTPUTS = ["connected to server and registered " + CLIENT1
                                 ]
TEST3_EXPECTED_CLIENT2_OUTPUTS = ["connected to server and registered " + CLIENT2,
                                 CLIENT1 + ": " + MESSAGE1
                                 ]

# constants for test4
TEST4_SERVER1_PORT = str(random.randrange(6600, 9000))
TEST4_SERVER2_PORT = str(random.randrange(6600, 9000))
TEST4_SERVER1_OVERLAY_PORT = str(random.randrange(6600, 9000))
TEST4_SERVER2_OVERLAY_PORT = str(random.randrange(6600, 9000))
TEST4_COMMANDS = ["python3 server.py -p " + TEST4_SERVER1_PORT + " -o " + TEST4_SERVER1_OVERLAY_PORT,
                  "python3 server.py -p " + TEST4_SERVER2_PORT + " -s 127.0.0.1 -t " + TEST4_SERVER1_OVERLAY_PORT + " -o " + TEST4_SERVER2_OVERLAY_PORT,
                  "python3 client.py -s 127.0.0.1 -p " + TEST4_SERVER1_PORT + " -n " + CLIENT1,
                  "python3 client.py -s 127.0.0.1 -p " + TEST4_SERVER2_PORT + " -n " + CLIENT2
                  ]
TEST4_SERVER1_INPUTS = []
TEST4_SERVER2_INPUTS = []
TEST4_CLIENT1_INPUTS = ["sendto " + CLIENT2 + " " + MESSAGE1
                        ]
TEST4_CLIENT2_INPUTS = []
TEST4_EXPECTED_SERVER1_OUTPUTS = ["server started on 127.0.0.1 at port " + TEST4_SERVER1_PORT,
                                  "server overlay started at port " + TEST4_SERVER1_OVERLAY_PORT,
                                  "server overlay connection from host 127.0.0.1 port ",
                                 CLIENT1 + " registered from host 127.0.0.1 port ",
                                 CLIENT1 + " to " + CLIENT2 + ": " + MESSAGE1,
                                 CLIENT2 + " is not registered with server",
                                 "Sending message to overlay server: " + CLIENT1 + " to " + CLIENT2 + ": " + MESSAGE1
                                 ]
TEST4_EXPECTED_SERVER2_OUTPUTS = ["server started on 127.0.0.1 at port " + TEST4_SERVER2_PORT,
                                  "server overlay started at port " + TEST4_SERVER2_OVERLAY_PORT,
                                  "connected to overlay server at 127.0.0.1 port " + TEST4_SERVER1_OVERLAY_PORT,
                                 CLIENT2 + " registered from host 127.0.0.1 port ",
                                 "Received from overlay server: " + CLIENT1 + " to " + CLIENT2 + ": " + MESSAGE1
                                 ]
TEST4_EXPECTED_CLIENT1_OUTPUTS = ["connected to server and registered " + CLIENT1
                                 ]
TEST4_EXPECTED_CLIENT2_OUTPUTS = ["connected to server and registered " + CLIENT2,
                                 CLIENT1 + ": " + MESSAGE1
                                 ]

# constants for test5
TEST5_SERVER1_PORT = str(random.randrange(6600, 9000))
TEST5_SERVER2_PORT = str(random.randrange(6600, 9000))
TEST5_SERVER1_OVERLAY_PORT = str(random.randrange(6600, 9000))
TEST5_SERVER2_OVERLAY_PORT = str(random.randrange(6600, 9000))
TEST5_COMMANDS = ["python3 server.py -p " + TEST5_SERVER1_PORT + " -o " + TEST5_SERVER1_OVERLAY_PORT,
                  "python3 server.py -p " + TEST5_SERVER2_PORT + " -s 127.0.0.1 -t " + TEST5_SERVER1_OVERLAY_PORT + " -o " + TEST5_SERVER2_OVERLAY_PORT,
                  "python3 client.py -s 127.0.0.1 -p " + TEST5_SERVER1_PORT + " -n " + CLIENT1,
                  "python3 client.py -s 127.0.0.1 -p " + TEST5_SERVER2_PORT + " -n " + CLIENT2
                  ]
TEST5_SERVER1_INPUTS = []
TEST5_SERVER2_INPUTS = []
TEST5_CLIENT1_INPUTS = ["sendto " + CLIENT2 + " " + MESSAGE1
                        ]
TEST5_CLIENT2_INPUTS = ["sendto " + CLIENT1 + " " + MESSAGE2
                        ]
TEST5_EXPECTED_SERVER1_OUTPUTS = ["server started on 127.0.0.1 at port " + TEST5_SERVER1_PORT,
                                  "server overlay started at port " + TEST5_SERVER1_OVERLAY_PORT,
                                  "server overlay connection from host 127.0.0.1 port ",
                                 CLIENT1 + " registered from host 127.0.0.1 port ",
                                 CLIENT1 + " to " + CLIENT2 + ": " + MESSAGE1,
                                 CLIENT2 + " is not registered with server",
                                 "Sending message to overlay server: " + CLIENT1 + " to " + CLIENT2 + ": " + MESSAGE1,
                                 "Received from overlay server: " + CLIENT2 + " to " + CLIENT1 + ": " + MESSAGE2
                                 ]
TEST5_EXPECTED_SERVER2_OUTPUTS = ["server started on 127.0.0.1 at port " + TEST5_SERVER2_PORT,
                                  "server overlay started at port " + TEST5_SERVER2_OVERLAY_PORT,
                                  "connected to overlay server at 127.0.0.1 port " + TEST5_SERVER1_OVERLAY_PORT,
                                 CLIENT2 + " registered from host 127.0.0.1 port ",
                                 "Received from overlay server: " + CLIENT1 + " to " + CLIENT2 + ": " + MESSAGE1,
                                 CLIENT2 + " to " + CLIENT1 + ": " + MESSAGE2,
                                 CLIENT1 + " is not registered with server",
                                 "Sending message to overlay server: " + CLIENT2 + " to " + CLIENT1 + ": " + MESSAGE2
                                 ]
TEST5_EXPECTED_CLIENT1_OUTPUTS = ["connected to server and registered " + CLIENT1,
                                  CLIENT2 + ": " + MESSAGE2
                                 ]
TEST5_EXPECTED_CLIENT2_OUTPUTS = ["connected to server and registered " + CLIENT2,
                                 CLIENT1 + ": " + MESSAGE1
                                 ]

TEST_COMMANDS = [TEST1_COMMANDS, TEST2_COMMANDS, TEST3_COMMANDS, TEST4_COMMANDS, TEST5_COMMANDS]
TEST_INPUTS = [[TEST1_SERVER_INPUTS, TEST1_CLIENT_INPUTS],
               [TEST2_SERVER_INPUTS, TEST2_CLIENT1_INPUTS, TEST2_CLIENT2_INPUTS],
               [TEST3_SERVER_INPUTS, TEST3_CLIENT1_INPUTS, TEST3_CLIENT2_INPUTS],
               [TEST4_SERVER1_INPUTS,TEST4_SERVER2_INPUTS, TEST4_CLIENT1_INPUTS, TEST4_CLIENT2_INPUTS],
               [TEST5_SERVER1_INPUTS,TEST5_SERVER2_INPUTS, TEST5_CLIENT1_INPUTS, TEST5_CLIENT2_INPUTS]
               ]
EXPECTED_OUTPUTS = [[TEST1_EXPECTED_SERVER_OUTPUTS, TEST1_EXPECTED_CLIENT_OUTPUTS],
                    [TEST2_EXPECTED_SERVER_OUTPUTS, TEST2_EXPECTED_CLIENT1_OUTPUTS, TEST2_EXPECTED_CLIENT2_OUTPUTS],
                    [TEST3_EXPECTED_SERVER_OUTPUTS, TEST3_EXPECTED_CLIENT1_OUTPUTS, TEST3_EXPECTED_CLIENT2_OUTPUTS],
                    [TEST4_EXPECTED_SERVER1_OUTPUTS, TEST4_EXPECTED_SERVER2_OUTPUTS, TEST4_EXPECTED_CLIENT1_OUTPUTS, TEST4_EXPECTED_CLIENT2_OUTPUTS],
                    [TEST5_EXPECTED_SERVER1_OUTPUTS, TEST5_EXPECTED_SERVER2_OUTPUTS, TEST5_EXPECTED_CLIENT1_OUTPUTS, TEST5_EXPECTED_CLIENT2_OUTPUTS]
                    ]


class TimeoutException(Exception):
    def __init__(self):
        super().__init__()

def handler(signum, frame):
    raise TimeoutException()

def run_process(process):
    signal.signal(signal.SIGALRM, handler)
    try:
        signal.alarm(TIME_INTERVAL)  # timeout after TIME_INTERVAL (in seconds)
        process.wait()
    except TimeoutException:
        pass
    finally:
        signal.alarm(0)

def create_processes(commands, processes):
    for cmd in commands:
        process = Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE, shell=True)
        processes.append(process)
        run_process(process)

def run_processes(processes):
    for process in processes:
        run_process(process)

def write_to_console(processes, inputs):
    for i in range(len(processes)):
        for line in inputs[i]:
            line += "\n"
            processes[i].stdin.write(line.encode("utf-8"))
            processes[i].stdin.flush()
        run_process(processes[i])

def check_console_messages(processes, outputs):
    signal.signal(signal.SIGALRM, handler)
    for i in range(len(processes)):
        counter = 0
        try:
            signal.alarm(TIME_INTERVAL)  # timeout after TIME_INTERVAL (in seconds)
            processes[i].stdout.flush()
            for line in processes[i].stdout:
                line = line.decode("utf-8").strip()
                if not (line.isspace() or line == ""):
                    testcase.assertIn(outputs[i][counter], line)
                    counter += 1
        except TimeoutException:
            # make sure that all expected lines are present
            testcase.assertEqual(counter, len(outputs[i]))
            pass
        finally:
            signal.alarm(0)

def kill_processes(processes):
    for process in processes:
        process.kill()

def cleanup():
    create_processes(CLEANUP_COMMANDS, [])

def check_results_and_cleanup(processes, outputs, identifier):
    try:
        check_console_messages(processes, outputs)
        print(identifier + " PASSED. CONGRATS!")
        return 20
    except AssertionError as e:
        errorMsg = str(e)
        if "!=" in errorMsg:
            logging.error(identifier + " FAILED: Missing console statements: " + str(e))
        else:
            logging.error(identifier + " FAILED: " + str(e))
        print(identifier + " FAILED.")
        return 0
    finally:
        kill_processes(processes)
        #cleanup()

def run_tests():
    points = 0
    for i in range(len(TEST_COMMANDS)):
        processes = []
        create_processes(TEST_COMMANDS[i], processes)
        write_to_console(processes, TEST_INPUTS[i])
        run_processes(processes)
        points += check_results_and_cleanup(processes, EXPECTED_OUTPUTS[i], "TEST" + str(i+1))
    return points



if __name__ == "__main__":
    print("Your grade is " + str(run_tests()) + "/100.")
