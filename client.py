from socket import *
import sys
import time
import re
import os
import threading

#心跳发送每两秒
def send_heartbeat():
    while True:
        time.sleep(2)  # 每隔2秒发送一个心跳
        heartbeat_message = "HBT"
        clientSocket.sendto(heartbeat_message.encode(),serverAddress)
# Server would be running on the same host as Client

def file_server():
    global s_port
    server_socket = socket(AF_INET, SOCK_STREAM)
    server_socket.bind(("127.0.0.1", 0)) #随机获得一个可用的端口号
    port = server_socket.getsockname()[1]
    server_socket.listen(5) #at most 5 peers 
    msg = f"CSP {port}" 
    clientSocket.sendto(msg.encode(),serverAddress)
    s_port = port
    #发送给服务器告诉它我这个port对应的服务器端口


    while True:
        conn, addr = server_socket.accept() #conn is a new socket for communication
        # 创建新线程来处理每个下载请求
        threading.Thread(target=send_file, args=(conn,_)).start()

def send_file(connection,filename):
    message = connection.recv(1024)
    filename = message.decode()
    subpath = username + f"/{filename}"
    if os.path.exists(subpath):
        with open(subpath, 'rb') as f:
            while True:
                data = f.read(1024)  # 每次读取 1024 字节
                if not data:
                    break  # 文件读取完毕
                connection.sendall(data)  # 发送数据     
       
        connection.close()

def receive_file(des_port,filename): #从目标des_port接受文件下载到本地
    sock = socket(AF_INET, SOCK_STREAM)
    sock.connect(("127.0.0.1", des_port))
    sock.send(filename.encode())
    # 打开一个文件以写入接收到的数据
    subpath = username + f"/{filename}"
    path = os.path.join(curpath, subpath)
    with open(path, 'wb') as f:
        while True:
            # 接收数据块
            data = sock.recv(1024)  # 每次接收 1024 字节
            if not data:
                break  # 如果没有数据，表示文件接收完成
            f.write(data)  # 写入数据块到文件

    print(f"{filename} downloaded successfully")
    sock.close()




#主函数
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("\n===== Error usage, python3 client.py SERVER_PORT ======\n")
        exit(0)

    serverHost = "127.0.0.1"
    serverPort = int(sys.argv[1])
    serverAddress = (serverHost, serverPort)
    clientSocket = socket(AF_INET, SOCK_DGRAM)  # Use SOCK_DGRAM for UDP
    curpath = os.path.dirname(__file__)
    s_port = 0


    while True: #log
        username = input("Enter username: ")
        pwd = input("Enter password: ")
        message = f"auth {username} {pwd}"
        
        # Send message to the server
        clientSocket.sendto(message.encode(), serverAddress)  # Use sendto instead of sendall
        _,  port = clientSocket.getsockname()
        
        
        # Receive response from the server
        # 1024 is a suggested packet size, you can specify it as 2048 or others
        data, server = clientSocket.recvfrom(1024)  # Use recvfrom for UDP
        receivedMessage = data.decode()
        # Parse the message received from server and take corresponding actions
        if receivedMessage == "ERR":
            print("Authentication failed. Please try again.")
        elif receivedMessage == "OK":
            print("Welcome to BitTrickle!")
            print("Available commands are: get, lap, lpf, pub, sch, unp, xit")
            hb_sender = threading.Thread(target=send_heartbeat)
            hb_sender.daemon = True
            hb_sender.start()
            file_server_thread = threading.Thread(target=file_server)#for providing the files.
            file_server_thread.daemon = True
            file_server_thread.start()
            break
        elif receivedMessage == "REP":
            print("You have already logged in.")

    
    while True:
        cmd = input("> ")
        if re.match(r'^xit$',cmd):
            print("Goodbye!")
            message = cmd.upper()
            clientSocket.sendto(message.encode(),serverAddress)
            break

        elif re.match(r'^lap$', cmd):
            message = cmd.upper()
            clientSocket.sendto(message.encode(),serverAddress)
            data, server = clientSocket.recvfrom(1024)  # Use recvfrom for UDP
            receivedMessage = data.decode()
            names = receivedMessage.split(",")
            if len(names) <= 1:
                print("No active peers")
            else:
                print(f"{len(names)-1} peers active:")
                for i in names:
                    if(i!=username): print(i)

        elif re.match(r'^lpf$', cmd):
            message = cmd.upper()
            clientSocket.sendto(message.encode(),serverAddress)
            data, server = clientSocket.recvfrom(1024)  # Use recvfrom for UDP
            receivedMessage = data.decode()
            count = 0
            names = receivedMessage.split(",")
            if names[0] != "":    
                count = len(names)

            if count == 0:
                print("No files published")
            else:
                print(f"{len(names)} files published")
                for i in names:
                    if(i!=username): print(i)
        
        elif re.match(r"^pub (\S+)$", cmd):
            _,filename = cmd.split()
            subpath = username + f"/{filename}"
            if os.path.exists(subpath):
                clientSocket.sendto(cmd.encode(),serverAddress)
                data, server = clientSocket.recvfrom(1024)  # Use recvfrom for UDP
                receivedMessage = data.decode()
                if (receivedMessage == "OK"):
                    print("File published successfully")
            else:
                print("No such file in directory")
        
        elif re.match(r"^unp (\S+)$", cmd):
            clientSocket.sendto(cmd.encode(),serverAddress)
            data, server = clientSocket.recvfrom(1024)  # Use recvfrom for UDP
            receivedMessage = data.decode()
            if (receivedMessage == "OK"):
                print("File unpublished successfully")
            else:
                 print("File unpublication failed")

        elif re.match(r"^sch (\S+)$", cmd):
            clientSocket.sendto(cmd.encode(),serverAddress)
            data, server = clientSocket.recvfrom(1024)  # Use recvfrom for UDP
            receivedMessage = data.decode()
            if(receivedMessage == "ERR"):
                print("File not found")
            else:
                names = receivedMessage.split(",")
                print(f"{len(names)} files found")
                for i in names:
                    print(i)


        elif re.match(r"^get (\S+)$", cmd):
            clientSocket.sendto(cmd.encode(),serverAddress)
            data, server = clientSocket.recvfrom(1024)  # Use recvfrom for UDP
            _,filename = cmd.split()
            receivedMessage = data.decode()
            if (receivedMessage == "ERR"):
                 print("File not found")
            else:
                recv_port = int(receivedMessage)
                if recv_port == s_port:
                     print(f"{filename} downloaded successfully")
                else:
                    threading.Thread(target=receive_file, args=(recv_port,filename)).start()
                    time.sleep(1)
                    
           
        else:
           print("Not valid command") 


    # Close the socket
    clientSocket.close()
    exit(0)