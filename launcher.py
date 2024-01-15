
from sys import argv
from pathlib import Path
import recursor
import random

def check_valid_master(lines: list):
    existing = {}
    for current in lines:
        get_domain = current.strip("\n").split(",")
        if len(get_domain) == 2 and recursor.valid_hostname(get_domain[0]):
            domain = get_domain[0] #current domain to check
            port = get_domain[1]
            try: 
                recursor.port_in_range(int(port))
            except ValueError:
                return 0
                
            if existing.get(domain) != None and existing.get(domain) != port: #domain already exists but it has different port
                return 0
            elif existing.get(domain) == None: #if domain exists, don't change port name; else add to existing domains/ports
                existing[domain] = port
            else:
                return 0  
        else:
            return 0
    return 1


def generate_tld(tld_strings):
    tld_dict = {}
    for domain in tld_strings:
        get_domain = domain.split(",")
        root_domain = get_domain[0].split(".")[-1]

        if tld_dict.get(root_domain) == None: #root domain doesn't already exist
            tld_dict[root_domain] = [domain] #key: root partial domain, value: list of corresponding tld domains
        else:
            ls = tld_dict.get(root_domain)
            ls.append(domain)
            tld_dict[root_domain] = ls
 
    return tld_dict
       
def generate_auth(lines: list):
    auth_dict = {}
    for domain in lines: #current domain
        get_domain = domain.strip("\n").split(",")
        to_generate = get_domain[0].split(".") 
        tld_domain = to_generate[-2] + "." + to_generate[-1] #tld partial domain
        
        if auth_dict.get(tld_domain) == None: #tld domain doesn't already exist
            auth_dict[tld_domain] = [domain.strip("\n")] #key: tld domain, value: list of corresponding auth domains
        else:
            ls = auth_dict.get(tld_domain) #add domain to list of existing domains that map to tld domain
            ls.append(domain.strip("\n"))
            auth_dict[tld_domain] = ls

    return auth_dict
        

def main(args: list[str]) -> None:
    if len(args) != 2:
        print("INVALID ARGUMENTS", flush=True)
        return
    
    try:
        master_file = open(args[0], "r")
    except (FileNotFoundError, IsADirectoryError):
        print("INVALID MASTER", flush=True)
        return
    
    lines = master_file.readlines()
    master_port = lines[0].strip("\n")

    try: 
        recursor.port_in_range(int(master_port))
    except ValueError:
        print("INVALID MASTER", flush=True)
        return

    if (len(lines) > 21505) or check_valid_master(lines[1:]) == 0:
        print("INVALID MASTER", flush=True)
        return
     
    path = Path(args[1])
    if not path.is_dir() or not path.exists():
        print("NON-WRITABLE SINGLE DIR", flush=True)
        return

    domains_to_config = lines[1:]
    existing_ports = [int(master_port)]

    auth_dict = generate_auth(domains_to_config) #key: tld domain, value: list of auth domains that map to key
    tld_strings = []

    for key in auth_dict.keys(): #generate auth config file 
        file_name = "auth-" + key.replace(".", "-") + ".conf"
        
        file_path = Path(args[1] + "/" + file_name)
        file_path.touch(exist_ok= True) #create new file in existing directory
        f = open(file_path, "w")
        
        ls = auth_dict.get(key) #get list of auth hostnames

        while True:
            port = random.randint(1024, 65535)
            if not (port in existing_ports): #create unique port
                existing_ports.append(port)
                break

        f.write(str(port) + "\n") #first line of file
        for domain in ls:
            if ls[-1] != domain: #if not at end of list, add a new line in file
                f.write(domain + "\n")
            else:
                f.write(domain)
        
        f.close()
        #path.touch #create file

        tld_strings.append(key + "," + str(port)) #list of tld domains and the ports they listen to
    
    tld_dict = generate_tld(tld_strings) #key: root domain, value: list of tld domains that map to key
    root_strings = []

    for key in tld_dict.keys(): #generate tld config files
        file_name = "tld-" + key + ".conf"
        
        file_path = Path(args[1] + "/" + file_name)
        file_path.touch(exist_ok= True)
        f = open(file_path, "w")
        
        ls = tld_dict.get(key)

        while True:
            port = random.randint(1024, 65535)
            if not (port in existing_ports):
                existing_ports.append(port)
                break

        f.write(str(port) + "\n")
        for domain in ls:
            if ls[-1] != domain:
                f.write(domain + "\n")
            else:
                f.write(domain)
        
        f.close()

        root_strings.append(key + "," + str(port))

    file_name = "root.conf"
    file_path = Path(args[1] + "/" + file_name)
    file_path.touch(exist_ok= True)
    f = open(file_path, "w")
    
    while True:
        port = random.randint(1024, 65535)
        if not (port in existing_ports):
            break

    f.write(str(port) + "\n")
    for line in root_strings:
        if root_strings[-1] != line:
            f.write(line + "\n")
        else:
            f.write(line)

    f.close()

if __name__ == "__main__":
    main(argv[1:])
