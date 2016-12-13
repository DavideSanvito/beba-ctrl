#!/usr/bin/python

import os,subprocess,time,sys
import distutils.spawn
from mininet.net import Mininet
from mininet.topo import SingleSwitchTopo
from mininet.node import UserSwitch,RemoteController
from mininet.term import makeTerm
from beba import BebaSwitchDbg,BebaHost

if os.geteuid() != 0:
    exit("You need to have root privileges to run this script")

# Kill Mininet and/or Ryu
os.system("sudo mn -c 2> /dev/null")
os.system("kill -9 $(pidof -x ryu-manager) 2> /dev/null")

print 'Starting Ryu controller'

if len(sys.argv)>1 and sys.argv[1]=='verbose':
	os.system('ryu-manager --verbose ../forwarding_consistency_1_to_many.py &')
else:
	os.system('ryu-manager ../forwarding_consistency_1_to_many.py 2> /dev/null &')

print 'Starting Mininet'
net = Mininet(topo=SingleSwitchTopo(4),switch=BebaSwitchDbg,host=BebaHost,controller=RemoteController,cleanup=True,autoSetMacs=True,listenPort=6634)
net.start()

time.sleep(3)

for i in range(1,5):
	os.system('sudo ethtool --offload s1-eth'+str(i)+' gso off tso off gro off')

if len(sys.argv)>1 and sys.argv[1]=='verbose':
	os.system('sudo dpctl tcp:127.0.0.1:6634 -c stats-flow')
	os.system('sudo dpctl tcp:127.0.0.1:6634 -c stats-state')

print 'Starting Echo Servers on h2, h3 and h4'

for h in [2,3,4]:
	net['h%d' % h].cmd('python ../echo_server.py %d00 &' %h)
	#net['h%d' % h].cmd('ncat -e /bin/cat -k -l %d00 &' %h)

time.sleep(3)

CONN_NUM = 20
print 'Starting %d TCP connections from h1' %CONN_NUM

for n in range(CONN_NUM):
	net['h1'].cmd('(echo "HI!" | nc -q -1 10.0.0.2 80) &')

time.sleep(5)

print '[h1]'
os.system('cat /tmp/tcpdumplog.h1')
print '[h2]'
os.system('cat /tmp/tcpdumplog.h2')


established = {}
syn_recv = {}
for h in [2,3,4]:
	out = net['h%d' % h].cmd('(netstat -an | grep tcp | grep 10.0.0.%d:%d00)' % (h,h))
	print '[h'+str(h)+'] '
	print net['h%d' % h].cmd('(netstat -an | grep tcp )')
	established[h]=out.count("ESTABLISHED")
	syn_recv[h]=out.count("SYN_RECV")

if sum(syn_recv.values()) != 0:
	print '\x1b[31mFAIL\x1b[0m: some connections are still in SYN_RECV (maybe SYN and ACK have not been consistently forwarded!)'
	if len(sys.argv)>1 and sys.argv[1]=='verbose':
	        os.system('sudo dpctl tcp:127.0.0.1:6634 -c stats-flow')
		os.system('sudo dpctl tcp:127.0.0.1:6634 -c stats-state')
	exit(1)
elif sum(established.values()) != CONN_NUM:
	print '\x1b[31mFAIL\x1b[0m: not all the %d connections have been ESTABLISHED' % CONN_NUM
	if len(sys.argv)>1 and sys.argv[1]=='verbose':
	        os.system('sudo dpctl tcp:127.0.0.1:6634 -c stats-flow')
		os.system('sudo dpctl tcp:127.0.0.1:6634 -c stats-state')
	exit(1)
elif 0 in established.values():
	print '\x1b[31mFAIL\x1b[0m: not all the servers have been selected'
	if len(sys.argv)>1 and sys.argv[1]=='verbose':
	        os.system('sudo dpctl tcp:127.0.0.1:6634 -c stats-flow')
		os.system('sudo dpctl tcp:127.0.0.1:6634 -c stats-state')
	exit(1)
else:
	print '\x1b[32mSUCCESS!\x1b[0m'

# Kill Mininet and/or Ryu
net.stop()
os.system("sudo mn -c 2> /dev/null")
os.system("kill -9 $(pidof -x ryu-manager) 2> /dev/null")
