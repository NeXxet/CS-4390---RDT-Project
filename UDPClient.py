import socket
import sys
import random
import math
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

def BuildPacket(seqNum, ackNum, payload): #rcvWin):
    #get ack number by adding to the sequence number the number of bytes in the payload
    # plus 1 byte for the seqNum, 1 for the ackNum itself, and 2 for the checksum
    ackNum = seqNum + math.ceil(len(payload) / 8) + 1 + 1 + 2
    #make sure ackNum loops around
    if(ackNum >= 256):
        ackNum -= 256

    #convert numbers to binary
    seqNumBin = ConvertToBin(seqNum, 8)
    ackNumBin = ConvertToBin(ackNum, 8)
    #make checksum
    checksum = MakeChecksum(seqNumBin + ackNumBin + payload)
    #build packet
    packet = seqNumBin + ackNumBin + checksum + payload
    
    return packet, ackNumBin

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

def Send(socket, dest, pkt, ackNumBin, corruptProb):
    rcvSeqNum = ''
    while rcvSeqNum != ackNumBin:
        #send the packet to the server
        thispkt = Corrupt(pkt, corruptProb) #call the Corrupt method to maybe corrupt the packet
        encodedMsg = str.encode(thispkt) #encode the new packet
        socket.sendto(encodedMsg, dest) #send to server

        #receive a reply
        pair = socket.recvfrom(bufferSize) #receive a message from the server
        rcvSeqNum = "{}".format(pair[0][:8]).replace('b', '').replace('\'', '')
        rcvAckNum = "{}".format(pair[0][8:]).replace('b', '').replace('\'', '')
        #IMPORTANT: the server only sends a seqNum and ackNum, you must manually
        # change this if that is to change
        print("rcvSeqNum:", rcvSeqNum)
        
    return int(rcvAckNum, 2)

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
ackNum = 0
i = 0 #i is used to iterate through the data and get the payload
j = 0 #j is used to count the number of packets

#send the data until it is gone
while i < len(binData): #iterate through the data, taking 100 bytes each time
    if(len(binData[i:]) >= 800): #if the data has more than 100 bytes left, take the next 100 bytes
        payload = binData[i:i+800]
    else:
        payload = binData[i:] #if the data has less than 100 bytes left, take the rest
    packet, ackNumBin = BuildPacket(seqNum, ackNum, payload) #create the packet and update ackNum
    print(j)
    ackNum = Send(client_socket, serverPort, packet, ackNumBin, CORRUPT_PROBA) #send the packet to the server
    seqNum = ackNum #set the next seqNum to the ackNum
    if(seqNum >= 256): #this should never proc, but leave it just in case
        seqNum -= 256;
    i += 800
    j += 1

#end transfer and close socket
print("transfer done")
client_socket.close()
