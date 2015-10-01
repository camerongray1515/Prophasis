import json
import os
import bcrypt

from binascii import hexlify

config_file_path = os.path.join(os.path.dirname(
    os.path.realpath(__file__)), "config.json")

def get_config():
    try:
        with open(config_file_path, "r") as f:
            config = json.load(f)
    except FileNotFoundError:
        raise SystemExit("Config file, config.json not found in agent "
            "directory, perhaps you need to run the agent setup script?")

    required_fields = ["plugin_repo"]
    for field in required_fields:
        if field not in config:
            raise SystemExit("Config file does not contain an entry for {0} "
                "you must rectify this in order to continue".format(field))

    return config

def setup_wizard():
    config = {}

    questions = [
        {"prompt": "What port would you like the server to run on?",
        "default": "4048",
        "validator": lambda x: x.isdigit() and int(x) > 1023 and
                int(x) <= 65535,
        "validation_error": "Value must be a number between 1024 and 65535 "
                "inclusive",
        "config_section": "Server",
        "config_key": "port"
        },

        {"prompt": "Run the server using SSL? (y/n)",
        "default": "y",
        "validator": lambda x: x in ["y", "n"],
        "validation_error": "Must answer 'y' or 'n'",
        "answer_converter": lambda x: x == "y",
        "config_key": "use_ssl"
        },

        {"prompt": "Path to cert file (.crt)",
        "config_key": "ssl_crt",
        "ask_condition": lambda config: config["use_ssl"]
        },

        {"prompt": "Path to key file (.key)",
        "config_key": "ssl_key",
        "ask_condition": lambda config: config["use_ssl"]
        },

        {"prompt": "What directory should installed plugins be kept in?",
        "default": "plugin_repo",
        "config_key": "plugin_repo"
        },
    ]

    for question in questions:
        if "ask_condition" in question:
            if not question["ask_condition"](config):
                continue

        answer_invalid=True
        while answer_invalid:
            if "default" in question:
                question_string = "{0} [{1}]: ".format(question["prompt"],
                        question["default"])
            else:
                question_string = "{0}: ".format(question["prompt"])

            answer = input(question_string)
            print("")

            if answer == "":
                if "default" in question:
                    answer = question["default"]
                else:
                    continue

            if "validator" not in question or question["validator"](answer):
                answer_invalid = False

                if "answer_converter" in question:
                    answer = question["answer_converter"](answer)

                config[question["config_key"]] = answer
            else:
                print("{0}".format(question["validation_error"]))

    # Generate authentication key, display it to the user then store the
    # hash of it.
    authentication_key = generate_authentication_key()

    print("The authentication key for this agent is:")
    print("\t" + authentication_key)
    print("You will need to enter this into the server when adding this "
            "agent.  If you lose this key you will need to run setup "
            "again to generate a new one.")

    config["auth_key_hash"] = bcrypt.hashpw(
            authentication_key.encode("ascii"), bcrypt.gensalt()).decode(
                "ascii")

    with open(config_file_path, "w") as f:
        json.dump(config, f, separators=(",\n", ": "))

    print("\nConfig file written!")

def generate_authentication_key(n_bits=256):
    if n_bits % 8 != 0:
        raise ValueError("Number of bits must be divisible by 8")
    random_bytes = os.urandom(int(n_bits / 8))
    authentication_key = hexlify(random_bytes).decode("ascii")

    return authentication_key