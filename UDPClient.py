import socket
import sys
import random
import math
import time

#initiate the buffer size and statistical variables
bufferSize = 1024
numTransmits = 0
numRetransmits = 0
numTOEvents = 0
numBytes = 0
numCorrupts = 0

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

def BuildPacket(seqNum, payload):
    #convert sequence number to binary
    seqNumBin = ConvertToBin(seqNum, 8)
    #make checksum
    checksum = MakeChecksum(seqNumBin + payload)
    #build packet
    packet = seqNumBin + checksum + payload
    return packet

def Corrupt(pkt, corruptProb):
    global numCorrupts
    #see if the packet is to be corrupted
    rand = random.randint(1,100)
    if rand > corruptProb: #corrupt if the random int is within the corrupt probability
        return pkt

    #corrupt the packet
    #print("PACKET CORRUPTED")
    numCorrupts += 1
    index = random.randint(0, len(pkt)-1) #randomly select an index
    if pkt[index] == '0': #flip the selected index
        flipped = '1'
    else:
        flipped = '0'
    pkt = pkt[:index] + flipped + pkt[index+1:] #reassign string with new index
    return pkt

def Send(socket, dest, pkt, corruptProb):
    #send the packet to the server
    thispkt = Corrupt(pkt, corruptProb) #call the Corrupt method to maybe corrupt the packet
    encodedMsg = str.encode(thispkt) #encode the new packet
    socket.sendto(encodedMsg, dest) #send to server
    #print("sent seqNum:", int(pkt[:8], 2))


def GBNSend(socket, dest, binData, corruptProb, timeout):
    global numBytes
    global numTransmits
    global numTOEvents
    global numRetransmits
    seqNum = 0
    window = [] #list of in order packets in the window
    WINSIZE = 5
    i = 0 #i is used to iterate through the data and get the payload

    #send the data until it is gone
    while i < len(binData): #iterate through the data, taking 100 bytes each time
        #send all packets that can fit in the window
        while len(window) < WINSIZE:
            #get payload data
            if(len(binData[i:]) >= 800): #if the data has more than 100 bytes left, take the next 100 bytes
                payload = binData[i:i+800]
            else:
                payload = binData[i:] #if the data has less than 100 bytes left, take the rest
            numBytes += math.ceil(len(payload) / 8)

            #build packet and get expected sequence number
            packet = BuildPacket(seqNum, payload) #create the packet and update ackNum
            window.append(packet)

            #get next sequence number
            seqNum += 1
            if(seqNum >= 256): #loop seqNum
                seqNum -= 256

            #send packet
            Send(socket, dest, packet, CORRUPT_PROBA) #send the packet to the server
            numTransmits += 1
            timerStart = time.time()
            
            i += 800

        #check for all replies from server
        while len(window) > 0:
            #if there is a timeout, send the whole window and break
            if time.time() - timerStart >= timeout:
                timerStart = time.time()
                numTOEvents += 1
                for p in window:
                    Send(socket, dest, p, CORRUPT_PROBA)
                    numRetransmits += 1
            else:
                #if not timed out, try to get a response
                try:
                    #receive a reply
                    pair = socket.recvfrom(bufferSize) #receive a message from the server
                    rcvAckNum = "{}".format(pair[0][:8]).replace('b', '').replace('\'', '')
                    #IMPORTANT: the server only sends an ackNum, you must manually
                    # change this if that is to change
                    #print("rcvAckNum:", int(rcvAckNum, 2))
                    
                    #if the ack is correct, increase the window size and move on
                    if rcvAckNum == window[0][:8]:
                        window.pop(0) #remove the top packet from the window
                        break
                    #else, ignore it
                except OSError:
                    pass #if there is no reply, just continue to the top of the loop

    #has broken out of outer while loop; make sure there isn't any data left to be received
    while len(window) > 0:
        #if there is a timeout, send the whole window and break
        if time.time() - timerStart >= timeout:
            timerStart = time.time()
            for p in window:
                Send(socket, dest, p, CORRUPT_PROBA)
        else:
            #if not timed out, try to get a response
            try:
                #receive a reply
                pair = socket.recvfrom(bufferSize) #receive a message from the server
                rcvAckNum = "{}".format(pair[0][:8]).replace('b', '').replace('\'', '')
                #IMPORTANT: the server only sends an ackNum, you must manually
                # change this if that is to change
                #print("rcvAckNum:", int(rcvAckNum, 2))
                
                #if the ack is correct, increase the window size and move on
                if rcvAckNum == window[0][:8]:
                    window.pop(0) #remove the top packet from the window
                #else, ignore it
            except OSError:
                pass #if there is no reply, just continue to the top of the loop
    
file = open(sys.argv[1], 'r') #data file name is first argument
data = file.read() #read in all the data to one large string
file.close() #close the file
binData = ''.join(format(ord(x), 'b') for x in data) #convert the data to binary

#create socket
serverPort = ("127.0.0.1", 20001)
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client_socket.setblocking(False)

CORRUPT_PROBA = int(sys.argv[2]) #corruption probabiity is the second argument
mechanism = sys.argv[3] #mechanism isthe  thrid argument
timeout = float(sys.argv[4]) #the timeout time is the fourth argumetn

#get the transfer mechanism and call appropriate function
print("begin transfer")
timeBegin = time.time()
if mechanism == "GBN":
    GBNSend(client_socket, serverPort, binData, CORRUPT_PROBA, timeout)

#make sure there isn't left over acks
while True:
    try:
        client_socket.recvfrom(bufferSize)
    except OSError:
        break
    
#print statistical variables
print("transfer done")
print("numTransmits:", numTransmits)
print("numRetransmits:", numRetransmits)
print("numTOEvents:", numTOEvents)
print("numBytes:", numBytes)
print("numCorrupts:", numCorrupts)
print("timeElapsed:", time.time() - timeBegin)
      
#close client
client_socket.close()
