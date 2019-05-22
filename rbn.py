#!/usr/bin/env python


import configargparse
import os
import re
import signal
import sys
import telnetlib

from qrz import *



RBN_HOST = "telnet.reversebeacon.net"
RBN_PORT = 7000
MY_CALLSIGN = "K6ZX"

TELNETLIB_DEBUG_LEVEL = 0

QRZ_USERNAME   = 'K6ZX'
QRZ_PASSWORD   = 'Sean!12233'


telnetInstance = None


def signalHandler(signum, frame):
    global telnetInstance
    
    print(f"\nTerminating connection to: {RBN_HOST}\n")
    telnetInstance.close()
    sys.exit(0)


signal.signal(signal.SIGINT, signalHandler)



def parseArguments():
    p = ("Telnet to Reverse Beacon Network (RBN) server and capture CW spots. "
         "This program provides better (IMHO) filtering of these spots. Provide "
         "the filtering parameters as command line arguments or in a config "
         "file. "
         )

    parser = configargparse.ArgumentParser(description='RBN spot filter program.',
                                           epilog=p)

    parser.add_argument('-b', '--band', action='append', dest='band',
                        help='Display stations only on these bands')
    parser.add_argument('-d', '--debug', action='store', dest='debug',
                        type=int, default = 0, help='DE ITU Zone')
    parser.add_argument('--de_itu', action='store', dest='deITU',
                        type=int, help='DE ITU Zone')
    parser.add_argument('--dx_itu', action='store', dest='dxITU',
                        type=int, help='DX ITU Zone')
    parser.add_argument('--de_cq', action='append', dest='deCQ',
                        type=int, help='DE CQ Zone')
    parser.add_argument('--dx_cq', action='append', dest='dxCQ',
                        type=int, help='DX CQ Zone')
    parser.add_argument('--min_wpm', action='store', dest='minWPM',
                        type=int, default=0, help='Minimum CW WPM to show')
    parser.add_argument('--max_wpm', action='store', dest='maxWPM',
                        type=int, default=100, help='Maximum CW WPM to show')
    parser.add_argument('-m', '--mode', action='append', dest='mode',
                        help='Select transmission mode')
    parser.add_argument('-f', '--config-file', action='store', dest='configFile',
                        is_config_file=True, help='Config file path')

    args = parser.parse_args()

    # print("-------------------------------------------------------------------")
    # print(parser.format_help())
    print("-------------------------------------------------------------------")
    print(parser.format_values())
    print("-------------------------------------------------------------------")

    return args


def processArgs(args):
    a = {}

    # if no bands are configured then want to return all bands
    if not args.band:
        a['band'] = ['160m', '80m', '40m', '20m', '17m', '15m', '12m', '10m',
                     '6m']
    else:
        a['band'] = args.band
    a['deITU'] = args.deITU
    a['dxITU'] = args.dxITU
    if not args.deCQ:
        a['deCQ'] = [*range(1, 41, 1)]
    else:
        a['deCQ'] = args.deCQ
    if not args.dxCQ:
        a['dxCQ'] = [*range(1, 41, 1)]
    else:
        a['dxCQ'] = args.dxCQ
    a['minWPM'] = args.minWPM
    a['maxWPM'] = args.maxWPM
    if not args.mode:
        a['mode'] = ['CW', 'RTTY', 'PSK31', 'PSK63', 'BPSK', 'FT8', 'FT4']
    else:
        a['mode'] = args.mode
    a['debug'] = args.debug
    
    return a


# Check if freq of spot lines within a band specified 
def filterBand(args, freq):
    # print(f"filterBand() args: {args}, freq {freq}")

    band = args['band']

    result = False

    if '160m' in band:
        if 1800 <= freq <= 2000:
            result = True
    if '80m' in band:
        if 3500 <= freq <= 4000:
            result = True
    if '40m' in band:
        if 7000 <= freq <= 7300:
            result = True
    if '30m' in band:
        if 10100 <= freq <= 10150:
            result = True
    if '20m' in band:
        if 14000 <= freq <= 14350:
            result = True
    if '17m' in band:
        if 18068 <= freq <= 18168:
            result = True
    if '15m' in band:
        if 21000 <= freq <= 21450:
            result = True
    if '12m' in band:
        if 24890 <= freq <= 24990:
            result = True
    if '10m' in band:
        if 28000 <= freq <= 29700:
            result = True
    if '6m' in band:
        if 50000 <= freq <= 54000:
            result = True

    return result


def filterMode(args, mode):
    # print(f"filterMode() args: {args}, mode: {mode}")

    xmtMode = args['mode']
    
    result = False

    if 'CW' in mode:
        result = True
    if 'RTTY' in mode:
        result = True
    if 'PSK31' in mode:
        result = True
    if 'PSK63' in mode:
        result = True
    if 'BPSK' in mode:
        result = True
    if 'FT8' in mode:
        result = True
    if 'FT4' in mode:
        result = True
        
    return result


def filterWPM(args, wpmStr):
    # print(f"filterWPM() args {args}, wpm: {wpmStr}")

    result = False
    wpm = int(wpmStr)

    if args['minWPM'] <= wpm <= args['maxWPM']:
        result = True
    
    return result


def filterCQZones(args, callData):
    result = False

    if 'cqzone' in callData:
        # print(f"filterCQZones() {args['dxCQ']}")
        # print(f"\tcq zone: {callData['cqzone']}")

        if callData['cqzone'] in args['dxCQ']:
            result = True

    return result



