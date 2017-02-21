#!/usr/bin/python
###############################################################################
# Copyright 2017 R.A. Winters <rwin336@gmail.com>
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
###############################################################################

# A simple script to 'carve' out a piece of a log from timestamp to timestamp
#
# I had to do this since the Rally status tool would not accpet large log files
# which are reguraly produced by OpenStack processes.
#

import getopt
import io
import sys
import re

from datetime import datetime

version = '1.0'
output_filename = "partial.log"

print('ARGV             : {0}'.format(sys.argv[1:]))

options, remainder = getopt.getopt(sys.argv[1:], 'l:s:e:o', ['log=',
                                                             'output=',
                                                             'start=',
                                                             'end='])

print('OPTIONS          : {0}'.format(options))


# Carve a piece of the log between 9/5 midnight and 9:00am
#
# ./carve-log.py --log=q-svc.log --start='2016-09-05 00:00:01' --end='2016-09-05 09:00:00' --output=my-file.log


for opt, arg in options:
    if opt in ('-l', '--log'):
        input_filename = arg
    elif opt in ('-o', '--output'):
        output_filename = arg
    elif opt in ('-s', '--start'):
        start_time_str = arg
    elif opt in ('-e', '--end'):
        end_time_str = arg

print("")
print('Input log file   : {0}'.format(input_filename))
print('Output log file  : {0}'.format(output_filename))
print('Start time       : {0}'.format(start_time_str))
print('End time         : {0}'.format(end_time_str))


def get_date_obj(line):
    date_obj = None
    log_re = re.compile("^(([0-9\-]+)\s+([0-9:])+).*")
    m = log_re.match(line)
    if m:
        date_obj = datetime.strptime(m.group(1), '%Y-%m-%d %H:%M:%S')

    return date_obj

def next_line(fd):
    log_re = re.compile("^(([0-9\-]+)\s+([0-9:])+).*")
    found = False
    line = None
   
    while not found:
        line = fd.readline()
        if log_re.match(line):
            found = True
       
    return line

def bin_search_start_date(log_filename, start_time):
    input_fd = open(log_filename, 'r')
    found = False
    
    # Determine EoF
    input_fd.seek(0, 2)
    eof = input_fd.tell()
    
    bin_op = 2
    current_pos = int(eof / 2 )
    previous_pos = current_pos
    previous_date = None
    
    while not found:
        input_fd.seek(current_pos)
        
        line = next_line(input_fd)
        current_pos = input_fd.tell()

        current_date = get_date_obj(line)
        if current_date is None:
            break
        
        if current_date == start_time:
            break

        if current_date < start_time:
            offset = int((eof - current_pos) / 2)
            previous_pos = current_pos
            previous_date = current_date
            current_pos += offset
        else:
            break
        
    input_fd.seek(previous_pos)
    current_pos = input_fd.tell()
    input_fd.close()
    return current_pos, previous_date


def process_log(log_filename, output_filename, start_pos, end_time):
    input_fd = open(log_filename, 'r')
    output_fd = open(output_filename, 'w')
    input_fd.seek(start_pos)
    log_re = re.compile("^(([0-9\-]+)\s+([0-9:])+).*")
    
    for line in input_fd:
        m = log_re.match(line)
        if m:
            log_time = datetime.strptime(m.group(1), '%Y-%m-%d %H:%M:%S')

        if log_time >= end_time:
            break

        output_fd.write(line)
    

    output_fd.close()
    input_fd.close()
    
start_time = datetime.strptime(start_time_str, '%Y-%m-%d %H:%M:%S')
end_time   = datetime.strptime(end_time_str, '%Y-%m-%d %H:%M:%S')

print("")
print("Start time obj: {0}".format(start_time))
print("End time obj  : {0}".format(end_time))

if end_time < start_time:
    raise "End time is prior to start time"

start_search_pos, start_search_date = bin_search_start_date(input_filename, start_time)
print("Start search position = {0}, Date = {1}".format(start_search_pos, start_search_date))

process_log(input_filename, output_filename, start_search_pos, end_time)





