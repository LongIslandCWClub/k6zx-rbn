#!/usr/bin/env python

# This is a script to automate the building of an executable from the
# python program in this directory. It uses the 'pyinstaller' package
# for this purpose. One of the prerequisites of using pyinstaller is
# that the python interpreter must be built with the '--enable-shared'
# switch. In a python development environment using 'pyenv' and
# 'venv', the python interpreter must be built as follows:
#
# $ env PYTHON_CONFIGURE_OPTS="--enable-shared" pyenv install 3.8.5
#


import configargparse
import glob
import os
import platform
import PyInstaller.__main__
import shutil
import sys



def parseArguments():
    p = ("Script to build a python program into a 'deployable' state. "
         "The python package 'pyinstaller' is used to create a single "
         "bundled application including the python interpreter and all "
         "the packages required. This greatly simplifies deployment "
         "of the application and its use by others.")

    parser = configargparse.ArgumentParser(description='Build python executable.',
                                           epilog=p)

    parser.add_argument('--distpath', '-d', action='store', dest='distpath',
                        type=str, help='Path to bundled application')
    parser.add_argument('--workpath', '-w', action='store', dest='workpath',
                        type=str, help='Path to temporary work files')

    parser.add_argument('command', action='store',
                        type=str, help='Command to run (build, clean)')

    parser.add_argument('script', action='store',
                        type=str,
                        help='Python script for which application is built')

    parser.add_argument('--onefile', '-o', action='store_true', dest='onefile',
                        help='Build application in one, bundled file')

    args = parser.parse_args()

    return vars(args)


def processArgs(args):
    a = {}
    
    if args['command'] == 'build' or args['command'] == 'clean':
        a['command'] = args['command']
    else:
        print(f"ERROR unknown command provided: {args['command']}, "
              "exiting...")
        sys.exit(1)

    a['script'] = os.path.abspath(args['script'])

    if args['distpath']:
        a['distpath'] = os.path.abspath(args['distpath'])
    else:
        a['distpath'] = args['distpath']

    if args['workpath']:
        a['workpath'] = os.path.abspath(args['workpath'])
    else:
        a['workpath'] = args['workpath']

    a['onefile'] = args['onefile']

    return a


def removeDir(dirPath):
    try:
        shutil.rmtree(dirPath)
    except OSError as e:
        print(f"ERROR: {dirPath}, {e.strerror}")
            

def buildLinux(args):
    if os.path.exists(args['workpath']):
        removeDir(args['workpath'])

    if os.path.exists(args['distpath']):
        removeDir(args['distpath'])
    
    cmd = "pyinstaller"
    if args['onefile']:
        cmd += ' --onefile'

    if args['workpath']:
        p = os.path.join(f"{args['workpath']}", 'linux')
        cmd += f" --workpath {p}"

    if args['distpath']:
        p = os.path.join(f"{args['distpath']}", 'linux')
        cmd += f" --distpath {p}"

    cmd += f" {args['script']}"
    # print(f"buildLinux() cmd: {cmd}")
    
    os.system(cmd)

    print(f"The resulting executable is located in: {p}")
    

def main():
    args = parseArguments()
    # print(f"DEBUG: args: {args}")

    progArgs = processArgs(args)
    # print(f"DEBUG: progArgs: {progArgs}")

    opSys = platform.system()
    # print(f"DEBUG: OS: {platform.system()}")

    if progArgs['command'] == 'build':
        if opSys == 'Linux':
            buildLinux(progArgs)
        elif opSys == 'Windows':
            buildWindows(progArgs)
        elif opSys == 'MacOS':
            buildMacOS(progArgs)
        else:
            print(f"ERROR: requested build for unknown OS: {opSys}")
    elif progArgs['command'] == 'clean':
        print(f"Cleaning {progArgs['script']} application build...")
        if not progArgs['distpath']:
            progArgs['distpath'] = os.path.abspath("./dist")
        if not progArgs['workpath']:
            progArgs['workpath'] = os.path.abspath("./build")

        removeDir(progArgs['distpath'])
        removeDir(progArgs['workpath'])

        fileLst = glob.glob(f"{os.path.abspath('.')}/*.spec")
        for f in fileLst:
            try:
                os.remove(f)
            except:
                print(f"ERROR removing file: {f}")



if __name__ == "__main__":
    main()
