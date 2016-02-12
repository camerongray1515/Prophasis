import os
import random
import hashlib
from binascii import hexlify

def main():
    file_loaded = False

    print("╔═════════════════════════════════════════════════════════════════╗")
    print("║ Prophasis Agent Setup Script                                    ║")
    print("╠═════════════════════════════════════════════════════════════════╢")
    print("║ Values shown in square brackets are default.  They will be used ║")
    print("║ if you do not supply a value for that item.                     ║")
    if file_loaded:
        print("╠═══════════════════════════════════════════════════════════════"
            "══╢")
        print("║ An existing config file has been found, pressing enter without"
            "  ║")
        print("║ entering a value will leave the current value unchanged.      "
            "  ║")
    print("╚═════════════════════════════════════════════════════════════════╝")

    # Default values
    config = {
        "port": 4048,
        "temp_dir": "/tmp",
        "plugin_repo": os.path.abspath(
            os.path.join(os.path.dirname(__file__), "plugin_repo"))
        }

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

    while True:
        temp_dir = input("What directory should be used for tempoary files? "
            "[{}]: ".format(config["temp_dir"]))

        if not temp_dir:
            temp_dir = config["temp_dir"]

        if os.path.isdir(temp_dir):
            config["temp_dir"] = os.path.abspath(temp_dir)
            break
        else:
            print("ERROR: {} is not a valid directory".format(temp_dir))

    while True:
        plugin_repo = input("Where should installed plugins be stored? [{}]: "
            "".format(config["plugin_repo"]))

        if not plugin_repo:
            plugin_repo = config["plugin_repo"]

        if os.path.isdir(plugin_repo):
            config["plugin_repo"] = os.path.abspath(plugin_repo)
            break
        else:
            print("ERROR: {} is not a valid directory".format(plugin_repo))

    while True:
        use_ssl = input("Run the agent using SSL? (y/n){}: ".format(
            "" if not file_loaded else "[ {}]".format(
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
                "" if not file_loaded else " [{}]".format(config["ssl_key"])
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
                "" if not file_loaded else " [{}]".format(config["ssl_crt"])
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

        print("╔═══════════════════════════════════════════════════════════════"
            "═══════════════╗")
        print("║ Authentication Key                                            "
            "               ║")
        print("╠═══════════════════════════════════════════════════════════════"
            "═══════════════╢")
        print("║ {}{}║".format(authentication_key,
            " "*(77-len(authentication_key))))
        print("╠═══════════════════════════════════════════════════════════════"
            "═══════════════╢")
        print("║ If you lose this key, run setup again to generate a new one   "
            "               ║")
        print("╚═══════════════════════════════════════════════════════════════"
            "═══════════════╝")

        # print("The authentication key for this agent is:")
        # print("\t" + authentication_key)
        # print("You will need to enter this into the server when adding this "
        #         "agent.  If you lose this key you will need to run setup "
        #         "again to generate a new one.")

        salt = generate_authentication_key()
        salted_key = salt + authentication_key
        config["auth_key_hash"] = salt + "|" + hashlib.sha256(
            salted_key.encode("ascii")).hexdigest()

    print(config)

def generate_authentication_key(n_bits=256):
    if n_bits % 8 != 0:
        raise ValueError("Number of bits must be divisible by 8")
    random_bytes = os.urandom(int(n_bits / 8))
    authentication_key = hexlify(random_bytes).decode("ascii")

    return authentication_key

if __name__ == "__main__":
    main()
