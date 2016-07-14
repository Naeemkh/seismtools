#!/usr/bin/env python
"""
# ==========================================================================
# The program is to get filename/directory in various ways, and then processes
# found V1/V2 files --> generate column acceleration .txt files and .her files.
# ==========================================================================
"""
from __future__ import print_function
import sys
import os
from smc import set_destination, load_smc_v1, load_smc_v2, \
                print_smc, print_her, print_bbp
from seism import seism_station

destination = ''

def get_parameters():
    """
    This function gets the list of files to process and creates a list.
    Additionally, it asks the user to enter a destination directory where
    output files will be written.
    """
    file_list = []
    output_format = ''
    global destination

    # Check if user provided any parameters
    if len(sys.argv) >= 2:
        output_format = sys.argv[1]
    if len(sys.argv) >= 3:
        destination = sys.argv[2]
    if len(sys.argv) >= 4:
        file_list = sys.argv[3:]

    # Get the output format the user wants
    while output_format != 'bbp' and output_format != 'her':
        output_format = raw_input('== Enter output format (bbp/her): ')
        output_format = output_format.lower()

    while not file_list:
        # ask user if filename is not provided in command-line
        file_list = raw_input('== Enter the file / directory name: ')
        file_list = file_list.split()

    while not destination:
        destination = raw_input('== Enter name of the directory to store outputs: ')
    # check existence of target directory
    if not os.path.exists(destination):
        os.makedirs(destination)
    else:
        # clear content of unprocessed and warning files if they exist
        if os.path.exists(os.path.join(destination, 'unprocessed.txt')):
            clear(os.path.join(destination, 'unprocessed.txt'))
        if os.path.exists(os.path.join(destination, 'warning.txt')):
            clear(os.path.join(destination, 'warning.txt'))

    # Set destination in smc module
    set_destination(destination)

    # All done!
    return file_list, output_format
# end of get_filename

def read_list(file_list, output_format):
    """
    The function is to read a list of files/directory and check their
    types to call corresponding functions.
    """

    for f in file_list:
        # if is a directory; read all files\directories in the directory
        # and append them to file_list
        if os.path.isdir(f):
            for fp in os.listdir(f):
                filename = os.path.join(f, fp)
                if not filename in file_list:
                    file_list.append(filename)

        # if is an non-empty file
        elif os.path.isfile(f) and os.stat(f).st_size != 0:
            # if the file is V1/raw data file: generate text file
            # for acceleration, and .her file
            if f.upper().endswith(".V1") or f.upper().endswith(".RAW"):
                processed = False
                station = load_smc_v1(f)

                # if encounters errors with records in station
                if (not station) or (not station.list):
                    station = False
                else:
                    processed = station.process_v1()

                if not processed:
                    print_message(f, 'unprocessed')
                else:
                    print_smc(station)
                    print_her(station)
                    check_station(station)

            # if the file is V2/processed data file; generate text file
            # for acceleration, and .her file
            elif f.upper().endswith(".V2"):
                processed = False
                station = load_smc_v2(f)

                if station:
                    processed = station.process_v2() #rotate

                if not processed:
                    print_message(f, 'unprocessed')
                else:
                    print_smc(station)
                    if output_format == 'her':
                        print_her(station)
                    elif output_format == 'bbp':
                        print_bbp(station)
                    else:
                        print("Error: Unknown output format %s!" %
                              (output_format))
                    check_station(station)

            else:
                try:
                    fp = open(f)
                except IOError as e:
                    print(e)
                    pass
                lines = fp.read().split()
                if not '#filelist' in lines[0]:
                    print("[ERROR]: unable to recognize file type: %s" % (f))
                else:
                    for l in lines[1:]:
                        if not l in file_list:
                            file_list.append(l)
                        # file_list += lines[1:]
        else:
            print("[ERROR]: no such file or directory: %s" % (f))
# end of read_list

def print_message(message, ftype):
    """
    The function is to generate a files containing warning/unprocessed
    messages for input files.
    """
    f = open(os.path.join(destination, '%s.txt' % (ftype)), 'a')
    f.write(message + "\n")
    f.close()
# end of print_message

def check_station(station):
    """
    The function is to check the station name of each record,
    if it's in the location should be discarded, print warning.
    """
    # check instance
    if not isinstance(station, seism_station):
        return
    if not station.list:
        return

    discard = {'dam': 'Dam', 'Fire Sta': 'Fire Station',
               'Acosta Res': 'Acosta Res', 'Bldg': 'Building',
               'Br': 'Interchange Bridge'}
    name = station.name
    for key in discard:
        if key in name:
            filename = station.network + station.id + '.' + station.type
            msg = filename + " was processed, but it's from " + discard[key]
            print_message(msg, 'warning')
            break
# end of check_station

def clear(filename):
    """
    This function clears the content of a file if it exists.
    """
    try:
        open(filename, 'w').close()
    except IOError as e:
        pass
# end of clear

# Main function
FILE_LIST, OUTPUT_FORMAT = get_parameters()
read_list(FILE_LIST, OUTPUT_FORMAT)
