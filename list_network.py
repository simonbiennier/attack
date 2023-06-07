import os
import platform
import netifaces
import re


def extract_ip_address(line):
    #this gets the IP adress from the string output of 'arp -a'
    match = re.search(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', line)
    if match:
        return match.group(0)
    else:
        return None
   
def extract_mac_address(line):
    match = re.search(r'([0-9A-Fa-f]{2}[:-]){1,5}([0-9A-Fa-f]{2})', line)
    if match:
        return match.group(0)
    else:
        return None

def get_default_gateway():
    #gets the gateway (router) IP, this is a cross-platform system
    gateways = netifaces.gateways()
    default_gateway = gateways['default'][netifaces.AF_INET][0]
    return default_gateway

def main():
    print("Scanning network for potential targets...")
    #grab the gateway(router)
    gateway = get_default_gateway()
    print("gateway: ", gateway)

    #grab the other devices
    devices = []
    for device in os.popen('arp -a'): 
        if(extract_ip_address(device) != gateway):
            #we do not need the gateway
            devices.append(device)
        else:
            gateway = (gateway, extract_mac_address(device))
    for i in range(len(devices)):
        print("[", i, "]: ", devices[i])
    
    #target selection
    print("What follows is the not-so-legal part, continue at own risk!")
    response = -1
    while response not in range(0, len(devices)):
        response = int(input("select target on index [number]: "))
        if(response not in range(0, len(devices))):
            print("Invalid target you dumb-dumb!")
    target = devices[response]
    target = (extract_ip_address(target), extract_mac_address(target))
    print("Target ", target[0], " at ", target[1], " selected, proceeding with ARP poisoning using gateway ", gateway[0], " at ", gateway[1])

    #actual poisoning here

    
running_os = platform.system()
#match platform.system():
    #case "Linux":
if(running_os == "Linux"):
    print("Host OS is Linux, a-ok to proceed! continue?")
    #case "Windows":
elif(running_os == "Windows"):
    print("Host OS is Windows, should be fine. Proceed?")
    #case "Darwin":
elif(running_os == "Darwin"):
    print("Host OS is MacOS, [placeholder_name] cannot operate correctly in this setting, proceed anyway?")
    #case other:
else:
    print("Host OS not recognized.  [placeholder_name] cannot guarantee correct operation, proceed anyway?")
quit = False
while quit == False:
    response = input("[Y/N]: ")
    match response:
    if(response == "y" | "Y" | "Yes" | "yes"):
        #case "y" | "Y" | "Yes" | "yes":
        print("Proceeding!")
        main()
        quit = True
        #case "n" | "N" | "No" | "no":
    if(response == "n" | "N" | "No" | "no"):
        print("Stopping!")
        quit = True
        #case other:
    else:
        print("Unrecognized response, read this please!!!")
