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

from __future__ import print_function

import sys
import time
import argparse
import wave

import alsaaudio

samplewidth_dict = {'S8':1,
                    'U8':1,
                    'S16_LE':2,
                    'S16_BE':2,
                    'U16_LE':2,
                    'U16_BE':2,
                    'S24_LE':3,
                    'S24_BE':3,
                    'U24_LE':3,
                    'U24_BE':3,
                    'S32_LE':4,
                    'S32_BE':4,
                    'U32_LE':4,
                    'U32_BE':4,
                    'FLOAT_LE':4,
                    'FLOAT_BE':4,
                    'FLOAT64_LE':8,
                    'FLOAT64_BE':8,
                    'S24_3LE':3,
                    'S24_3BE':3,
                    'U24_3LE':3,
                    'U24_3BE':3,}

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

def wave_file_config_info(filename, pcm_info):
    wave_file = wave.open(args.aec_file, 'wb')
    wave_file.setnchannels(pcm_info['channels'])
    wave_file.setsampwidth(samplewidth_dict[pcm_info['format_name']])
    wave_file.setframerate(args.samplerate)

    return wave_file
    
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
    
    ae_crosstalk_wav = wave_file_from_info(args.aec_file,pcm_info)

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
    
            print(f'Write {l}-frames to file read at: {read_time}.')
            ae_crosstalk_wav.writeframes(data)

            if read_time - start_time > args.duration:
                acquisition_on = False

        dt = (periodsize-ts_tuple[2])/args.samplerate
        if dt > 0:
            time.sleep(dt)

def test_wifi_crosstalk(args):

    pcm_device = alsaaudio.PCM(alsaaudio.PCM_CAPTURE, 
                               alsaaudio.PCM_NONBLOCK, 
                               channels=1, 
                               rate=args.samplerate, 
                               format=args.format, 
                               periodsize=args.samplerate//10, 
                               device=args.device)

    pcm_info = pcm_device.info()
    print(pcm_info)
    
    ae_crosstalk_wav = wave_file_from_info(args.aec_file,pcm_info)

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
    
            print(f'Write {l}-frames to file read at: {read_time}.')
            ae_crosstalk_wav.writeframes(data)

            if read_time - start_time > args.duration:
                acquisition_on = False

        dt = (periodsize-ts_tuple[2])/args.samplerate
        if dt > 0:
            time.sleep(dt)



if __name__ == '__main__':


    args = parse_arguments()
    print(args)
    test_ae_crosstalk(args)
   
