import os
import random
import hashlib
import json
from binascii import hexlify
from appdirs import site_config_dir, site_data_dir

def main():
    config_file_dir = site_config_dir("Prophasis", "Prophasis")
    config_file_path = os.path.join(config_file_dir, "agent.conf.json")
    file_loaded = False
    try:
        with open(config_file_path, "r") as config_file:
            config = json.load(config_file)
        file_loaded = True
    except FileNotFoundError:
        # Default values
        config = {
            "port": 4048,
            "temp_dir": os.path.join(site_data_dir("Propasis", "Prophasis"),
                "tmp"),
            "plugin_repo": os.path.join(site_data_dir("Propasis", "Prophasis"),
                "plugin_repo")
            }

    print("Prophasis Agent Setup Script")
    print("============================")
    print("Values shown in square brackets are default.  They will be used if "
        "you do not supply a value for that item.\n")
    if file_loaded:
        print("An existing config file has been found, pressing enter without "
            "entering a value will leave the current value unchanged.\n")

    while True:
        port = input("What port would you like the server to run on? [{}]: "
            "".format(config["port"]))

        if not port:
            port = str(config["port"])

        if port.isdigit() and int(port) >= 1024 and int(port) <= 65535:
            config["port"] = int(port)
            break
        else:
            print("ERROR: {} is not a valid port".format(port))

    temp_dir = input("What directory should be used for tempoary files? "
        "(Will be created if it doesn't exist) [{}]: ".format(
            config["temp_dir"]))

    if not temp_dir:
        temp_dir = config["temp_dir"]

    config["temp_dir"] = os.path.abspath(temp_dir)

    plugin_repo = input("Where should installed plugins be stored?"
        " (Will be created if it doesn't exist) [{}]: ".format(
            config["plugin_repo"]))

    if not plugin_repo:
        plugin_repo = config["plugin_repo"]

        config["plugin_repo"] = os.path.abspath(plugin_repo)

    while True:
        use_ssl = input("Run the agent using SSL? (y/n){}: ".format(
            "" if not file_loaded else " [{}]".format(
                "y" if config["use_ssl"] else "n")
        ))

        if file_loaded and not use_ssl:
            break

        if use_ssl in ["y", "n"]:
            config["use_ssl"] = use_ssl == "y"
            break
        else:
            print("ERROR: Must enter \"y\" or \"n\"")

    if config["use_ssl"]:
        while True:
            ssl_key = input("Path to key file (.key){}: ".format(
                "" if "ssl_key" not in config else " [{}]".format(
                    config["ssl_key"])
            ))

            if file_loaded and not ssl_key:
                break

            if os.path.isfile(ssl_key):
                config["ssl_key"] = os.path.abspath(ssl_key)
                break
            else:
                print("ERROR: File does not exist!")

        while True:
            ssl_crt = input("Path to cert file (.crt){}: ".format(
                "" if "ssl_crt" not in config else " [{}]".format(
                    config["ssl_crt"])
            ))

            if file_loaded and not ssl_crt:
                break

            if os.path.isfile(ssl_crt):
                config["ssl_crt"] = os.path.abspath(ssl_crt)
                break
            else:
                print("ERROR: File does not exist!")

    generate_key = True
    if file_loaded:
        while True:
            regenerate = input("Do you want to generate another authentication "
                "key? (y/n): ")

            if regenerate in ["y", "n"]:
                generate_key = regenerate == "y"
                break
            else:
                print("ERROR: Must enter \"y\" or \"n\"")

    if generate_key:
        # Generate authentication key, display it to the user then store the
        # hash of it.
        authentication_key = generate_authentication_key()

        print()
        print("The authentication key for this agent is:")
        print("\t" + authentication_key)
        print("You will need to enter this into the server when adding this "
                "agent.  If you lose this key you will need to run setup "
                "again to generate a new one.")
        print()

        salt = generate_authentication_key()
        salted_key = salt + authentication_key
        config["auth_key_hash"] = salt + "|" + hashlib.sha256(
            salted_key.encode("ascii")).hexdigest()

    print()
    config_file_json = json.dumps(config, separators=(",\n", ": "))
    print("The following config has been generated:")
    print(config_file_json)

    print()
    print("Config file: {}".format(config_file_path))
    print()

    while True:
        write = input("Would you like to write this config and create "
            "directories? (y/n): ")
        if write == "y":
            break
        elif write == "n":
            print()
            print("Exiting...")
            return

    print()
    print("Creating directories....")
    os.makedirs(config_file_dir, mode=0o755, exist_ok=True)
    os.makedirs(config["plugin_repo"], mode=0o755, exist_ok=True)
    os.makedirs(config["temp_dir"], mode=0o755, exist_ok=True)

    print("Writing config file...")
    with open(config_file_path, "w") as config_file:
        config_file.write(config_file_json)
    print("Complete!")

def generate_authentication_key(n_bits=256):
    if n_bits % 8 != 0:
        raise ValueError("Number of bits must be divisible by 8")
    random_bytes = os.urandom(int(n_bits / 8))
    authentication_key = hexlify(random_bytes).decode("ascii")

    return authentication_key

if __name__ == "__main__":
    main()
