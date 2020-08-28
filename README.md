# Enhanced Reverse Beacon Network: rbn

The **rbn** package provides an enhanced Reverse Beacon Network (RBN)
client that adds some useful features to the standard RBN
functionality. 

This repository is the source code respository. The *compiled*
application is contained in the **k6zx-rbnapp* repository. 


## Table of Contents

* [General Info](#general_info)
* [Installation](#installation)
* [Invocation](#invocation)

<a name="general_info"></a>
## General Info

The RBN is a network of receiving stations listening to the amateur
bands and reporting what stations they hear transmitting. This
information is transmitted from the listening stations to a server
from which amateur radio operators can access these spot reports to
see who is operating on which frequencies, which operating modes, CW
speed, and the received signal strength from those stations at the
receiving stations. This allows one to see who is receiving your
transmissions and how well you are being heard. It also can show who
in your geographical area is being heard and by whom. 

The RBN has a web interface that one uses a browser to access and it
also has a telnet interface that allows for maximum throughput of the
spot data. RBN has two telnet access ports, one for CW, RTTY, and PSK
spots and another dedicated to FT8. It is the CW telnet interface that
the **rbn** package uses and then filtering of the spots is performed
as specified by the user's configuration. Access to FT8 spots is not
implemented. 

The **rbn** package allows one to connect to the RBN telnet stream and
filter the spots in many ways under the control of the user. Spots
that pass the filters and are displayed can be color-coded if the
station spotted is a member of a club (LICW and SKCC are currently
implemented). There is also a distance value that shows the location
of spotted station and the distance from that station to the user's
location. This is the added functionality provided by the **rbn**
package over and above what is available from RBN. 

This repository contains the source code of the **rbn** package. It
has been tested on the following operating systems[^1]:

- Linux

[^1]: Testing on MacOS and Windows 10 is planned for the future.


<a name="installation"></a>
## Installation

The **rbn** package is implemented in Python and requires python 3. It
can be executed from source code in the manner of any python script
but the easiest method of deployment and execution is to use the
**rbnapp** package that is single file executable for all supported
operating systems. **rbnapp** is packaged separately and should be
accessed from that repository. 

For those knowledgeable/interested users, **rbn** may be executed from
source as follows. It is developed/tested on a Linux OS using the
Python Version Management Tool,
[pyenv](https://github.com/pyenv/pyenv), and creating a python
[virtual environment](https://docs.python.org/3/library/venv.html)
(i.e. python -m venv venv). The python interpreter and required python
modules are installed in the local virtual environment. In this way
the entire required python support system is available locally. The
required python modules are identified in the file 'requirements.txt'
and are installed in the local virtual environment using *pip install
-r requirements.txt*. 

It would also be possible to use the python interpreter and required
packages installed on the system. This must be a python 3 version,
python 2 is not supported. The additional python packages will need to
be installed also using the package management system of the OS in
question. 

HERE HERE

**cwwords** can perform initialization of its data files and
configuration files. This is done with the following invocation: 

  $ cwwords.py --init <config_dir>
  
  where <config_dir> is a directory in which the program's
  configuration files are stored. 
  
There are several default configuration files that are written to this
directory that contain the configuration parameters for each of the
modes of operation of **cwwords**. 


<a name="invocation"></a>
## Invocation

The **cwwords** package 

