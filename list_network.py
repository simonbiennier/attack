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
    for device in devices:
        print(device)

match platform.system():
    case "Linux":
        print("Host OS is Linux, a-ok to proceed! continue?")
    case "Windows":
        print("Host OS is Windows, should be fine. Proceed?")
    case "Darwin":
        print("Host OS is MacOS, [placeholder_name] cannot operate correctly in this setting, proceed anyway?")
    case other:
        print("Host OS not recognized.  [placeholder_name] cannot guarantee correct operation, proceed anyway?")
quit = False
while quit == False:
    response = input("[Y/N]: ")
    match response:
        case "y" | "Y" | "Yes" | "yes":
            print("Proceeding!")
            main()
            quit = True
        case "n" | "N" | "No" | "no":
            print("Stopping!")
            quit = True
        case other:
            print("Unrecognized response, read this please!!!")