import socket
import sys
import random
from time import sleep
bufferSize = 1024

def ConvertToBin(num, minLength):
    bnry = bin(num).replace('0b','') #convert to binary string and remove prefix
    temp = bnry[::-1] #reverse the string
    while len(temp) < minLength:
        temp += '0' #put 0s behind the existing number until it is of length
    bnry = temp[::-1] #reverse the string again to get the correct binary number
    return bnry

def MakeChecksum(pkt):
    thisPkt = pkt
    while (len(thisPkt) % 16) != 0: #make sure the pkt has correct number of bits
        thisPkt += '0' #add 0s to the end of the packet
    i = 0
    sum = 0
    while i < len(thisPkt): #sum together each 16-bit word
        sum += int(thisPkt[i:i+16], 2)
        i += 16
    sumString = ConvertToBin(sum, 16) #convert to binary string
    while len(sumString) > 16: #make sure to add all carry bits until the checksum is 16 bits
        numExtra = len(sumString) - 16
        carryBits = sumString[:numExtra+1]
        sumString = ConvertToBin(int(carryBits, 2) + int(sumString[numExtra:], 2), 16)
    checksum = ''
    for i in sumString: #swap all digits in the checksum
        if i == '1':
            checksum += '0'
        else:
            checksum += '1'
    return checksum

#not used yet, still a WIP
def BuidHeader(seqNum, ackNum, rcvWin):
    #need array of the variables for the header and need to convert them
    # one by one to binary and stick them in one string to be sent as the
    # header
    #probably needed: sequence number, acknowledgement number, receive window, and checksum
    header = ''
    header += ConvertToBin(seqNum, 8) #add 8-bit sequence number to header
    header += ConvertToBin(ackNum, 8) #add 8-bit acknowledgement number to header
    header += ConvertToBin(rcvWin, 8) #add 8-bit receive window size to header
    return header

def BuildPacket(header, payload):
    return header + payload

def Corrupt(pkt, corruptProb):
    #see if the packet is to be corrupted
    rand = random.randint(1,100)
    if rand > corruptProb: #corrupt if the random int is within the corrupt probability
        return pkt

    #corrupt the packet
    print("PACKET CORRUPTED")
    index = random.randint(0, len(pkt)-1) #randomly select an index
    if pkt[index] == '0': #flip the selected index
        flipped = '1'
    else:
        flipped = '0'
    pkt = pkt[:index] + flipped + pkt[index+1:] #reassign string with new index
    return pkt

def Send(socket, dest, pkt, corruptProb):
    check = MakeChecksum(pkt) #make checksum
    pkt = pkt[:8] + check + pkt[8:] #insert checksum after seq num in packet
    reply = ''
    while reply != "ACK":
        thispkt = Corrupt(pkt, corruptProb) #call the Corrupt method to maybe corrupt the packet
        encodedMsg = str.encode(thispkt) #encode the new packet
        socket.sendto(encodedMsg, dest) #send to server
        pair = socket.recvfrom(bufferSize) #receive a message from the server
        reply = "{}".format(pair[0]).replace('b', '').replace('\'', '') #get the raw message received
        print("reply:", reply)

file = open(sys.argv[1], 'r') #data file name is first argument
data = file.read() #read in all the data to one large string
file.close() #close the file
binData = ''.join(format(ord(x), 'b') for x in data) #convert the data to binary

#create socket
serverPort = ("127.0.0.1", 20001)
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

#set up local variables
CORRUPT_PROBA = int(sys.argv[2]) #corruption probabiity is second argument
seqNum = 0
i = 0
j = 0

#send the data until it is gone
while i < len(binData): #iterate through the data, taking 100 bytes each time
    if(len(binData[i:]) >= 800): #if the data has more than 100 bytes left, take the next 100 bytes
        payload = binData[i:i+800]
    else:
        payload = binData[i:] #if the data has less than 100 bytes left, take the rest
    header = ConvertToBin(seqNum, 8) #header, for now, is just the sequence number
    packet = BuildPacket(header, payload) #create the packet
    print(j)
    Send(client_socket, serverPort, packet, CORRUPT_PROBA) #send the packet to the server
    seqNum += 1 #for now, just increase sequence number by 1
    if(seqNum == 256):
        seqNum = 0
    i += 800
    j += 1

#end transfer and close socket
print("transfer done")
client_socket.close()
