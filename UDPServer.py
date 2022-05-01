import socket
import math

def ConvertToBin(num, minLength): #this is a copy of client's ConvertToBin
    bnry = bin(num).replace('0b','') #convert to binary string and remove prefix
    temp = bnry[::-1] #reverse the string
    while len(temp) < minLength:
        temp += '0' #put 0s behind the existing number until it is of length
    bnry = temp[::-1] #reverse the string again to get the correct binary number
    return bnry

def MakeChecksum(pkt): #this is a copy of client's MakeChecksum
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

def BuildPacket(ackNum, payload): #this is NOT a copy of client's BuildPacket
    #convert numbers to binary
    ackNumBin = ConvertToBin(ackNum, 8)
    #build packet
    packet = ackNumBin + payload
    #print("sent ackNum:", ackNum)
    return packet

def Send(socket, dest, pkt): #this is NOT a copy of client's Send
    encodedMsg = str.encode(pkt)
    socket.sendto(encodedMsg, dest)

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

#always be looking for messages
lastSeqNum = -1
expectedSeqNum = 0
transferDone = False
while not transferDone:
    #receive and acknowledge all received messages and increment i once a correct packet is received
    correctPkt = False
    while not correctPkt:
        addressPair = server_socket.recvfrom(bufferSize)
        rcvPacket = addressPair[0]
        address = addressPair[1]

        rcvSeqNumBin = "{}".format(rcvPacket[:8]).replace('b', '').replace('\'', '') #sequence number is first 8 bits
        rcvChecksum = "{}".format(rcvPacket[8:24]).replace('b', '').replace('\'', '') #checksum is the next 16 bits
        rcvPayload = "{}".format(rcvPacket[24:]).replace('b', '').replace('\'', '') #payload is the rest
        #IMPORTANT: change these assignments according to how the packet is
        # generated in the UDPClient file, there is no way to have the server
        # check for us

        rcvSeqNum = int(rcvSeqNumBin, 2)           
        
        checksum = MakeChecksum(rcvSeqNumBin + rcvPayload) #make receiver checksum
        if (rcvChecksum == checksum) and (rcvSeqNum == expectedSeqNum):
            #print("Correct packet received")
            packet = BuildPacket(rcvSeqNum, '') #build ack packet with no payload
            lastSeqNum = rcvSeqNum
            expectedSeqNum += 1
            if expectedSeqNum >= 256: #loop expected sequence number
                expectedSeqNum -= 256
            correctPkt = True
            numBytes += math.ceil(len(rcvPayload) / 8)
            if (len(rcvPayload) / 8) != 100:
                transferDone = True
        else:
            #print("Incorrect packet received")
            packet = BuildPacket(lastSeqNum, '') #build nack packet with no payload
            correctPkt = False
            if rcvChecksum != checksum:
                numErrors += 1
            else:
                numOutOfSeq += 1

        Send(server_socket, address, packet)

#print statistical variables
print("transfer done")
print("numBytes:", numBytes)
print("numErrors:", numErrors)
print("numOutOfSeq:", numOutOfSeq)

#close server
server_socket.close()
