#!/usr/bin/env python


import colorama
import configargparse
from geopy import distance
from inspect import currentframe, getframeinfo
import logging
import os
import re
import signal
import sqlite3
import sys
import telnetlib

from qrz import *



RBN_HOST = "telnet.reversebeacon.net"
RBN_PORT = 7000

TELNETLIB_DEBUG_LEVEL = 0

telnetInstance = None


lastCall = ""
lastTime = ""


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
    parser.add_argument('-c', '--callsign', action='store', dest='callsign',
                        type=str, help="Specify user's callsign")
    parser.add_argument('-l', '--logging', action='store', dest='logging',
                        type=int, default = 0, help='Enable program logging')
    parser.add_argument('--telnetdebug', action='store', dest='telnetdebug',
                        type=int, default = 0, help='Enable telnetlib debugging')
    parser.add_argument('--de_maid', action='append', dest='deMaid',
                        help='DE Maidenhead squares')
    parser.add_argument('--dx_maid', action='append', dest='dxMaid',
                        help='DX Maidenhead squares')
    parser.add_argument('--de_ituzone', action='append', dest='deITUZone',
                        type=int, help='DE ITU Zone')
    parser.add_argument('--dx_ituzone', action='append', dest='dxITUZone',
                        type=int, help='DX ITU Zone')
    parser.add_argument('--de_cq', action='append', dest='deCQ',
                        help='DE CQ Zone')
    parser.add_argument('--dx_cq', action='append', dest='dxCQ',
                        help='DX CQ Zone')
    parser.add_argument('--min_wpm', action='store', dest='minWPM',
                        type=int, default=0, help='Minimum CW WPM to show')
    parser.add_argument('--max_wpm', action='store', dest='maxWPM',
                        type=int, default=100, help='Maximum CW WPM to show')
    parser.add_argument('-m', '--mode', action='append', dest='mode',
                        help='Select transmission mode')
    parser.add_argument('-f', '--config-file', action='store', dest='configFile',
                        is_config_file=True, help='Config file path')
    parser.add_argument('--licw-file', action='store', dest='licwFile', type=str,
                        default='amateur-radio/clubs/licw.txt',
                        help='LICW Callsign file')
    parser.add_argument('--cwops', action='store', dest='cwops',
                        default='amateur-radio/clubs/cwops.txt',
                        help='CWOps Callsign file')
    parser.add_argument('--skcc-file', action='store', dest='skccFile',
                        default='SKCCLogger/SKCCData_DB.sql',
                        help='SKCCLogger local membership database')
    parser.add_argument('--qrz_username', action='store', dest='qrzUsername',
                        type=str, help='QRZ username')
    parser.add_argument('--qrz_password', action='store', dest='qrzPassword',
                        type=str, help='QRZ password')
    parser.add_argument('--latitude', action='store', dest='latitude',
                        type=float, help='Station latitude')
    parser.add_argument('--longitude', action='store', dest='longitude',
                        type=float, help='Station longitude')
    parser.add_argument('--skcc', action='store_true', dest='skcc',
                        help='Highlight SKCC members')
    parser.add_argument('--licw', action='store_true', dest='licw',
                        help='Highlight LICW members')


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

    if not args.deMaid:
        a['deMaid'] = ['all']
    else:
        a['deMaid'] = args.deMaid
        
    if not args.dxMaid:
        a['dxMaid'] = ['all']
    else:
        a['dxMaid'] = args.dxMaid
        
    if not args.deITUZone:
        a['deITUZone'] = ['all']
    else:
        a['deITUZone'] = args.deITUZone

    if not args.dxITUZone:
        a['dxITUZone'] = ['all']
    else:
        a['dxITUZone'] = args.dxITUZone
        
    if not args.deCQ:
        a['deCQ'] = ['all']
    else:
        a['deCQ'] = args.deCQ
        
    if not args.dxCQ:
        a['dxCQ'] = ['all']
    else:
        a['dxCQ'] = args.dxCQ
        
    a['minWPM'] = args.minWPM
    a['maxWPM'] = args.maxWPM
    
    if not args.mode:
        a['mode'] = ['CW', 'RTTY', 'PSK31', 'PSK63', 'BPSK', 'FT8', 'FT4']
    else:
        a['mode'] = args.mode
        
    a['logging'] = args.logging
    a['telnetdebug'] = args.telnetdebug
    
    if os.path.isabs(args.licwFile):
        a['licwFile'] = args.licwFile
    else:
        a['licwFile'] = os.path.join(os.environ['HOME'], args.licwFile)
        
    if os.path.isabs(args.cwops):
        a['cwops'] = args.cwops
    else:
        a['cwops'] = os.path.join(os.environ['HOME'], args.cwops)

    if os.path.isabs(args.skccFile):
        a['skccFile'] = args.skccFile
    else:
        a['skccFile'] = os.path.join(os.environ['HOME'], args.skccFile)

    if args.callsign:
        a['callsign'] = args.callsign
    else:
        print("ERROR: the user's callsign is not provided, exiting...")
        sys.exit(1)

    if args.qrzUsername:
        a['qrzUsername'] = args.qrzUsername
    else:
        print("ERROR: the user's QRZ callsign is not provided, exiting...")
        sys.exit(1)

    if args.qrzPassword:
        a['qrzPassword'] = args.qrzPassword
    else:
        print("ERROR: the user's QRZ password is not provided, exiting...")
        sys.exit(1)

    a['position'] = []
    if args.latitude:
        a['position'].append(args.latitude)
    else:
        print("ERROR: the station's latitude is not provided, exiting...")
        sys.exit(1)

    if args.longitude:
        a['position'].append(args.longitude)
    else:
        print("ERROR: the station's longitude is not provided, exiting...")
        sys.exit(1)

    if args.skcc:
        a['skcc'] = True
    else:
        a['skcc'] = False

    if args.licw:
        a['licw'] = True
    else:
        a['licw'] = False

    return a


