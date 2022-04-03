from pickletools import int4
import socket
import struct
from enums import GameState as GameStateEnum
from enums import SessionState as SessionStateEnum
import datetime

UDP_IP = "0.0.0.0" #This sets server ip to the RPi ip
UDP_PORT = 5606 #You can freely edit this

#reading header
header_data_types = {}
with open('pcars2_header_data_format.txt', 'r') as f:
    lines = f.read().split('\n')
    for line in lines:
        header_data_types[line.split()[1]] = line.split()[0]

#reading data and assigning names to data types in data_types dict
telemetry_data_types = {}
with open('pcars2_telemetry_data_format.txt', 'r') as f:
    lines = f.read().split('\n')
    for line in lines:
        telemetry_data_types[line.split()[1]] = line.split()[0]

#reading data and assigning names to data types in data_types dict
race_data_types = {}
with open('pcars2_race_data_format.txt', 'r') as f:
    lines = f.read().split('\n')
    for line in lines:
        race_data_types[line.split()[1]] = line.split()[0]

#reading data and assigning names to data types in data_types dict
gamestate_data_types = {}
with open('pcars2_gamestate_data_format.txt', 'r') as f:
    lines = f.read().split('\n')
    for line in lines:
        gamestate_data_types[line.split()[1]] = line.split()[0]

#reading data and assigning names to data types in data_types dict
timing_data_types = {}
with open('pcars2_timing_data_format.txt', 'r') as f:
    lines = f.read().split('\n')
    for line in lines:
        timing_data_types[line.split()[1]] = line.split()[0]

#assigning sizes in bytes to each variable type
jumps={
    's32': 4, #Signed 32bit int, 4 bytes of size - long
    'u32': 4, #Unsigned 32bit int
    'u16': 2, #Unsigned 16bit int - short
    's16': 2, #Signed 16bit int
    'u8': 1, #Unsigned 8bit int
    's8': 1, #Signed 8bit int
    'f32': 4, #Floating point 32bit
    'b8': 1, # 8 bits - 1 byte
    'c1': 1, #char 1
    'c2': 2, #char 2
    'c3': 3, #char 3
    'c64': 64, #char 64
    'hzn': 12, #Unknown, 12 bytes of.. something
    'pb': 10, #packetbase, 10 bytes of.. something
    'a3f32': 12, #Array[3] Floating point 32bit
    'a4f32': 16, #Array[3] Floating point 32bit
    'a4u8': 4, #array[4] Unsigned 8bit int
    'a2u8': 2, #array[2] Unsigned 8bit int
    'a4u16': 8, #array[4] Unsigned 16bit int - short
    'a4s16': 8, #array[4] Signed 16bit int
}

def get_data(data, type_def):
    return_dict={}

    #additional var
    passed_data = data
    
    for i in type_def:
        d_type = type_def[i]#checks data type (s32, u32 etc.)
        jump=jumps[d_type]#gets size of data
        current = passed_data[:jump]#gets data

        decoded = 0
        #complicated decoding for each type of data
        if d_type == 's32':
            decoded = int.from_bytes(current, byteorder='little', signed = True)
        elif d_type == 'u32':
            decoded = int.from_bytes(current, byteorder='little', signed=False)
        elif d_type == 'f32':
            decoded = struct.unpack('f', current)[0]
        elif d_type == 'u16':
            decoded = struct.unpack('H', current)[0]
        elif d_type == 's16':
            decoded = struct.unpack('h', current)[0]
        elif d_type == 'u8':
            decoded = struct.unpack('B', current)[0]
        elif d_type == 's8':
            decoded = struct.unpack('b', current)[0]
        elif d_type == 'b8':
            decoded = current
        elif d_type == 'c1':
            decoded = current.decode(encoding = 'ISO-8859-1').split("\x00")[0]
        elif d_type == 'c2':
            decoded = current.decode(encoding = 'ISO-8859-1').split("\x00")[0]
        elif d_type == 'c3':
            decoded = current.decode(encoding = 'ISO-8859-1').split("\x00")[0]
        elif d_type == 'c64':
            decoded = current.decode(encoding = 'ISO-8859-1').split("\x00")[0]
        elif d_type == 'a4c40':
            print (current)
            #decoded = current.decode(encoding = 'ISO-8859-1').split("\x00")[0]
        elif d_type == 'a3f32':
            decoded = list(struct.unpack('fff', current))
        elif d_type == 'a4f32':
            decoded = list(struct.unpack('ffff', current))
        elif d_type == 'a2u8':
            decoded = list(struct.unpack('BB', current))
        elif d_type == 'a4u8':
            decoded = list(struct.unpack('BBBB', current))
        elif d_type == 'a4u16':
            decoded = list(struct.unpack('HHHH', current))
        elif d_type == 'a4s16':
            decoded = list(struct.unpack('hhhh', current))

        #adds decoded data to the dict
        return_dict[i] = decoded
        
        #removes already read bytes from the variable
        passed_data = passed_data[jump:]
    
    #returns the dict
    return return_dict


