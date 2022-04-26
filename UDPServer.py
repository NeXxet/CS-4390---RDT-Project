import socket

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

localIP = "127.0.0.1"
localPort = 20001
bufferSize = 1024

msgFromServer = "Hello to client"
encodedMsg = str.encode(msgFromServer)

server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind((localIP, localPort))

i = -1
while True:
    addressPair = server_socket.recvfrom(bufferSize)
    i += 1
    packet = addressPair[0]
    address = addressPair[1]

    seqNum = "{}".format(packet[:8]).replace('b', '').replace('\'', '') #sequence number is first 8 bits
    checksum = "{}".format(packet[8:24]).replace('b', '').replace('\'', '') #checksum is the next 16 bits
    payload = "{}".format(packet[24:]).replace('b', '').replace('\'', '') #payload is the rest
    #IMPORTANT: change these assignments according to how the packet is
    # generated in the UDPClient file, there is no way to have the server
    # check for us
    
    rcvrChecksum = MakeChecksum(seqNum + payload) #make receiver checksum
    if checksum == rcvrChecksum:
        print(i, "Correct packet received")
    else:
        print(i, "Incorrect packet received")

    #clientMsg = "Message from Client:{}".format(data)
    #clientIP = "Client IP Address:{}".format(address)

    #print(clientMsg)
    #print(clientIP)
    #print(i)

    #server_socket.sendto(encodedMsg, address)
