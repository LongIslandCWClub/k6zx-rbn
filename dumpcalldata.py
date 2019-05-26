#!/usr/bin/env python

# Dump the local store of the rbn.py callsign data from QRZ.com. This is a
# test program.


import os
import shelve



def main():
    shelveFile = os.path.join(os.environ['HOME'],
                              'amateur-radio/rbnData.db')
    calldata = shelve.open(shelveFile)

    for key in calldata:
        record = calldata[key]
        # print(record)

        output = f"{record['call']:6s}   "
        if 'fname' in record:
            output += f"{record['fname']} "
        if 'name' in record:
            output += f"{record['name']}, "
        if 'addr2' in record:
            output += f"{record['addr2']}, "
        if 'state' in record:
            output += f"{record['state']}, "
        if 'country' in record:
            output += f"{record['country']}, "
        if 'grid' in record:
            output += f"{record['grid']}"
            

        print(output)

    calldata.close()
    

if __name__ == "__main__":
    main()

