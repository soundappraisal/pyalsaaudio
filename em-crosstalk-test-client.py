#!/usr/bin/env python3
# -*- mode: python; indent-tabs-mode: t; c-basic-offset: 4; tab-width: 4 -*-

## recordtest.py
##
## This is an example of a simple sound capture script.
##
## The script opens an ALSA pcm device for sound capture, sets
## various attributes of the capture, and reads in a loop,
## writing the data to standard out.
##
## To test it out do the following:
## python recordtest.py out.raw # talk to the microphone
## aplay -r 8000 -f S16_LE -c 1 out.raw

#!/usr/bin/env python

import sys
import time
import argparse
import numpy as np

import socket
import json
import base64

import alsaaudio

from em_crosstalk_test_tools import wave_file_from_info

def parse_arguments():
    parser = argparse.ArgumentParser(description='Record sound to make possible electro-magnetic crosstalk visible.')

    parser.add_argument('-a','--aec-file',
                        type=str,
                        action='store',
                        default = 'acquisition-electronics-crosstalk.wav',
                        help='specify the file in which to store the acquisition electronics crosstalk test',)

    parser.add_argument('-w','--wifi-file',
                        type=str,
                        action='store',
                        default = 'wifi-crosstalk.wav',
                        help='specify the file in which to store the Wi-Fi crosstalk test',)

    parser.add_argument('-d','--device',
                        type=str,
                        action='store',
                        default = 'default',
                        help='specify the ALSA device: <ALSA plugin>:<card><deviceno>',)

    parser.add_argument('-r','--remote',
                        type=str,
                        action='store',
                        default = 'localhost:8001',
                        help='specify the remote IP address and port to be accessed through Wi-Fi',)

    parser.add_argument('-f', '--format',
                        type=int,
                        action='store',
                        default=alsaaudio.PCM_FORMAT_S16_LE,
                        help='numerical format of a single sample',)

    parser.add_argument('-s', '--samplerate',
                        type=int,
                        action='store',
                        default=48000,
                        help='samplerate in Hz',)


    parser.add_argument('-t', '--duration',
                        type=int,
                        action='store',
                        default=10,
                        help='minimal duration of recording in seconds',)

    args = parser.parse_args()

    return args

def test_ae_crosstalk(args):

    pcm_device = alsaaudio.PCM(alsaaudio.PCM_CAPTURE,
                               alsaaudio.PCM_NONBLOCK,
                               channels=1,
                               rate=args.samplerate,
                               format=args.format,
                               periodsize=args.samplerate//10,
                               device=args.device)

    pcm_info = pcm_device.info()
    print(pcm_info)

    name = pcm_info['name'].replace(':','_').replace(',','_')

    ae_crosstalk_wav = wave_file_from_info(f'{args.aec_file}{name}.wav',pcm_info)

    periodsize =  pcm_info['period_size']


    pcm_device.set_tstamp_mode()
    pcm_device.set_tstamp_type()

    start_time = None
    read_time = None

    acquisition_on = True

    while acquisition_on:
        # Read data from device
        l, data = pcm_device.read()
        ts_tuple = pcm_device.htimestamp()

        if l > 0:

            read_time = ts_tuple[0]+ 1e-9* ts_tuple[1]
            if start_time is None:
                start_time = read_time

            print(f'Write {l}-frames to file recorded at time: {read_time}.')
            ae_crosstalk_wav.writeframes(data)

            if read_time - start_time > args.duration:
                acquisition_on = False

        dt = (periodsize-ts_tuple[2])/args.samplerate
        if dt > 0:
            time.sleep(dt)

    pcm_device.close()

def test_wifi_crosstalk(args):

    pcm_device = alsaaudio.PCM(alsaaudio.PCM_CAPTURE,
                               alsaaudio.PCM_NONBLOCK,
                               channels=1,
                               rate=args.samplerate,
                               format=args.format,
                               periodsize=args.samplerate,
                               device=args.device)

    pcm_info = pcm_device.info()
    print(pcm_info)

    ae_crosstalk_wav = wave_file_from_info(args.wifi_file, pcm_info)

    periodsize =  pcm_info['period_size']

    ip_address, ip_port = args.remote.split(':')
    buffersize = 4096
    print(f'ip_address: {ip_address}, ip_port:{ int(ip_port)}')
    pcm_info['msg_type']='pcm_info'
    msg = json.dumps(pcm_info)
    print(f'msg: {msg}, type: {type(msg)}')

    wifi_socket = socket.socket (socket.AF_INET, socket.SOCK_STREAM)
    wifi_socket.connect((ip_address, int(ip_port)))


    encoded_msg = msg.encode('utf-8')
    print(f'length {len( encoded_msg)}')
    wifi_socket.send(encoded_msg)

    time.sleep(1)

    pcm_device.set_tstamp_mode()
    pcm_device.set_tstamp_type()

    start_time = None
    read_time = None

    acquisition_on = True

    newdata = False
    pointer = 0
    network_interval = 0.1
    network_interval_bytes = int(np.floor(0.1*args.samplerate))*ae_crosstalk_wav.getsampwidth()

    data_to_send_old = None
    data_to_send = None
    while acquisition_on:
        # Read data from device
        ts_tuple = pcm_device.htimestamp()

        if ts_tuple[2] > periodsize or start_time is None:
            l, data = pcm_device.read()
            ts_tuple = pcm_device.htimestamp()
            if l > 0:
                read_time = ts_tuple[0]+ 1e-9* ts_tuple[1]
                if start_time is None:
                    start_time = read_time
                    socket_time = start_time

                print(f'Write {l}-frames to file recorded at time: {read_time}. Type data: {type(data)}')
                ae_crosstalk_wav.writeframes(data)

                if read_time - start_time > args.duration:
                    print(f'read_time: {read_time}, start_time: {start_time}, duration: {args.duration}')
                    acquisition_on = False

                newdata = True

                if data_to_send is not None:
                    data_to_send_old = data_to_send

                data_to_send = data
                print(f'length data_to_send {len( data_to_send)}, acquisition_on: {acquisition_on}')

        current_time = time.time()
        if start_time is not None and  current_time - socket_time > network_interval:
            if len(data_to_send) > 0:
                if not newdata:
                    print(current_time)
                    wifi_socket.send(data_to_send[pointer:pointer+network_interval_bytes])
                    pointer+=network_interval_bytes
                    socket_time = current_time
                else:
                    if data_to_send_old is not None:
                        wifi_socket.send(data_to_send[pointer:])
                    pointer = 0
                    newdata = False


    wifi_socket.send(b'')
    wifi_socket.close()

if __name__ == '__main__':


    args = parse_arguments()
    print(args)

    test_ae_crosstalk(args)
    test_wifi_crosstalk(args)