def filter(progArgs, qrz, line):
    lineStr = line.decode('utf-8').rstrip()

    l = lineStr.split()

    if len(l) > 7:
        # print("-------------------------------")
        # print(f"split: {l}")

        deCall = l[2].split('-')[0]
        freq = float(l[3])
        dxCall = l[4]
        mode = l[5]
        snr = l[6]
        wpm = l[8]
        xmsn = l[10]
        # time = l[11]
        time = l[(len(l) - 1)]

        # print(f"DEBUG: {dxCall} de {deCall}, freq {freq}, {mode}, {snr} dB, "
        #       f"{wpm} WPM, {time}Z")

        try:
            dxCallData = qrz.callsignData(dxCall, quiet=True)
            callsignFound = True
            # print(f"\tDEBUG: call data: {dxCallData}")
        except CallsignNotFound:
            callsignFound = False
        except Exception as e:
            print(f"filter() caught exception '{e}' for callsign {dxCall}")
            callsignFound = False

        if (callsignFound and
            filterBand(progArgs, freq) and
            filterMode(progArgs, mode) and
            filterWPM(progArgs, wpm) and
            filterCQZones(progArgs, dxCallData)
            ):
            retStr = (f"{dxCall:6s} de {deCall:6s}  {freq:7.1f} MHz  {mode}  "
                      f"{snr:>2s} dB  {wpm:>2s} WPM  {time}")
        else:
            retStr = ""

        return retStr

    

def filter1(progArgs, qrz, line):
    lineStr = line.decode('utf-8').rstrip()

    # patternStr = (f"DX\s+de\s+([a-zA-Z0-9]+)-#:\s+([0-9.]+)\s+"
    #               "([a-zA-Z0-9/]+)\s+([a-zA-Z]+)\s+([0-9]+)\s+dB\s+"
    #               "([0-9]+)\s+WPM|BPS\s+[a-zA-Z0-9\s]+\s+([0-9]+)Z")
    # pattern = re.compile(patternStr)
    pattern = re.compile(r"""
    DX\s+de\s+
    ([a-zA-Z0-9/\-\/]+)-\#:\s+                 # receiving (de) station
    ([0-9.]+)\s+                               # frequency
    ([a-zA-Z0-9\-\/]+)\s+                      # xmit (dx) station
    ([a-zA-Z0-9]+)\s+                          # mode
    ([-+]?[0-9]+)\s+dB\s+                      # SNR
    ([0-9]+)\s+WPM|BPS\s+                      # words/min or bits/sec
    [a-zA-Z0-9]+\s+                            # type of 'message' received
    ([0-9]+)Z                                  # time
    """, re.VERBOSE)
    
    match = pattern.match(lineStr)

    l = lineStr.split()
    print(f"split: {l}")
    
    if match:
        print("-------------------------------")
        # print(f"\tline:  {lineStr}")

        deCall = match.group(1)
        freq = float(match.group(2))
        dxCall = match.group(3)
        mode = match.group(4)
        snr = match.group(5)
        wpm = match.group(6)
        gmt = match.group(7)

        # print(f"match: {match.group(0)}")
        
        # print(f"\tDEBUG: {dxCall} de {deCall}, freq {freq}, {mode}, {snr} dB, "
        #       f"{wpm} WPM, {gmt}Z")

        try:
            dxCallData = qrz.callsignData(dxCall, quiet=True)
            callsignFound = True
            # print(f"\tDEBUG: call data: {dxCallData}")
        except CallsignNotFound:
            callsignFound = False
        except Exception as e:
            print(f"filter() caught exception '{e}' for callsign {dxCall}")
            callsignFound = False

        if (callsignFound and
            filterBand(progArgs, freq) and
            filterMode(progArgs, mode) and
            filterWPM(progArgs, wpm) and
            filterCQZones(progArgs, dxCallData)):
            retStr = (f"{dxCall:6s} de {deCall:6s}  {freq:7.1f} MHz  {mode}  "
                      f"{snr:>2s} dB  {wpm:>2s} WPM  {gmt}Z")
        else:
            retStr = ""
            print(f"line:  {lineStr}")
            print(f"match: {match.group(0)}")
    else:
        retStr = lineStr
        
    return retStr


# def spinningCursor():
#     while True:
#         for cursor in '|/-\\':
#             yield cursor

    

def main():
    global telnetInstance

    args = parseArguments()

    progArgs = processArgs(args)
    print(f"DEBUG - progArgs: {progArgs}")

    tn = telnetlib.Telnet(RBN_HOST, RBN_PORT)
    telnetInstance = tn

    tn.set_debuglevel(progArgs['debug'])

    tn.read_until(b"Please enter your call: ")
    loginStr = (MY_CALLSIGN + "\n").encode('ascii')
    tn.write(loginStr)

    qrz = QRZ(QRZ_USERNAME, QRZ_PASSWORD)
    
    dots = 0
    columns, rows = os.get_terminal_size(0)
    columns -= 10
    while True:
        rawline = tn.read_until(b"\r\n")
        line = filter(progArgs, qrz, rawline)
        if line:
            if dots > 0:
                # goto to beginning of line and clear the line
                print("", end="\r")            # carriage return
                sys.stdout.write("\033[K")     # clear to eol
                dots = 0
                
            print(line)
        else:
            if dots >= columns:
                # goto to beginning of line and clear the line
                print("", end="\r")            # carriage return
                sys.stdout.write("\033[K")     # clear to eol
                dots = 0
            else:
                print(".", end="", flush=True)
                dots += 1




if __name__ == "__main__":
    main()
