
import socket
import json
import base64

from em_crosstalk_test_tools import wave_file_from_info

socket_open = True

T_PORT = 8001
TCP_IP = 'localhost'
BUF_SIZE = 4096


wifi_socket = socket.socket (socket.AF_INET, socket.SOCK_STREAM)
wifi_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

wifi_socket.bind((TCP_IP, T_PORT))
wifi_socket.listen(1)

con, addr = wifi_socket.accept()

print ('Connection Address is: ' , addr)


message_raw  = con.recv(BUF_SIZE)
print(message_raw)
message = message_raw.decode('utf-8')
data_dictionary = json.loads(message)
name = data_dictionary['name'].replace(':','_').replace(',','_')

wavfile = wave_file_from_info(f'wifi-crosstalk-serverside_{name}.wav', data_dictionary)

while socket_open:
    message_raw = con.recv(BUF_SIZE)
   
    if message_raw != b'':
        data = message_raw
        wavfile.writeframes(data)
    else:
        wavfile.close()
        socket_open = False

con.close()