def filterFriend(args, dxCall, licwLst, line):
    result = False

    for call in licwLst:
        rg = re.escape(call) + '\s+de'
        if re.search(rg, line):
            result = True
            break

    return result

        
    

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

    if args['logging'] and result == False:
        logging.info("filterBand(): cfg {args['band']}, {freq}")
        
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

    if args['logging'] and result == False:
        logging.info(f"filterMode(): cfg {args['mode']}, mode {mode}")
        
    return result


def filterWPM(args, wpmStr):
    # print(f"filterWPM() args {args}, wpm: {wpmStr}")

    result = False
    wpm = int(wpmStr)

    if args['minWPM'] <= wpm <= args['maxWPM']:
        result = True
    
    if args['logging'] and result == False:
        logging.info(f"filterWPM(): min {args['minWPM']}, max {args['maxWPM']} "
                     f"WPM {wpm}")
        
    return result


def filterCQZones(args, callData):
    result = False

    if 'cqzone' in callData:
        # print(f"filterCQZones() {args['dxCQ']}")
        # print(f"\tcq zone: {callData['cqzone']}")

        # need to convert from string to int to match zone types in the
        # progArgs dxCQ list
        zone = int(callData['cqzone'])

        if args['logging']:
            logging.info(f"calldata cqzone type {type(callData['cqzone'])}, "
                         f"args dxCQ type {type(args['dxCQ'])}, "
                         f"args elem type {type(args['dxCQ'][0])}")
        
        if zone in args['dxCQ']:
            result = True
        else:
            if args['logging']:
                logging.info(f"filterCQZones(): cfg CQ zone {args['dxCQ']} "
                             f"CQ zone {zone}")
            else:
                pass
    else:
        result = True          # this call doesn't have a CQ Zone so print it
        result = False         # on second thought too many stations w/o zone
        if args['logging']:
            logging.info(f"filterCQZones(): station has no 'cqzone'")
        
    return result


def filterITUZones(args, callData):
    result = False

    result = True   # temporary
    return result


def filterMaidenhead(args, callData):
    result = False

    if 'all' in args['dxMaid']:
        result = True
    elif 'grid' in callData:
        grid = callData['grid'][:2]
        if grid in args['dxMaid']:
            result = True
    else:
        if args['logging']:
            logging.info(f"filterMaidenhead() {callData['call']} has no grid")

    return result


