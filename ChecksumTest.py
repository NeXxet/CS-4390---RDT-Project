#This is a test of converting numbers to binary, randomly and artifially corrupting
# packets, and creating and checking checksums.
#This does not use packet structure or actual sequence numbers but instead tests
# the basic structure of how to use them
import random

def Random32BitNum():
    #return a binary string with a random 16 bit integer
    return ConvertToBin(random.randint(0, 2**32), 32)

def ConvertToBin(num, length):
    bnry = bin(num).replace('0b','') #convert to binary string and remove prefix
    temp = bnry[::-1] #reverse the string
    while len(temp) < length:
        temp += '0' #put 0s behind the existing number until it is of length
    bnry = temp[::-1] #reverse the string again to get the correct binary number
    return bnry

def Corrupt(num):
    index = random.randint(0, len(num)-1) #randomly select an index to change
    if num[index] == '0': #fip the selected index
        flipped = '1'
    else:
        flipped = '0'
    num = num[:index] + flipped + num[index+1:] #reassign string with new flipped index
    return num

def MakeChecksum(pkt):
    #make sure that pkt is 32 bits
    if len(pkt) != 32:
        print("packet the right length to form checksum: ", pkt)
        return
    #divide packet into two 16 bit sections
    a = pkt[:16]
    b = pkt[16:]
    #sum up the sections
    sum = ConvertToBin(int(a, 2) + int(b, 2), 18) #allow for 2 carry bits
    #add the carry bits if there are any
    if sum[:2] != "00":
        sum = ConvertToBin(int(sum[:2], 2) + int(sum[2:], 2), 16)
    #change the sum to 1's complement
    checksum = ''
    for i in sum:
        if i == '1':
            checksum += '0'
        else:
            checksum += '1'
    #return the checksum
    return checksum

def Send(pkt):
    print("Sent packet:", pkt)
    check = MakeChecksum(pkt)
    print("    Checksum:", check)
    #randomly corrupt the packet
    rand = random.randint(1, 100)
    if rand <= CORRUPT_PROBA:
        pkt = Corrupt(pkt)
        print("PACKET CORRUPTED")
    print()
    #return the actual packet sent
    return pkt, check

def Receive(pkt, sentCheck):
    print("Received packet:", pkt)
    check = MakeChecksum(pkt)
    print("    Checksum:", check)
    if check != sentCheck:
        print("CHECKSUMS NOT EQUAL, REQUEST RETRANSMITION")
    print()

i = 0
#seqNum = 0
CORRUPT_PROBA = 20
while i < 10:
    #make a random packet
    packet = Random32BitNum()
    #simulate the sending of a packet
    packet, sentChecksum = Send(packet)
    #simulate the receiving of a packet
    Receive(packet, sentChecksum)
    print("-------")
    #seqNum += 1
    #if seqNum >= 256:
        #seqNum = 0
    i += 1
