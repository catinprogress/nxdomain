"""
Write code for your recursor here.

You may import library modules allowed by the specs, as well as your own other modules.
"""
from sys import argv
import socket
import time

def port_in_range(port: int) -> bool:
    if port in range(1024, 65536):
        return True
    raise ValueError
        
def check_alphanumeric(name: str) -> bool:
    if "-" in name:  
        remove_hyphen = name.split("-")
        is_valid = False
        for check in remove_hyphen:
            if check.isalnum() or (len(check) == 0):
                is_valid = True
            else:
                is_valid = False
                break        
        if is_valid:
            return True       
    elif name.isalnum():
        return True
    
    return False

def valid_hostname(test: str) -> bool: #verify C.B.A format
    name = test.split(".")
         
    if len(name) >= 3:
        a = name[-1]
        b = name[-2]
        c = "".join(name[:-2])

        if c.startswith(".") or c.endswith("."):
            return False

        A_is_valid = check_alphanumeric(a)
        B_is_valid = check_alphanumeric(b)

        C_is_valid = False
        for check in name[:-2]:
            if check_alphanumeric(check):
                C_is_valid = True
            else:
                C_is_valid = False
                break
        
        if A_is_valid and B_is_valid and C_is_valid:
            return True   
    
    return False

def main(args: list[str]) -> None:
    if len(args) != 2:
        print("INVALID ARGUMENTS", flush=True)
        return
    
    try:
        TTL = float(args[1])
    except ValueError:
        print("INVALID ARGUMENTS", flush=True)
        return
    
    root_port = args[0]
    try:       
        port_in_range(int(root_port))
    except ValueError:
        print("INVALID ARGUMENTS", flush=True)
        return
    
    while True:
        try:
            domain = input()
        except EOFError:
            return
        
        if not valid_hostname(domain):
            print("INVALID", flush=True)
            continue
        
        identifiers = domain.split(".")

        root_query = identifiers[-1] + "\n"
        tld_query = identifiers[-2] + "." + identifiers[-1] + "\n"
        authoritative_query = domain + "\n"
        
        try: 
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
            s.settimeout(TTL)
            s.connect(('', int(root_port)))
            start = time.time()

            s.sendall(root_query.encode())
            response = s.recv(1024).decode()
            s.close()
            end = time.time()
            
            if response.strip("\n") == "NXDOMAIN":
                print("NXDOMAIN", flush=True)
                continue
            tld_port = int(response.strip("\n"))
        except (InterruptedError, ConnectionRefusedError):
            s.close()
            print("FAILED TO CONNECT TO ROOT", flush=True)
            exit()
        except TimeoutError:
            s.close()
            print("NXDOMAIN", flush=True) 
            continue

        new_TTL = end - start

        try:
            t = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            t.settimeout(new_TTL) 
            t.connect(('', tld_port))  
            start = time.time()
            
            t.sendall(tld_query.encode())
            response = t.recv(1024).decode()
            t.close()
            end = time.time()
            if response.strip("\n") == "NXDOMAIN":
                print("NXDOMAIN", flush=True)
                continue
            authoritative_port = int(response.strip("\n"))      
        except (InterruptedError, ConnectionRefusedError):
            t.close()
            print("FAILED TO CONNECT TO TLD", flush=True)
            exit()
        except TimeoutError:
            t.close()
            print("NXDOMAIN", flush=True) 
            continue

        new_TTL = end - start

        try:
            a = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
            a.settimeout(new_TTL)
            a.connect(('', authoritative_port))
            start = time.time()
            
            a.sendall(authoritative_query.encode())
            response = a.recv(1024).decode()
            a.close()
            end = time.time()
            
            print(response.strip("\n"), flush=True)
            if response.strip("\n") == "NXDOMAIN":
                continue        
        except (InterruptedError, ConnectionRefusedError):
            a.close()
            print("FAILED TO CONNECT TO AUTH", flush=True)
            exit()
        except TimeoutError:
            a.close()
            print("NXDOMAIN", flush=True)
            

if __name__ == "__main__":
    main(argv[1:])
