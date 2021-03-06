#!/usr/bin/env python

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.log import lg, info, setLogLevel
from mininet.util import dumpNodeConnections, quietRun, moveIntf
from mininet.cli import CLI
from mininet.node import Switch, Node

from subprocess import Popen, PIPE, check_output
from time import sleep, time
from multiprocessing import Process
from argparse import ArgumentParser

import util
from router import Router

def filter_routers(routers):
    return filter(lambda r : isinstance(r, Router), routers)


def getIP(hostname):
    h, s = hostname.replace('h', '').split('s')
    ip = '192.168.%s.%s/24' % (s, h)
    return ip


def getGateway(hostname):
    h, s = hostname.replace('h', '').split('s')
    gw = '192.168.%s.254' % s
    return gw


class Lab2Topo(Topo):
    def __init__(self):
        super(Lab2Topo, self).__init__()
        
        # routers
        R1 = self.addSwitch('R1', cls=Router)
        R2 = self.addSwitch('R2', cls=Router)

        # switches
        sws_A = [ self.addSwitch('LAN%d' % i) for i in range(1, 4) ]
        sws_B = [ self.addSwitch('LAN%d' % i) for i in range(8, 10) ]
        
        # hosts
        for sub in range(1, 4):
            for host in range(1, 3):
                self.addNode('h%ds%d' % (host, sub))

        for sub in range(8, 10):
            for host in range(1, 3):
                self.addNode('h%ds%d' % (host, sub))
        
        # links sw-router
        for idx, sw in enumerate(sws_A):
            self.addLink(sw, R1)

        for idx, sw in enumerate(sws_B):
            self.addLink(sw, R2)

        # links host-sw
        for sub in range(1, 4):
            for host in range(1, 3):
                self.addLink('h%ds%d' % (host, sub), 'LAN%d' % sub)

        for sub in range(8, 10):
            for host in range(1, 3):
                self.addLink('h%ds%d' % (host, sub), 'LAN%d' % sub)

        # link router-router
        self.addLink(R1, R2)
        

def main():
    util.init_clean_up()
    
    net = Mininet(topo=Lab2Topo())
    
    info( '*** Starting network\n')
    net.start()

    # init routers
    util.init_routers(filter_routers(net.switches))
        
    # init hosts
    info('\n')
    for host in net.hosts:
        host.cmd("ifconfig %s-eth0 %s" % (host.name, getIP(host.name)))
        host.cmd("route add default gw %s" % (getGateway(host.name)))

    # force ping on router -> hosts
    # nao funciona para pingall, fazer manual ping abaixo
    '''
    for host in net.hosts:
        net.getNodeByName("R1").cmdPrint("ping -c 5 %s" % getIP(host.name).split('/')[0])
        net.getNodeByName("R2").cmdPrint("ping -c 5 %s" % getIP(host.name).split('/')[0])
    '''
    
    CLI(net)
    
    net.stop()
    util.exit_clean_up()

'''
manual ping

R1 ping -c 1 h1s1
R1 ping -c 1 h1s2
R1 ping -c 1 h1s3
R1 ping -c 1 h2s1
R1 ping -c 1 h2s2
R1 ping -c 1 h2s3
R2 ping -c 1 h1s8
R2 ping -c 1 h2s8
R2 ping -c 1 h1s9
R2 ping -c 1 h2s9

'''


if __name__ == "__main__":
    setLogLevel( 'info' )
    main()

