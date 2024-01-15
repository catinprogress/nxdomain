import socket
import time

def main():
   query = "au\n"
   query2 = "!ADD new.host 3333\n"
   query3 = "!EXIT\n"
   try: 
      s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
      s.connect(('', 1024))
      s.settimeout(40)
      
      s.send(query.encode())
      time.sleep(2)
      print(s.recv(1024).decode(), flush=True)
      s.close()

      time.sleep(3)

      t = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
      t.connect(('', 1024))
      t.settimeout(40)
      
      t.send(query2.encode())
      time.sleep(2)
      
      t.send(query3.encode())
      time.sleep(2)
   except (InterruptedError, ConnectionRefusedError):
      print("FAILED TO CONNECT", flush=True)
   except TimeoutError:
      print("TIMEOUT", flush=True) 
   finally:
      s.close()

if __name__ == "__main__":
   main()