import socket
serverPort = 12000
server_socket = socket.socket(socket.AF_INET, socket.SOCKET_DGRAM)
server_socket.bind(('127.0.0.1', serverPort))

while True:
    data, addr = server_socket.recvfrom(2048)
    message = bytes("modified message from server").encode('utf-8')
    server_socket.sendto(message, addr)