#!/usr/bin/env python


import telnetlib



HOST = "telnet.reversebeacon.net"
PORT = 7000
CALLSIGN = "K6ZX"

DEBUG_LEVEL = 0
# DEBUG_LEVEL = 1


def main():
    tn = telnetlib.Telnet(HOST, PORT)

    tn.set_debuglevel(DEBUG_LEVEL)

    tn.read_until(b"Please enter your call: ")
    loginStr = (CALLSIGN + "\n").encode('ascii')
    # tn.write(f"{CALLSIGN.encode('ascii')}" + "\n")
    tn.write(loginStr)
    
    while True:
        line = tn.read_until(b"\r\n")
        print(line.decode('utf-8').rstrip())


if __name__ == "__main__":
    main()
