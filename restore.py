import database
import mod_peer

users = database.get_all_users()
for user in users:
    public_key = user[3]
    allowed_ips = user[4]
    mod_peer.add_peer(public_key, allowed_ips, "wgg")
    print(f"Publick key {public_key} Added")