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
# Normal invocation of this build script is:
#   $ ./build.py -o ../rbnapp build ./rbn.py
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

    # Positional arguments
    parser.add_argument('appdir', action='store', type=str,
                        help='Directory where compiled executable is stored')

    parser.add_argument('command', action='store', type=str,
                        help='Command to run (build, clean)')

    parser.add_argument('script', action='store', type=str,
                        help='Python script for which application is built')

    # Optional arguments
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

    a['appdir'] = os.path.abspath(args['appdir'])
    a['builddir'] = os.path.join(a['appdir'], 'build')

    a['onefile'] = args['onefile']

    return a


def removeDir(dirPath):
    try:
        shutil.rmtree(dirPath)
    except OSError as e:
        print(f"ERROR: {dirPath}, {e.strerror}")
            

def buildUnix(args, osType):
    if os.path.exists(args['builddir']):
        removeDir(args['builddir'])

    cmd = "pyinstaller"
    if args['onefile']:
        cmd += ' --onefile'

    # Add default rbn.cfg file to bundle. This adds the default config
    # file to the pyinstaller bundle. When the executable file is
    # executed, a temporary directory is created and any files that
    # are added using the pyinstaller '--add-data' directive, will be
    # extracted into the subdirectory specified. This must be
    # coordinated in the application so it can access these files.
    cmd += ' --add-data rbn.cfg:data'

    pyDistPath = os.path.join(f"{args['builddir']}", 'dist')
    pyWorkPath = os.path.join(f"{args['builddir']}", 'build')
    
    cmd += f" --distpath {pyDistPath}"
    cmd += f" --workpath {pyWorkPath}"
    
    cmd += f" {args['script']}"

    os.system(cmd)

    appName = os.path.splitext(os.path.basename(args['script']))[0]
    appPath = os.path.join(args['appdir'], "build", "dist", appName)
    destDir = os.path.join(args['appdir'], osType)
    destPath = os.path.join(destDir, appName)

    if not os.path.exists(destDir):
        os.mkdir(destDir)

    cmd = f"cp -p {appPath} {destDir}"
    os.system(cmd)
                 
    print(f"The resulting executable is located in: {destPath}")
    

def main():
    args = parseArguments()
    # print(f"DEBUG: args: {args}")

    progArgs = processArgs(args)
    # print(f"DEBUG: progArgs: {progArgs}")

    opSys = platform.system()
    # print(f"DEBUG: OS: {platform.system()}")

    if progArgs['command'] == 'build':
        if opSys == 'Linux':
            buildUnix(progArgs, 'linux')
        elif opSys == 'Darwin':
            buildUnix(progArgs, 'macos')
        elif opSys == 'Windows':
            buildWindows(progArgs)
        else:
            print(f"ERROR: requested build for unknown OS: {opSys}")
    elif progArgs['command'] == 'clean':
        print(f"Cleaning {progArgs['script']} application build...")
        removeDir(progArgs['builddir'])

        fileLst = glob.glob(f"{os.path.abspath('.')}/*.spec")
        for f in fileLst:
            try:
                os.remove(f)
            except:
                print(f"ERROR removing file: {f}")



if __name__ == "__main__":
    main()
