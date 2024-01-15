from sys import argv
import socket
import recursor

#check valid commands return values
#0 = invalid
#1 = add
#2 = del
#3 = exit
#4 = NXDOMAIN

def check_valid_command(command: str):
    if command.startswith("!"):
        ls = command.split(" ")
        if len(ls) == 2:
            if ls[0] == "!DEL":
                return 2
        elif len(ls) == 3:
            if ls[0] == "!ADD":
                return 1
        elif len(ls) == 1:
            if ls[0] == "!EXIT":
                return 3
    else: #invalid hostname
        return 4
    return 0 #incomplete command format


def check_valid_hostname(domain: str): 
    test = domain.strip("\n").split(".")
    if len(test) == 2: #partial domain B.A
        return (recursor.check_alphanumeric(test[0]) and recursor.check_alphanumeric(test[1]))
    elif len(test) >= 3: #full domain C.B.A
        return recursor.valid_hostname(domain.strip("\n"))
    elif len(test) == 1: #partial domain A
        return recursor.check_alphanumeric(domain.strip("\n"))

def add(host: str, port: str, domains: dict):
    if not check_valid_hostname(host):
        return
    
    try:
        recursor.port_in_range(int(port)) #check if invalid port
    except ValueError:
        return

    if (domains.get(host) == port) or (port in domains.values()): #already recorded domain,port or port already exists
        return
    else: 
        domains[host] = port #add host, port to record
            
def delete(record: str, domains: dict):
    if not check_valid_hostname(record):
        return None
 
    return domains.pop(record, None) #return none if the hostname doesn't already exist
    

def main(args: list[str]) -> None:
    if len(args) != 1:
        print("INVALID ARGUMENTS", flush=True)
        return
    
    try:
        config_file = open(args[0], "r")
    except (FileNotFoundError, IsADirectoryError):
        print("INVALID CONFIGURATION", flush=True)
        return

    lines = config_file.readlines()
    domains = {} #record of hosts and their port in config file

    i = 0
    valid_config = False
    while i < len(lines):
        if i == 0: #check if first line is port number
            test = lines[i].strip("\n")
            try:
                PORT = int(test) #check if port is an integer value
                recursor.port_in_range(PORT)
                valid_config = True
            except ValueError:
                valid_config = False
                break           
        else: #check if all other lines are valid format
            domain = lines[i].split(",")
            if len(domain) == 2 and check_valid_hostname(domain[0]):
                try:
                    recursor.port_in_range(int(domain[1].strip("\n")))
                except ValueError:
                    valid_config = False
                    break
                
                if domains.get(domain[0]) != None and domains.get(domain[0]) != domain[1].strip("\n"): #if domain exists but contradicting port number
                    valid_config = False
                    break
                else:
                    domains[domain[0]] = domain[1].strip("\n") #domain --> key: hostname, value: port number
                    valid_config = True
            else:
                valid_config = False
                break
        i += 1
    
    if not valid_config:
        print("INVALID CONFIGURATION", flush=True)
        return      
    
    buff = ""

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('', PORT))
    s.listen(5)
    client, address = s.accept()
    while True:
        query = client.recv(1024).decode()
        if not query: #make sure that only one connection is accepted at a time
            client.close()
            buff = ""
            client, address = s.accept()
            continue
        buff += query #buffer of queries

        if "\n" in buff: #valid query
            current_command = buff.split("\n")[0]
        else:
            continue

        port = domains.get(current_command)
        host = current_command

        if port == None: #key doesn't exist
            to_send = 'NXDOMAIN\n'
            port = 'NXDOMAIN'
        else:
            to_send = port + "\n"
        
        if to_send == "NXDOMAIN\n": #check if valid command
            check = check_valid_command(current_command)
            if check == 0: #invalid command format
                to_send = ""
                print("INVALID", flush=True)
            elif check == 1: #add - add hostname, port to record of the server
                to_send = ""
                add(current_command.split(" ")[1], current_command.split(" ")[2], domains)
            elif check == 2: #del - remove hostname from record of the server
                to_send = ""
                to_del = current_command.split(" ")
                delete(to_del[1], domains)
            elif check == 3: #exit - shuts down server
                buff = ""
                client.close()
                s.close()
                exit()              
            
        if len(to_send) > 0:
            client.sendall(to_send.encode())
            print("resolve " + host + " to " + port.strip("\n"), flush=True)

        buff = buff.replace(current_command + "\n", "", 1)  #remove resolved query

if __name__ == "__main__":
    main(argv[1:])
