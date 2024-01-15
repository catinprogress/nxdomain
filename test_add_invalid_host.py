import socket
import time

def main():
   query = "!ADD sublime.com..au 2345\n"
   query2 = "!EXIT\n"
   try: 
      s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
      s.connect(('', 1024))
      s.settimeout(30)
      
      s.send(query.encode())
      time.sleep(2)
      
      s.send(query2.encode())
      time.sleep(2)
   except (InterruptedError, ConnectionRefusedError):
      print("FAILED TO CONNECT", flush=True)
   except TimeoutError:
      print("TIMEOUT", flush=True) 
   finally:
      s.close()

if __name__ == "__main__":
   main()