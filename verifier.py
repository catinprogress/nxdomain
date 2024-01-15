
from sys import argv
import launcher
from pathlib import Path
import recursor
import server

def valid_root(lines: list):
    root_dict = {}
    for line in lines:
        if "." in line:
            return 0
        get_domains = line.strip("\n").split(",")
        if len(get_domains) == 2 and recursor.check_alphanumeric(get_domains[0]):
            domain = get_domains[0]
            port = get_domains[1]

            try:
                recursor.port_in_range(int(port))
            except ValueError:
                return 0
                
            if root_dict.get(domain) != None and root_dict.get(domain) != port: #same host name, different port
                return 0
            elif root_dict.get(domain) == None: #host name doesn't exist
                root_dict[domain] = port
        else:
            return 0
    return root_dict

def valid_tld(lines: list):
    tld_dict = {}
    for line in lines:
        get_domains = line.strip("\n").split(",", 1)
        if len(get_domains) == 2:
            domain = get_domains[0]
            port = get_domains[1]

            if len(domain.split(".")) == 2 and server.check_valid_hostname(domain):
                try:
                    recursor.port_in_range(int(port))
                except ValueError:
                    return 0
                
                if tld_dict.get(domain) != None and tld_dict.get(domain) != port: 
                    return 0
                elif tld_dict.get(domain) == None:
                    tld_dict[domain] = port
            else:
                return 0
        else:
            return 0
    return tld_dict

def valid_auth(lines: list): 
    auth_domains = []
    auth_dict = {} 
    for line in lines:
        get_domains = line.strip("\n").split(",")
        if len(get_domains) == 2 and recursor.valid_hostname(get_domains[0]):
            domain = get_domains[0]
            port = get_domains[1]

            try:
                recursor.port_in_range(int(port))
            except ValueError:
                return 0

            if auth_dict.get(domain) != None and auth_dict.get(domain) != port: #check that same host name has same port
                return 0
            elif auth_dict.get(domain) == None: #key: auth domain, value: port it listens to
                auth_dict[domain] = port

            if not (line.strip("\n") in auth_domains):
                auth_domains.append(line.strip("\n")) #list of valid lines in config file
            else:
                return 0
        else:
            return 0
    return auth_domains, auth_dict

def main(args: list[str]) -> None:
    if len(args) != 2: 
        print("invalid arguments", flush=True)
        return
    
    try:
        master = open(args[0], "r")
        lines = master.readlines()
        port_master = lines[0].strip("\n")
        recursor.port_in_range(int(port_master))
    except (FileNotFoundError, IsADirectoryError, ValueError):
        print("invalid master", flush=True)
        return    

    if launcher.check_valid_master(lines[1:]) == 0:
        print("invalid master", flush=True)
        return
   
    path = Path(args[1])
    if not path.is_dir() or not path.exists():
        print("singles io error", flush=True)
        return
    
    configs = [] #list of config files to verify
    master_domains = lines[1:]

    for file in path.iterdir():
        if file.is_file():
            configs.append(file)
        else:
            print("invalid single", flush=True)
            return

#get all auth configs and check that they map to domains in master
    count = 0 #count all resolved auth domains and ensure that it is the same length as records in master
    to_remove = []
    existing_ports = [] 
    valid_tlds = {}
    for current in configs: #find auth files in config and verify that they are equivalent to master
        try:
           f = Path(current)
        except (FileNotFoundError, IsADirectoryError):
            print("invalid single", flush=True)
            return
            
        lines_2 = f.open().readlines()
        port = lines_2[0].strip("\n")

        if port in existing_ports: #check that port of each single file is not the same
            print("neq", flush=True)
            return

        if valid_auth(lines_2[1:]) != 0:
            auth_domains = valid_auth(lines_2[1:])[0] 
            auth_dict = valid_auth(lines_2[1:])[1] 

            for line in auth_domains: #check that all lines in auth config file match with master
                if not ((line in master_domains) or (line + "\n" in master_domains)):
                    print("neq", flush=True)
                    return
                count += 1
            
            for domain in auth_dict.keys():
                partial_tld = domain.split(".")[-2] + "." + domain.split(".")[-1]
                if not (partial_tld in valid_tlds.keys()):
                    valid_tlds[partial_tld] = port #key: valid tld from valid auth config file, value: port of auth config file
            
            to_remove.append(current) #auth configs to remove from configs list
            existing_ports.append(port)
   
    for file in to_remove: #prevent re-reading same files in directory
        configs.remove(file)
    to_remove.clear()

    if count != len(master_domains) or len(configs) == 0:
        print("invalid single", flush=True)
        return

 #get all tld configs and check that they map to domains in auth   
    valid_roots = {}
    count = 0
    for current in configs: 
        try:
           f = Path(current)
        except (FileNotFoundError, IsADirectoryError):
            print("invalid single", flush=True)
            return
            
        lines_2 = f.open().readlines()
        port = lines_2[0].strip("\n")

        if port in existing_ports:
            print("neq", flush=True)
            return

        if valid_tld(lines_2[1:]) != 0: #valid config file
            tld_dict = valid_tld(lines_2[1:]) #key: tld domain, value: port that it listens to 

            for partial in tld_dict.keys(): #check that all ports in tld file map to the correct auth server
                if valid_tlds.get(partial) != tld_dict.get(partial):
                    print("neq", flush=True)
                    return
                count += 1
                
                partial_root = partial.split(".")[-1]
                if not (partial_root in valid_roots.keys()):
                    valid_roots[partial_root] = port #all roots should map to the correct tld server port

            to_remove.append(current)
            existing_ports.append(port)

    for file in to_remove:
        configs.remove(file)
    to_remove.clear()

    if count != len(valid_tlds.values()) or len(configs) != 1:
        print("invalid single", flush=True)
        return
    
 #check final file is root config and check that all root partial domains can be resolved to an existing tld server  
    file = configs[0]
    count = 0
    try:
        f = Path(file)
    except (FileNotFoundError, IsADirectoryError):
        print("invalid single", flush=True)
        return
            
    lines_2 = f.open().readlines()
    port = lines_2[0].strip("\n")

    if port in existing_ports:
        print("neq", flush=True)
        return

    if valid_root(lines_2[1:]) != 0:
        root_dict = valid_root(lines_2[1:]) #key: root domain, value: port that it listens to

        for partial in root_dict.keys(): #check that all the retrieved domains map to the correct tld server
            if valid_roots.get(partial) != root_dict.get(partial):
                print("neq", flush=True)
                return
            count += 1
    else:
        print("invalid single", flush=True)
        return
                
    if count != (len(valid_roots.values())):
        print("neq", flush=True)
    else:
        print("eq", flush=True)

if __name__ == "__main__":
    main(argv[1:])
