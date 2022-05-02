import sys
import socket
import math
from queue import PriorityQueue
import binascii

def WriteAsciiToFile(payload, outFile):
    while (len(payload) % 7) != 0:
        payload += '0'
    i = 0
    while i < len(payload):
        n = int(payload[i:i+7], 2)
        outFile.write(chr(n))
        i += 7

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

def BuildPacket(ackNum, payload):
    #convert numbers to binary
    ackNumBin = ConvertToBin(ackNum, 8)
    #build packet
    packet = ackNumBin + payload
    #print("sent ackNum:", ackNum)
    return packet

def Send(socket, dest, pkt):
    # send the packet to the client
    encodedMsg = str.encode(pkt)
    socket.sendto(encodedMsg, dest)
    
def GBNReceive(socket, outFile):
    global numBytes
    global numErrors
    global numOutOfSeq
    lastSeqNum = -1
    expectedSeqNum = 0
    transferDone = False
    while not transferDone:
        addressPair = socket.recvfrom(bufferSize)
        rcvPacket = addressPair[0]
        address = addressPair[1]

        #convert message to usable binary
        rcvPacket = "{}".format(rcvPacket).replace('b', '').replace('\'', '')
        rcvSeqNumBin = rcvPacket[:8] #sequence number is first 8 bits
        rcvChecksum = rcvPacket[8:24] #checksum is the next 16 bits
        rcvPayload = rcvPacket[24:] #payload is the rest
        
        rcvSeqNum = int(rcvSeqNumBin, 2)           
           
        checksum = MakeChecksum(rcvSeqNumBin + rcvPayload) #make receiver checksum
        if (rcvChecksum == checksum) and (rcvSeqNum == expectedSeqNum):
            #print("Correct packet received")
            packet = BuildPacket(rcvSeqNum, '') #build ack packet with no payload
            lastSeqNum = rcvSeqNum
            expectedSeqNum += 1
            if expectedSeqNum >= 256: #loop expected sequence number
                expectedSeqNum -= 256
            numBytes += math.ceil(len(rcvPayload) / 8)
            if (len(rcvPayload) / 8) != 100:
                transferDone = True

            #write payload to outFile
            WriteAsciiToFile(rcvPayload, outFile)
            
        else:
            #print("Incorrect packet received")
            packet = BuildPacket(lastSeqNum, '') #build ack packet for the last arrival with no payload
            if rcvChecksum != checksum:
                numErrors += 1
            else:
                numOutOfSeq += 1

        Send(server_socket, address, packet)

def SRReceive(socket, outFile):
    global numBytes
    global numErrors
    global numOutOfSeq
    buffer = PriorityQueue()
    expectedSeqNum = 0
    transferDone = False
    while (not transferDone) or (not buffer.empty()):
        try:
            addressPair = socket.recvfrom(bufferSize)
            rcvPacket = addressPair[0]
            address = addressPair[1]

            #convert message to usable binary
            rcvPacket = "{}".format(rcvPacket).replace('b', '').replace('\'', '')
            rcvSeqNumBin = rcvPacket[:8] #sequence number is first 8 bits
            rcvChecksum = rcvPacket[8:24] #checksum is the next 16 bits
            rcvPayload = rcvPacket[24:] #payload is the rest
            
            rcvSeqNum = int(rcvSeqNumBin, 2)           
               
            checksum = MakeChecksum(rcvSeqNumBin + rcvPayload) #make receiver checksum
            if rcvChecksum == checksum:
                # accept packet
                # send ack
                packet = BuildPacket(rcvSeqNum, '') #build ack packet with no payload
                numBytes += math.ceil(len(rcvPayload) / 8)
                Send(server_socket, address, packet) #send ack to client
                buffer.put(rcvPacket)
                #check if the final piece of data has been delivered
                if (len(rcvPayload) / 8) != 100:
                    transferDone = True
                
                # check if it was expected
                if rcvSeqNum == expectedSeqNum:
                    # packet is expected
                    # pop all received packets until there is a gap
                    nextSeqNum = rcvSeqNum
                    while not buffer.empty():
                        if buffer.queue[0][:8] == ConvertToBin(nextSeqNum, 8):
                            # remove the first item from the list and write it to the outFile
                            WriteAsciiToFile(buffer.get()[24:], outFile)
                            
                            nextSeqNum += 1 # increase nextSeqNum by 1 and loop
                            if nextSeqNum >= 256:
                                nextSeqNum -= 256
                        else:
                            break # a gap was detected, meaning there is a packet missing
                    
                    expectedSeqNum += 1
                    if expectedSeqNum >= 256: #loop expected sequence number
                        expectedSeqNum -= 256
                else:
                    # packet is unexpected
                    numOutOfSeq += 1
                    
            else:
                # do no accept corrupted packet
                numErrors += 1

        except OSError:
            break # nothing reseived from the client after timeout time, so break loop

    # make sure to empty the buffer once the client is done transmitting
    while not buffer.empty():
        buffer.get()
    

#setup variables
localIP = "127.0.0.1"
localPort = 20001
bufferSize = 1024
numBytes = 0
numErrors = 0
numOutOfSeq = 0

#create and bind the socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind((localIP, localPort))

#get output file and open it to append
outFile = open(sys.argv[1], 'a')
outFile.truncate() # clear the file

#look for the initial message telling the server which mechanism to use
addressPair = server_socket.recvfrom(bufferSize)
msg = addressPair[0]
mechanism = "{}".format(msg).replace('b', '').replace('\'', '')
server_socket.settimeout(3) # if nothing received from client after 3 seconds of try, timeout
if mechanism == "GBN":
    print("beginning Go-Back-N transfer")
    GBNReceive(server_socket, outFile)
elif mechanism == "SR":
    print("beginning Selective Repeat transfer")
    SRReceive(server_socket, outFile)
else:
    print("invalid mechanism name:", mechanism)
    server_socket.close()
    exit()

#print statistical variables
print("transfer done")
print("numBytes:", numBytes)
print("numErrors:", numErrors)
print("numOutOfSeq:", numOutOfSeq)

#close server
server_socket.close()