def filter(progArgs, qrz, licwLst, line):
    global lastCall
    global lastTime
    
    lineStr = line.decode('utf-8').rstrip()

    l = lineStr.split()

    if len(l) == 12:
        if progArgs['logging']:
            logging.info("-------------------------------")
            logging.info(f"split: {l}")

        try:
            deCall = l[2].split('-')[0]
            freq = float(l[3])
            dxCall = l[4]
            mode = l[5]
            snr = l[6]
            wpm = l[8]
            xmsn = l[10]
            time = l[(len(l) - 1)]
        except ValueError as e:
            print(f"error {e}")
            print(f"line: {l}")

        if progArgs['logging']:
            logging.info(f"DEBUG: {dxCall} de {deCall}, freq {freq}, {mode}, "
                         f"{snr} dB, {wpm} WPM, {time}Z")

        if qrz.localCallsignDataExists(dxCall):
            # The callsign data exists in the local shelve file, so this
            # station has been heard during this session. This is an
            # optimization to minimize QRZ traffic that has already been
            # retrieved.
            if dxCall == progArgs['callsign']:
                # if the received DX callsign is user's callsign, then get the
                # data for the DE callsign, to get distance from the DE callsign
                # to user's location
                callData = qrz.getLocalCallsignData(deCall)
                callsignFound = True
                if progArgs['logging']:
                    logging.info(f"filter() ")
            else:
                # else, the usual case, get the data for the DX station,
                # to get the distance from the DX station to the user's
                # location
                callData = qrz.getLocalCallsignData(dxCall)
                callsignFound = True
                if progArgs['logging']:
                    logging.info(f"filter() ")
        else:
            # The callsign data isn't in the local shelve file, so must
            # go to QRZ to retrieve that station's information
            try:
                if dxCall == progArgs['callsign']:
                    # user's callsign, get data for DE callsign so
                    # distance is from DE station to user's location
                    callData = qrz.callsignData(deCall, quiet=True)
                    callsignFound = True
                    qrz.setLocalCallsignData(deCall, callData)
                    if progArgs['logging']:
                        logging.info(f"callsignData: {callData}")
                else:
                    # get DX station's data to get distance from DX to
                    # user's location
                    callData = qrz.callsignData(dxCall, quiet=True)
                    callsignFound = True
                    qrz.setLocalCallsignData(dxCall, callData)
                    if progArgs['logging']:
                        logging.info(f"callsignData: {callData}")

                if 'grid' not in callData:
                    logging.info(f"{callData['call']} has no grid in QRZ")
                
            except CallsignNotFound:
                callsignFound = False
            except Exception as e:
                frameinfo = getframeinfo(currentframe())
                print(f"\nfilter() caught exception '{e}' for callsign {dxCall}, "
                      f"{frameinfo.filename}: {frameinfo.lineno}")
                callsignFound = False

        retStr = ""
        printData = False
        if callsignFound:
            # If information about the callsign is found, then do the
            # filtering based on the criteria from the configuration
            # file, and print only those records from RBN that pass
            # those filters.
            if filterFriend(progArgs, dxCall, licwLst, lineStr):
                printData = True
            elif (filterBand(progArgs, freq) and
                  filterMode(progArgs, mode) and
                  filterWPM(progArgs, wpm) and
                  filterMaidenhead(progArgs, callData) and
                  filterITUZones(progArgs, callData)):
                printData = True

            if printData:
                retStr = (f"{dxCall:8s} de {deCall:6s}  {freq:7.1f} MHz  {mode}  "
                          f"{snr:>2s} dB  {wpm:>2s} WPM  {time}")

                if 'lat' in callData and 'lon' in callData:
                    d = distance.distance((callData['lat'], callData['lon']),
                                          progArgs['position']).miles
                    retStr += f"  dist {round(d):5} mi"

                if 'state' in callData:
                    retStr += f"  {callData['state']}"
                elif 'country' in callData:
                    retStr += f"  {callData['country']}"

                if (lastCall == dxCall) and (lastTime == time):
                    retStr = '*'

                lastCall = dxCall
                lastTime = time

                if progArgs['logging']:
                    logging.info(f"call {dxCall} - {lastCall} "
                                 f"time {time} - {lastTime}")
                
        return retStr


def getCallsigns(file):
    callsigns = []
    with open(file) as f:
        while True:
            line = f.readline()
            if not line:
                # EOF
                break
            elif line.startswith('#'):
                # if line is a comment, skip
                continue
            elif not line.strip():
                continue
            else:
                callsigns.append(line.strip())

    return callsigns


