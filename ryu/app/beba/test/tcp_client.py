import socket,time
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(("10.0.0.2", 80))
s.send('HI')
time.sleep(20)
s.close()
