import mod_peer
import database
import subprocess
import ipaddress
import time
import os
import requests
from dotenv import load_dotenv

# Load the .env file
load_dotenv()

main_server = os.getenv('MAIN_SERVER')


def generate_wireguard_keys():
    # Generate private key
    private_key = subprocess.check_output(["wg", "genkey"]).decode().strip()

    # Generate public key from private key
    public_key = subprocess.check_output(["wg", "pubkey"], input=private_key.encode()).decode().strip()

    return private_key, public_key

def find_next_available_ip(start_ip):
    # Parse the starting IP and subnet
    network = ipaddress.ip_network(start_ip, strict=False)
    current_ip = network.network_address

    while True:  # Continue indefinitely until an available IP is found
        current_ip_cidr = f"{current_ip}/32"  # Always use /32 for individual IP checks
        if not database.check_allowed_ips(current_ip_cidr):
            return current_ip_cidr
        current_ip += 1

        # Check if we've reached the maximum possible IPv4 address
        if current_ip == ipaddress.IPv4Address('11.0.3.255'):
            print("No IPs Left")
            return None  # No available IP in the entire IPv4 range

def add_wg_user(name, date, usage, interface):
    private_key, public_key = generate_wireguard_keys()
    allowed_ips = find_next_available_ip("11.0.0.2/32")
    
    if allowed_ips is None:
        print("Error: No available IP addresses")
        return None
    
    if database.add_user(name, private_key, public_key, allowed_ips, date, usage):
        mod_peer.add_peer(public_key, allowed_ips, interface)
        return private_key, allowed_ips
    else:
        print("Error: Failed to add user to database")
    
    return None

def remove_wg_user(name, interface):
    user = database.get_user_by_name(name)
    mod_peer.remove_peer(user[3], interface)
    database.remove_user(name)

def disable_wg_user(name, interface):
    user = database.get_user_by_name(name)
    database.change_status(name, 0)
    mod_peer.remove_peer(user[3], interface)

def enable_wg_user(name, interface):
    user = database.get_user_by_name(name)
    mod_peer.add_peer(user[3], user[4], interface)
    database.change_status(name, 1)



def get_latest_handshake(interface, public_key):
    try:
        # Run the wg show command
        result = subprocess.run(
            ['wg', 'show', interface, 'latest-handshakes'],
            capture_output=True,
            text=True,
            check=True
        )
        
        # Split the output into lines
        lines = result.stdout.strip().split('\n')
        
        # Search for the line with the given public key
        for line in lines:
            parts = line.split()
            if len(parts) == 2 and parts[0] == public_key:
                # Get the timestamp
                return parts[1]
                
                # # Calculate the time difference
                # time_diff = int(time.time()) - timestamp
                
                # # Convert to human-readable format
                # if time_diff < 60:
                #     return f"{time_diff} second{'s' if time_diff != 1 else ''} ago"
                # elif time_diff < 3600:
                #     minutes = time_diff // 60
                #     seconds = time_diff % 60
                #     return f"{minutes} minute{'s' if minutes != 1 else ''}, {seconds} second{'s' if seconds != 1 else ''} ago"
                # elif time_diff < 86400:
                #     hours = time_diff // 3600
                #     minutes = (time_diff % 3600) // 60
                #     return f"{hours} hour{'s' if hours != 1 else ''}, {minutes} minute{'s' if minutes != 1 else ''} ago"
                # else:
                #     days = time_diff // 86400
                #     hours = (time_diff % 86400) // 3600
                #     return f"{days} day{'s' if days != 1 else ''}, {hours} hour{'s' if hours != 1 else ''} ago"
        
        # If the public key is not found
        return "Never"
    
    except subprocess.CalledProcessError as e:
        print(f"Error running wg command: {e}")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None



def check_wg_interface(interface_name):
    try:
        # Run the 'wg show' command for the specified interface
        result = subprocess.run(['wg', 'show', interface_name], capture_output=True, text=True, check=True)
        
        # If the command succeeds, the interface is up
        return True
    except subprocess.CalledProcessError:
        # If the command fails, the interface is likely down or doesn't exist
        return False
    


def get_wireguard_public_key(interface):
    try:
        # Use wg show command to get interface info
        cmd = f"wg show {interface} public-key"
        stream = os.popen(cmd)
        public_key = stream.read().strip()
        
        if not public_key:
            return f"down"
        
        return public_key
    
    except Exception as e:
        return f"An unexpected error occurred: {str(e)}"
    

def get_wireguard_private_key(interface):
    try:
        # Use wg show command to get interface info
        cmd = f"wg show {interface} private-key"
        stream = os.popen(cmd)
        private_key = stream.read().strip()
        
        if not private_key:
            return f"down"
        
        return private_key
    
    except Exception as e:
        return f"An unexpected error occurred: {str(e)}"



def send_notification(action, name):
    # Headers
    headers = {
        "Content-Type": "application/json"
    }
    # Request body
    data = {
        "action": action,
        "name": name
    }
    url = main_server + "/dev/status/"
    # Send POST request
    try:
        response = requests.post(url, headers=headers, json=data)
        
        # Check if the request was successful
        if response.status_code == 200:
            print("Request successful!")
        else:
            print(f"Request failed with status code: {response.status_code}")
            print(f"Response content: {response.text}")
    except requests.RequestException as e:
        print(f"An error occurred: {e}")

# function for sending notification on 3 days left and 80 percent used
def send_notification2(action, name):
    # Headers
    headers = {
        "Content-Type": "application/json"
    }
    # Request body
    data = {
        "action": action,
        "name": name
    }
    url = main_server + "/dev/status2/"
    # Send POST request
    try:
        response = requests.post(url, headers=headers, json=data)
        
        # Check if the request was successful
        if response.status_code == 200:
            print("Request successful!")
        else:
            print(f"Request failed with status code: {response.status_code}")
            print(f"Response content: {response.text}")
    except requests.RequestException as e:
        print(f"An error occurred: {e}")
### end



def send_backup():
    privkey = get_wireguard_private_key("wgg")
    route = "/api/backup/sync/"
    url = main_server + route
    ip = requests.get('https://ipinfo.io/ip').text.strip()
    files = {"file": open("./db.db", "rb")}
    params = {"privkey": privkey, "ip":ip}  # Changed from 'data' to 'params'
    response = requests.post(url, files=files, params=params)  # Changed 'data' to 'params'
    print(response.json())