def getSQLCallsigns(db):
    conn = sqlite3.connect(db)
    c = conn.cursor()

    lst = []
    for row in c.execute('SELECT Mbr_Call from SKCCData_DB'):
        lst.append(row[0])

    return lst
    
    

def rbnLogin(tn, args):
    tn.open(RBN_HOST, RBN_PORT, 10)
    
    tn.read_until(b"Please enter your call: ")
    loginStr = (args['callsign'] + "\n").encode('ascii')
    tn.write(loginStr)

    tn.read_until(b"Local users", timeout=20)
    print("Connection established...")

    while True:
        s = tn.read_until(b"\r\n")

        if re.match(rf"^{args['callsign']}", s.decode('utf-8')):
            print("Receiving RBN Data...")
            break;
    

def rbnProcess(tn, args, licwCallLst, skccCallLst):
    dots = 0
    columns, rows = os.get_terminal_size(0)
    columns -= 10

    qrz = QRZ(args['qrzUsername'], args['qrzPassword'], args['logging'])
    
    while True:
        rawline = tn.read_until(b"\r\n")
        line = filter(args, qrz, licwCallLst, rawline)
        if line == '*' or line == "":
            if dots >= columns:
                # goto to beginning of line and clear the line
                print("", end="\r")            # carriage return
                sys.stdout.write("\033[K")     # clear to eol
                dots = 0
            else:
                if line == "*":
                    ch = "*"
                else:
                    ch = "."
                    
                print(ch, end="", flush=True)
                dots += 1
        elif line:
            if dots > 0:
                # goto to beginning of line and clear the line
                print("", end="\r")            # carriage return
                sys.stdout.write("\033[K")     # clear to eol
                dots = 0

            meFound = False
            if re.match(args['callsign'], line):
                meFound = True

            # Highlight LICW members only if that option is enabled
            friendFound = False
            if args['licw']:
                if not meFound:
                    for call in licwCallLst:
                        rg = re.escape(call) + '\s+de'
                        # print(f"{rg} --- {line}")
                        if re.search(rg, line):
                            friendFound = True
                            # print(f"\n\nfound callsign: {call}")
                            break

            # Highlight SKCC members only if enabled
            skccFound = False
            if args['skcc']:
                if (not friendFound) or (not meFound):
                    for call in skccCallLst:
                        # rg = re.escape(call)
                        rg = re.escape(call) + '\s+de'
                        if re.search(rg, line):
                            skccFound = True
                            break

            if meFound:
                print(colorama.Back.YELLOW + line)
            elif friendFound:
                print(colorama.Back.GREEN + line)
            elif skccFound:
                print(colorama.Back.CYAN + line)
            else:
                print(line)


def main():
    global telnetInstance

    args = parseArguments()

    progArgs = processArgs(args)

    # DEBUG
    print(progArgs)
    
    if progArgs['logging']:
        logging.basicConfig(filename='rbn.log', filemode='w',
                            level=logging.INFO)

    licwCallsigns = getCallsigns(progArgs['licwFile'])
    cwopsCallsigns = getCallsigns(progArgs['cwops'])
    licwCallsigns = licwCallsigns + cwopsCallsigns

    skccCallsigns = getSQLCallsigns(progArgs['skccFile'])
    

    colorama.init(autoreset=True)

    # DEBUG
    # print(colorama.Back.BLUE + 'testing...')
    # print(colorama.Back.RED + 'testing...')
    # print(colorama.Back.GREEN + 'testing...')
    # print(colorama.Back.YELLOW + 'testing...')
    # print(colorama.Back.CYAN + 'testing...')
    # print(colorama.Back.MAGENTA + 'testing...')
    # sys.exit(0)
    
    while True:
        try:
            tn = telnetlib.Telnet()
            telnetInstance = tn
            
            tn.set_debuglevel(progArgs['telnetdebug'])
            print(f"Connecting...")
            tn.open(RBN_HOST, RBN_PORT, 10)

            rbnLogin(tn, progArgs)

            rbnProcess(tn, progArgs, licwCallsigns, skccCallsigns)
            
        except EOFError as e:
            print(colorama.Fore.RED + f"Connection failed: {e}" +
                  colorama.Style.RESET_ALL)
            print("Retrying...")
        finally:
            tn.close()



if __name__ == "__main__":
    main()
