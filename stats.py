import subprocess
import database
from mainapp import disable_wg_user, send_notification, send_notification2, send_backup
import time
import schedule

def is_within_three_days(future_date, current_time):
    three_days_in_seconds = 3 * 24 * 60 * 60  # 3 days * 24 hours * 60 minutes * 60 seconds
    time_difference = float(future_date) - float(current_time)
    return time_difference < three_days_in_seconds


def get_wg_transfer_data(interface):
    try:
        # Run the wg show <interface> transfer command
        cmd = ['wg', 'show', interface, 'transfer']
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT).decode('utf-8')
        # Process the output
        transfer_data = []
        for line in output.strip().split('\n'):
            parts = line.split()
            if len(parts) == 3:
                public_key, rx, tx = parts
                total_transfer = (int(rx) + int(tx)) / (1024 * 1024)  # Convert to MB
                transfer_data.append((public_key, total_transfer))
        return transfer_data
    
    except subprocess.CalledProcessError as e:
        return [("error", f"Command failed: {e.output.decode('utf-8').strip()}")]
    except Exception as e:
        return [("error", str(e))]

interface = "wgg"


def check_traffic():
    start_time = time.time()
    peers = get_wg_transfer_data(interface)
    for pubkey, usage in peers:
        if pubkey == "error":
            print(f"Error: {usage}")
        else:
            user_data = database.get_user_by_pubkey(pubkey)
            if not user_data:
                print(f"WARN! >>> {pubkey} is not in the database")
                continue
            id_row, name, private_key, public_key, allowed_ips, date, total_volume, db_used, db_last_used, status, percent_push, days_push = user_data
            # name = database.get_user_by_pubkey(pubkey)[1]
            # total_volume = database.get_user_by_pubkey(pubkey)[6]
            # db_used = database.get_user_by_pubkey(pubkey)[7]
            # db_last_used = database.get_user_by_pubkey(pubkey)[8]
            if usage == 0:
                continue
            if usage == db_last_used:
                continue
            usage_percentage  = (db_used / total_volume) * 100
            if usage_percentage >= 80 and percent_push != "sent":
                send_notification2("percent", name)
                database.set_percent_push(name)
            if usage > db_used:
                new_usage = db_used + (usage - db_last_used)
                database.update_used(pubkey, new_usage)
                database.update_last_used(pubkey, usage)
            if usage < db_used:
                if usage > db_last_used:
                    usage_diff = usage - db_last_used
                    new_usage = db_used + usage_diff
                    database.update_used(pubkey, new_usage)
                    database.update_last_used(pubkey, usage)
                    print(2)
                if usage < db_last_used:
                    new_usage = db_used + usage
                    database.update_used(pubkey, new_usage)
                    database.update_last_used(pubkey, usage)
                    print(3)
            if total_volume < db_used:
                disable_wg_user(name, interface)
                send_notification("limit",name)
                continue
    end_time = time.time()
    execution_time = end_time - start_time
    print(f"check_traffic() took {execution_time:.4f} seconds to run")


def check_date():
    peers = get_wg_transfer_data(interface)
    for pubkey, usage in peers:
        if pubkey == "error":
            print(f"Error: {usage}")
            continue
        else:
            user_data = database.get_user_by_pubkey(pubkey)
            if not user_data:
                print(f"WARN! >>> {pubkey} is not in the database")
                continue
            id_row, name, private_key, public_key, allowed_ips, date, total_volume, db_used, db_last_used, status, percent_push, days_push = user_data
            current_time = time.time()
            if is_within_three_days(date, current_time) and days_push != "sent":
                send_notification2("expire", name)
                database.set_days_push(name)
            if float(date) < current_time:
                send_notification("expired",name)
                disable_wg_user(name, interface)


# Schedule check_traffic() to run every 15 seconds
schedule.every(15).seconds.do(check_traffic)

# Schedule check_date() to run every 30 minutes
schedule.every(30).minutes.do(check_date)

# Schedule send_backup() to run every 60 minutes
schedule.every(60).minutes.do(send_backup)


# Run the scheduled jobs
while True:
    schedule.run_pending()
    time.sleep(1)