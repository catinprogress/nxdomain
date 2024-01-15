import socket
import time

def main():
   query = "au\n"
   query2 = "!ADD"
   query3 = "new.host 3333\n"
   query4 = "co"
   query5 = "m\n"
   query6 = "!EXIT\n"
   try: 
      s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
      s.connect(('', 1024))
      s.settimeout(80)
      
      s.send(query.encode())
      time.sleep(2)
      print(s.recv(1024).decode(), flush=True)
      
      s.send(query2.encode())
      time.sleep(2)

      s.send(query3.encode())
      time.sleep(2)

      s.send(query4.encode())
      time.sleep(2)

      s.send(query5.encode())
      time.sleep(2)
      print(s.recv(1024).decode(), flush=True)

      s.send(query6.encode())
      time.sleep(2)
   except (InterruptedError, ConnectionRefusedError):
      print("FAILED TO CONNECT", flush=True)
   except TimeoutError:
      print("TIMEOUT", flush=True) 
   finally:
      s.close()

if __name__ == "__main__":
   main()