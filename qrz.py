

# qrz.py - Functions to query the QRZ.com database


from inspect import currentframe, getframeinfo
import logging
import os
import re
import requests
import shelve
import xmltodict




class QRZerror(Exception):
    pass


class CallsignNotFound(Exception):
    pass



class QRZ:

    QRZ_BASE_URL = 'http://xmldata.qrz.com/xml/current/'
    

    def __init__(self, username, password, logging):
        self._session = None
        self._session_key = None

        self.username = username
        self.password = password
        self.logging = logging

        # open shelve file with QRZ callsign info storage
        self.QRZ_SHELVE_FILE = os.path.join(os.environ['HOME'],
                                            'amateur-radio/rbnData.db')
        self.qrzLocalData = shelve.open(self.QRZ_SHELVE_FILE, flag='n')


    # Class destructor, need to close and remove the shelve file
    def __del__(self):
        self.qrzLocalData.close()

        


    def _get_session(self):
        url = self.QRZ_BASE_URL + '?username={}&password={}'.\
                                   format(self.username, self.password)
        self._session = requests.Session()
        self._session.verify = False
        r = self._session.get(url)

        if r.status_code == 200:
            raw_session = xmltodict.parse(r.content)
            self._session_key = raw_session['QRZDatabase']['Session']['Key']
            if self._session_key:
                return True
        raise Exception('could not get QRZ session')


    def getQRZCallsignData(self, callsign, retry=True, quiet=False):
        if self._session_key is None:
            self._get_session()

        # search for '/' in callsigns and effectively remove it from
        # the callsign submitted to qrz.com
        match = re.search(r'([0-9a-zA-Z]+)/*', callsign)
        if match:
            callsign = match.group(1)
            
        # print(f'callsignData: call: {callsign}')

        url = self.QRZ_BASE_URL + '?s={}&callsign={}'.format(self._session_key,
                                                             callsign)
        r = self._session.get(url)

        if r.status_code != 200:
            raise Exception("Error Querying: Response code {}".\
                            format(r.status_code))

        raw = xmltodict.parse(r.content).get('QRZDatabase')
        if not raw:
            raise QRZerror('Unexpected API Result')

        if raw['Session'].get('Error'):
            errormsg = raw['Session'].get('Error')
            if 'Session Timeout' in errormsg or 'Invalid session key' in errormsg:
                if retry:
                    self._session_key = None
                    self._session = None

                    return self.callsign(callsign, retry=False)
                else:
                    pass
            elif "not found" in errormsg.lower():
                raise CallsignNotFound(errormsg)

            raise QRZerror(raw['Session'].get('Error'))

        else:
            callData = raw.get('Callsign')
            if callData:
                if not quiet:
                    print(f"Rcvd QRZ data for: {callsign}")
                return callData

        raise Exception("Unhandled Error during Query")


    def localCallsignDataExists(self, callsign):
        result = False
        
        if callsign in self.qrzLocalData:
            result = True

        return result
    
            
            
    def getLocalCallsignData(self, callsign):
        if self.logging:
            # logging.info(f"getLocalCallsignData() {self.qrzLocalData[callsign]}")
            logging.info(f"getLocalCallsignData() get call {callsign}")
        return self.qrzLocalData[callsign]


    def getCallsignData(self, callsign, args):
        if self.localCallsignDataExists(callsign):
            # callsign data has already been retrieved from qrz.com
            # and is in the local shelve file
            callData = self.getLocalCallsignData(callsign)
        else:
            # callsign data hasn't been retrieved from qrz.com so get it
            try:
                callData = self.getQRZCallsignData(callsign, quiet=True)
                self.setLocalCallsignData(callsign, callData)
            except Exception as e:
                # frameinfo = getframeinfo(currentframe())
                # print(f"\nfilter() caught exception '{e}' for callsign {callsign}, "
                #       f"{frameinfo.filename}: {frameinfo.lineno}")
                return None
                
        # if args['logging']:
        #     logging.info(f"callsignData: {callData}")

        return callData
                


    def setLocalCallsignData(self, callsign, data):
        if self.logging:
            # logging.info(f"setLocalCallsignData() {data}")
            logging.info(f"setLocalCallsignData() set data for {callsign}")
        # print(f"setLocalCallsignData() set data {callsign}: {data}")
        self.qrzLocalData[callsign] = data
        

    def getLocalCallsignDataKeys(self):
        return list(self.qrzLocalData.keys())
