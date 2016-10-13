#!/usr/bin/python

import os,subprocess,time,sys
from mininet.net import Mininet
from mininet.topo import SingleSwitchTopo
from mininet.node import UserSwitch,RemoteController
from mininet.term import makeTerm

if os.geteuid() != 0:
    exit("You need to have root privileges to run this script")

# Kill Mininet and/or Ryu
os.system("sudo mn -c 2> /dev/null")
os.system("kill -9 $(pidof -x ryu-manager) 2> /dev/null")

print 'Starting Ryu controller'
if len(sys.argv)>1 and sys.argv[1]=='verbose':
	os.system('ryu-manager --verbose ../portknock.py &')
else:
	os.system('ryu-manager ../portknock.py 2> /dev/null &')

print 'Starting Mininet'
net = Mininet(topo=SingleSwitchTopo(2),switch=UserSwitch,controller=RemoteController,cleanup=True,autoSetMacs=True,listenPort=6634)
net.start()

time.sleep(5)

if len(sys.argv)>1 and sys.argv[1]=='verbose':
	os.system('sudo dpctl tcp:127.0.0.1:6634 -c stats-flow')
	os.system('sudo dpctl tcp:127.0.0.1:6634 -c stats-state')

# Start Server @h2 on port 22
net['h2'].cmd('nc -lu 22 &')

# h1 attempts a wrong sequence and then the correct sequence
net['h1'].cmd('(echo "HI!" | ../test_port_knocking.sh) &')

out = ''
attempts = 0
while 'ESTABLISHED' not in out and attempts<15:
	out = net['h2'].cmd('(netstat -an | grep udp | grep 22)')
	print 'Waiting %d seconds...' % (15-attempts)
	attempts += 1
	time.sleep(1)

if 'ESTABLISHED' in out:
	print '\x1b[32mSUCCESS!\x1b[0m'
else:
	print '\x1b[31mFAIL\x1b[0m'
	if len(sys.argv)>1 and sys.argv[1]=='verbose':
	        os.system('sudo dpctl tcp:127.0.0.1:6634 -c stats-flow')
	        os.system('sudo dpctl tcp:127.0.0.1:6634 -c stats-state')
	exit(1)

# Kill Mininet and/or Ryu
net.stop()
os.system("sudo mn -c 2> /dev/null")
os.system("kill -9 $(pidof -x ryu-manager) 2> /dev/null")
