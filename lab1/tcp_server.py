import socket 
import threading 
from string import printable

bind_ip = "0.0.0.0" 
bind_port = 9001

COMMANDS = [b'ECHO', b'PING', b'SET', b'GET', b'QUIT']

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
server.bind((bind_ip, bind_port)) 
# maximum backlog of connections set to 5
server.listen(5) 

print(f"[+] Listening on port {bind_ip} : {bind_port}")                            

diz = {} 

#client handling thread
def handle_client(client_socket):   
    buffer = b''
    while True:
        user_input = client_socket.recv(1024)
        if not user_input:                     
            break
        buffer += user_input
        # assign all prompts to prompts and holds the rest of the recv in the buffer, ready to the next recv
        *prompts, buffer = buffer.split(b'\n')   
        
        for prompt in prompts:
            prompt = prompt.strip()
            if not prompt:               
                break
            parts = prompt.strip().split(b' ', 1)
            command = parts[0]

            # if parts not in printable:
            #     client_socket.send(b"ERR\n")
            if command == COMMANDS[1]:
                client_socket.send(b"PONG\n")

            elif command == COMMANDS[0]:
                data = parts[1] if len(parts) > 1 else b''
                #data = user_input.strip().split(b' ', 1)
                client_socket.send(data + b"\n")

            elif command == COMMANDS[-1]:
                client_socket.send(b"BYE\n")
                break

            elif command == COMMANDS[2]:
                if not b' ' in parts[1]:
                    client_socket.send(b"ERR\n")
                else:
                    key, value = parts[1].split(b' ', 1)
                    diz[key]=value
                    client_socket.send(b"OK\n")

            elif command == COMMANDS[3]:
                if len(parts)>1:
                    key = parts[1].split(b' ')[0]
                    if key in diz:
                        client_socket.send(diz[key]+b'\n')
                    else:
                        client_socket.send(b"NOT_FOUND\n")
                else:
                    client_socket.send(b"ERR\n")
            
            else:
                client_socket.send(b"ERR\n")

    client_socket.close()


while True: 
    client, addr = server.accept() 
    print(f"[+] Accepted connection from: {addr[0]}:{addr[1]}")
    #spin up our client thread to handle the incoming data 
    client_handler = threading.Thread(target=handle_client, args=(client,))
    client_handler.start()