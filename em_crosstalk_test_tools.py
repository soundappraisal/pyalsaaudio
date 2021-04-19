'''
Support functions for the em-crosstalk tests.
'''

import wave

samplewidth_dict = {'S8': 1,
                    'U8': 1,
                    'S16_LE': 2,
                    'S16_BE': 2,
                    'U16_LE': 2,
                    'U16_BE': 2,
                    'S24_LE': 3,
                    'S24_BE': 3,
                    'U24_LE': 3,
                    'U24_BE': 3,
                    'S32_LE': 4,
                    'S32_BE': 4,
                    'U32_LE': 4,
                    'U32_BE': 4,
                    'FLOAT_LE': 4,
                    'FLOAT_BE': 4,
                    'FLOAT64_LE': 8,
                    'FLOAT64_BE': 8,
                    'S24_3LE': 3,
                    'S24_3BE': 3,
                    'U24_3LE': 3,
                    'U24_3BE': 3, }


def wave_file_from_info(filename, pcm_info):
    wave_file = wave.open(filename, 'wb')
    wave_file.setnchannels(pcm_info['channels'])
    wave_file.setsampwidth(samplewidth_dict[pcm_info['format_name']])
    wave_file.setframerate(pcm_info['rate'])

    return wave_file
