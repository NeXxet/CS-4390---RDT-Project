import socket
serverPort = 12000
client_socket = socket.socket(socket.AF_INET, socket.SOCKET_DGRAM)

message = "Hello message to server"
client_socket.sendto(message.encode("utf-8"), ('127.0.0.1', serverPort))
data, addr = client_socket.recvfrom(2048)

print("message from server:")
print(str(data))
client_socket.close()