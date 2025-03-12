#!/usr/bin/env python

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.link import TCLink
from mininet.node import OVSController
import subprocess

class CustomTopo(Topo):
    """Custom topology with 4 switches and 7 hosts"""
    
    def build(self, **_opts):
        # Add switches
        s1 = self.addSwitch('s1')
        s2 = self.addSwitch('s2')
        s3 = self.addSwitch('s3')
        s4 = self.addSwitch('s4')
        
        # Add hosts
        h1 = self.addHost('h1')
        h2 = self.addHost('h2')
        h3 = self.addHost('h3')
        h4 = self.addHost('h4')
        h5 = self.addHost('h5')
        h6 = self.addHost('h6')
        h7 = self.addHost('h7')
        
        # Add links
        self.addLink(h1, s1)
        self.addLink(h2, s1)
        self.addLink(h3, s2)
        self.addLink(h4, s3)
        self.addLink(h5, s3)
        self.addLink(h6, s4)
        self.addLink(h7, s4)
        
        # Add switch-to-switch links with custom parameters
        # We don't set bandwidth here because it will be set by setup_network function
        self.addLink(s1, s2)
        self.addLink(s2, s3)
        self.addLink(s3, s4)

def setup_network(bandwidth_s1_s2=10, bandwidth_s2_s3=10, bandwidth_s3_s4=10, loss_s2_s3=0):
    """Setup the network with custom parameters"""
    topo = CustomTopo()
    
    # Create the network with TCLink
    net = Mininet(topo=topo, controller=OVSController, link=TCLink)
    
    # Get switch objects
    s1, s2, s3, s4 = net.get('s1', 's2', 's3', 's4')
    
    # Configure links with custom parameters
    # Use r2q=100 to fix the quantum warning
    s1s2_link = net.linksBetween(s1, s2)[0]
    s2s3_link = net.linksBetween(s2, s3)[0]
    s3s4_link = net.linksBetween(s3, s4)[0]
    
    # Configure bandwidths (and r2q)
    s1s2_link.intf1.config(bw=bandwidth_s1_s2, r2q=100)
    s1s2_link.intf2.config(bw=bandwidth_s1_s2, r2q=100)
    
    s2s3_link.intf1.config(bw=bandwidth_s2_s3, r2q=100, loss=loss_s2_s3)
    s2s3_link.intf2.config(bw=bandwidth_s2_s3, r2q=100, loss=loss_s2_s3)
    
    s3s4_link.intf1.config(bw=bandwidth_s3_s4, r2q=100)
    s3s4_link.intf2.config(bw=bandwidth_s3_s4, r2q=100)
    
    return net