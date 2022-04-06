import socket
localIP = "127.0.0.1"
localPort = 20001
bufferSize = 1024

msgFromServer = "Hello to client"
encodedMsg = str.encode(msgFromServer)

server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind((localIP, localPort))

while True:
    addressPair = server_socket.recvfrom(bufferSize)
    data = addressPair[0]
    address = addressPair[1]

    clientMsg = "Message from Client:{}".format(data)
    clientIP = "Client IP Address:{}".format(address)

    print(clientMsg)
    print(clientIP)

    server_socket.sendto(encodedMsg, address)
