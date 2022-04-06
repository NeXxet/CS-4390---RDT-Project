import socket

msgFromClient = "Hello to server"
encodedMsg = str.encode(msgFromClient)
serverPort = ("127.0.0.1", 20001)
bufferSize = 1024

client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

client_socket.sendto(encodedMsg, serverPort)
msgFromServer = client_socket.recvfrom(bufferSize)

data = "Message from Server {}".format(msgFromServer[0])

print(data)

client_socket.close()
