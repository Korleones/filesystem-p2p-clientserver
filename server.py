from socket import *
import sys
import datetime
import threading
import time
import random


# 验证用户名和密码
def authenticate(username, password, credentials):
    return credentials.get(username) == password

#服务器日志输出
def log_message(action, username, port, response=None):
    # 获取当前时间
    now = datetime.datetime.now()
    # 格式化时间
    timestamp = now.strftime("%H:%M:%S.%f")[:-3]  # 只保留到毫秒
    
    # 根据操作类型构造日志消息
    if action == "recv":
        log_message = f"{timestamp}: {port}: Received {response} from {username}"
    elif action == "sent":
        log_message = f"{timestamp}: {port}: Sent {response} to {username}"
    # 打印日志消息
    print(log_message)

#客户端消息处理
def handle_client(message,clientAddress):
    # Handle login message (assuming message format is "auth username password")
    global logged_in_users
    global public_files
    global user_port_dic

    _ ,port = clientAddress
    if message.startswith('auth'):
        parts = message.split()
        response = "AUTH"
        if len(parts) == 3:
            _ , username, password = message.split()  # 拆分消息

            log_message("recv",username,port,response)
            for p in logged_in_users.keys():
                if logged_in_users[p][0] == username:
                    response = "REP"
                    log_message("sent",username,port,response)
                    serverSocket.sendto(response.encode(), clientAddress)
                    return


            if authenticate(username, password, credentials):
                response = "OK"
                info = [username,port,True] #(用户名，端口，在线状态)
                with lock:
                    logged_in_users[port] = info
                    user_port_dic[username] = port 
                
            else:
                response = "ERR"

            log_message("sent",username,port,response)

            serverSocket.sendto(response.encode(), clientAddress)
         
        else:
            response = "ERR"
            log_message("sent",username,port,response)
            serverSocket.sendto(response.encode(), clientAddress)

    elif message == "HBT":
        with lock:
            if port in logged_in_users.keys():
                logged_in_users[port][2] = True  # Mark client as active
        if(port in logged_in_users.keys()):
            username = logged_in_users[port][0]
            log_message("recv",username,port,"HBT")

    elif message == "LAP":
        if(port in logged_in_users.keys()):
            username = logged_in_users[port][0]
            log_message("recv",username,port,"LAP")
            names = []
            with lock:
                for port in logged_in_users.keys():
                    names.append(logged_in_users[port][0])
            message = ','.join(names)
            serverSocket.sendto(message.encode(),clientAddress)
            log_message("sent",username,port,"OK")


    elif message == "LPF":
        if(port in logged_in_users.keys()):
            username = logged_in_users[port][0]
            log_message("recv",username,port,"LPF")
            names = []
            response = ""
            if len(list(public_files.keys())) != 0:
                with lock:
                    for file in public_files.keys():
                        names.append(file)
                    response = ','.join(names)
            serverSocket.sendto(response.encode(),clientAddress)
            log_message("sent",username,port,"OK")


    elif message == "XIT":
        if(port in logged_in_users.keys()):
            with lock:
                for peer in list(logged_in_users.keys()):
                    if logged_in_users[peer][1] == port:
                        print(f"Removing inactive peer: {peer}")
                        del user_port_dic[logged_in_users[peer][0]]
                        del logged_in_users[peer]
                    
    elif message[:3]== "pub":
        if(port in logged_in_users.keys()):
            username = logged_in_users[port][0]
            log_message("recv",username,port,"PUB")
            _, filename = message.split()
            with lock:
                if(filename in public_files.keys()):
                    publisher = public_files[filename]
                    if(username not in publisher):
                        publisher.append(username)
                    public_files[filename] = publisher
                else:
                    public_files[filename] = [username]
            response = "OK"
            serverSocket.sendto(response.encode(),clientAddress)
            log_message("sent",username,port,"OK")
        

    elif message[:3]== "unp":
        if(port in logged_in_users.keys()):
            username = logged_in_users[port][0]
            log_message("recv",username,port,"UNP")
            _, filename = message.split()
            with lock:
                if(len(public_files.keys()) == 0 or (filename not in public_files.keys()) or (username not in public_files[filename])):
                    response = "ERR"
                    serverSocket.sendto(response.encode(),clientAddress)
                    log_message("sent",username,port,"ERR")
                else:
                    public_files[filename].remove(username)
                    if(len(public_files[filename]) == 0):
                        del(public_files[filename])
                    response = "OK"
                    serverSocket.sendto(response.encode(),clientAddress)
                    log_message("sent",username,port,"OK")


    elif message[:3]== "sch":
        if(port in logged_in_users.keys()):
            username = logged_in_users[port][0]
            log_message("recv",username,port,"SCH")
            _, filename = message.split()
            names = []
            with lock:
                if(len(public_files.keys()) == 0):
                    response = "ERR"
                    serverSocket.sendto(response.encode(),clientAddress)
                    log_message("sent",username,port,"ERR")
                    return

                for i in public_files.keys():
                    if (filename in i) is True:
                        if(username not in public_files[i]):
                            names.append(i)         
                        
                if len(names) == 0:
                    response = "ERR"
                    serverSocket.sendto(response.encode(),clientAddress)
                    log_message("sent",username,port,"ERR")
                else:
                    message = ",".join(names)
                    serverSocket.sendto(message.encode(),clientAddress)
                    log_message("sent",username,port,"OK")
                


    elif message[:3]== "get":
        if(port in logged_in_users.keys()):
            username = logged_in_users[port][0]
            log_message("recv",username,port,"GET")
            _, filename = message.split()
            with lock:
                if(len(public_files.keys()) == 0 or filename not in public_files.keys()):
                    response = "ERR"
                    serverSocket.sendto(response.encode(),clientAddress)
                    log_message("sent",username,port,"ERR")
                    return
                
                if filename in public_files.keys():
                    count = len(public_files[filename])
                    numbers = range(0,count)
                    
                    number = random.choice(numbers) #randomly find a publisher to download.
    
                    
                    des_username = public_files[filename][number]
                    if(des_username not in user_port_dic.keys()):
                        response = "ERR"
                        serverSocket.sendto(response.encode(),clientAddress)
                        log_message("sent",username,port,"ERR")
                        return
                    c_port = user_port_dic[des_username]
                    s_port = c_port_to_s_port[c_port]
                    if c_port not in  logged_in_users.keys(): 
                        response = "ERR"
                        serverSocket.sendto(response.encode(),clientAddress)
                        log_message("sent",username,port,"ERR")
                    else:
                        serverSocket.sendto(str(s_port).encode(),clientAddress) #返回下载人的端口 要转换一下，而且要找在线的人
                        log_message("sent",username,port,"OK")

    elif message[:3]== "CSP":
        if(port in logged_in_users.keys()):
            username = logged_in_users[port][0]
            log_message("recv",username,port,"CSP")
            _, s_port = message.split()
            c_port_to_s_port[port] = s_port
            

