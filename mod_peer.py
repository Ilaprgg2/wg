import subprocess

def add_peer(publickey, allowed_ips, interface):
    try:
        # Add the new peer using the wg command
        subprocess.run(["wg", "set", interface, "peer", publickey, "allowed-ips", allowed_ips], check=True)
        
        # Save the configuration using wg-quick save
        subprocess.run(["wg-quick", "save", interface], check=True)
        
        print(f"Peer with public key {publickey} added to {interface}")
    except subprocess.CalledProcessError as e:
        print(f"Error adding peer: {e}")

def remove_peer(publickey, interface):
    try:
        # Remove the peer using the wg command
        subprocess.run(["wg", "set", interface, "peer", publickey, "remove"], check=True)
        
        # Save the configuration using wg-quick save
        subprocess.run(["wg-quick", "save", interface], check=True)
        
        print(f"Peer with public key {publickey} removed from {interface}")
    except subprocess.CalledProcessError as e:
        print(f"Error removing peer: {e}")