#setting up an udp server
sock = socket.socket(socket.AF_INET, # Internet
                     socket.SOCK_DGRAM) # UDP

sock.bind((UDP_IP, UDP_PORT))

print ("Starting PCARS2 UDP Listener")


telemetry_data={}
while True:
    packet, addr = sock.recvfrom(1500) # buffer size is 1400 bytes, this line reads data from the socket

    header=get_data(packet, header_data_types)
    #print(header)
    dt = datetime.datetime.now()
    ts = datetime.datetime.timestamp(dt)
    telemetry_data['timestamp']=ts

    if header['packetType']==0:
        #received data is now in the retuturned_data dict, key names are in data_format.txt
        #print ('Telemetry Packet', len(packet))
        returned_data = get_data(packet, telemetry_data_types)
        telemetry_data['telemetry']=returned_data
    
    if header['packetType']==1:
        #received data is now in the retuturned_data dict, key names are in data_format.txt
        #print ('Race Data Packet', len(packet))
        returned_data = get_data(packet, race_data_types)
        telemetry_data['raceData']=returned_data

    if header['packetType']==2:
        #received data is now in the retuturned_data dict, key names are in data_format.txt
        #print ('Participants Packet', len(packet))
        pass

    if header['packetType']==3:
        #received data is now in the retuturned_data dict, key names are in data_format.txt
        #print ('Timings Packet', len(packet))
        returned_data = get_data(packet, timing_data_types)
        #Data Convertions
        returned_data['racePosition']=returned_data['racePosition']-128
        telemetry_data['timing']=returned_data

    if header['packetType']==4:
        #received data is now in the retuturned_data dict, key names are in data_format.txt
        #print ('Game State Packet', len(packet))
        returned_data = get_data(packet, gamestate_data_types)

        #Data Convertions
        #first 3 bits are used for game state enum, second 3 bits for session state enum
        gameState=returned_data['gameState']
        bytes =bytearray(gameState)
        bytes_as_bits = ''.join(format(byte, '08b') for byte in bytes)
        sessionState=bytes_as_bits[0:4]
        gameState=bytes_as_bits[4:8]
        returned_data['gameState']=GameStateEnum(int(gameState, 2)).name
        returned_data['sessionState']=SessionStateEnum(int(sessionState, 2)).name

        telemetry_data['gameState']=returned_data

    if header['packetType']==7:
        #received data is now in the retuturned_data dict, key names are in data_format.txt
        #print ('TimeStats Packet', len(packet))
        pass

    if header['packetType']==8:
        #received data is now in the retuturned_data dict, key names are in data_format.txt
        #print ('ParticipantVehicleNames Packet', len(packet))
        pass

    if 'gameState' in telemetry_data.keys():
        gs=True



    else:
        print ('No gameState yet')
        gs=False

    if 'raceData' in telemetry_data.keys():
        rd=True
    else:
        print ('No raceData yet')
        rd=False

    if 'telemetry' in telemetry_data.keys():
        tel=True
    else:
        print ('No telemetery data yet')
        tel=False

    if 'timing' in telemetry_data.keys():
        tim=True
    else:
        print ('No timing data yet')
        tim=False

    if gs & rd & tel & tim:
        gameState=telemetry_data['gameState']['gameState']
        sessionstate=telemetry_data['gameState']['sessionState']
        print (gameState, sessionstate)
        if gameState=='INGAME_PLAYING' and sessionstate=='RACE':
            print (telemetry_data)
        


'''
PACKET_TYPES = {
	eCarPhysics = 0,
	eRaceDefinition = 1,
	eParticipants = 2,
	eTimings = 3,
	eGameState = 4,
	eWeatherState = 5, # not sent at the moment, information can be found in the game state packet
	eVehicleNames = 6, # not sent at the moment
	eTimeStats = 7,
	eParticipantVehicleNames = 8
}
'''