#heartbeat monitor
def monitor_peers():
    global logged_in_users
    while True:
        time.sleep(3)  # Check every 3 seconds
        with lock:
            # Set all statuses to False initially, then remove if still False in the next check
            for peer in list(logged_in_users.keys()):
                if logged_in_users[peer][2] == False:
                    print(f"Removing inactive peer: {peer}")
                    del user_port_dic[logged_in_users[peer][0]]
                    del logged_in_users[peer]
                    
                else:
                    # Reset the status to False, waiting for next heartbeat
                    logged_in_users[peer][2] = False





#main func
if __name__ == "__main__":
    credentials = {}
    public_files = {}
    user_port_dic = {}
    c_port_to_s_port = {}
    logged_in_users = {}
    lock = threading.Lock()  # For thread-safe access to active_peers
    with open("server/credentials.txt", 'r') as file:
        for line in file:
            if len(line.split()) == 0: continue
            username, password = line.split()  
            credentials[username] = password
        if len(sys.argv) != 2:
            print("\n===== Error usage, python3 server.py SERVER_PORT ======\n")
            exit(0)

    serverHost = "127.0.0.1"
    serverPort = int(sys.argv[1])
    serverAddress = (serverHost, serverPort)

    # define socket for the server side and bind address
    serverSocket = socket(AF_INET, SOCK_DGRAM)
    serverSocket.bind(serverAddress)

    print("\n===== Server is running =====")
    print("===== Waiting for connection requests from clients... =====")

    # Dictionary to store user login status

    

    hb_monitor = threading.Thread(target=monitor_peers)
    hb_monitor.daemon = True
    hb_monitor.start()
    
    while True:
        # receive message from the client
        data, clientAddress = serverSocket.recvfrom(1024)  # receive data from clients
        message = data.decode()
        handle_client(message,clientAddress)
        

