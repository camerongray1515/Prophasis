import requests
import json
from functools import wraps

# We may want to have some hosts not check the CA of certificates so this
# stops the log spam when this is the case
requests.packages.urllib3.disable_warnings()

class AuthenticationError(Exception):
    pass

class RequestError(Exception):
    pass

class CommandUnsuccessfulError(Exception):
    pass

class Agent():
    """
        Methods can raise the following exceptions which should be handled

        CommandUnsuccessfulError - The command was executed but failed
        AuthenticationError - Authentication key was most likely incorrect
        RequestError - The server returned an error code
        requests.exceptions.ConnectionError - Could not connect to remote
            machine e.g. the connection was refused
        requests.exceptions.Timeout - The connection to the remote host timed
            out
    """
    def __init__(self, host, auth_key, port=4048, use_ssl=True,
        verify_certs=True):
        protocol = "https" if use_ssl else "http"
        self.url = "{0}://core:{1}@{2}:{3}".format(protocol, auth_key, host,
            port)
        self.verify_certs = verify_certs

    def _check_request_status(self, r):
        if r.status_code != 200:
            if r.status_code == 401:
                raise AuthenticationError
            else:
                raise RequestError

    def check_plugin_verison(self, plugin_id, plugin_version):
        payload = {"plugin-id": plugin_id, "plugin-version": plugin_version}
        r = requests.get(self.url + "/check-plugin-version/", params=payload,
            verify=self.verify_certs)

        self._check_request_status(r)

        result = json.loads(r.text)
        if not result["success"]:
            raise CommandUnsuccessfulError(result["message"])

        return result["update-required"]

    def get_plugin_data(self, plugin_id):
        payload = {"plugin-id": plugin_id}
        r = requests.get(self.url + "/get-plugin-data/", params=payload,
            verify=self.verify_certs)

        self._check_request_status(r)

        result = json.loads(r.text)
        if not result["success"]:
            raise CommandUnsuccessfulError(result["message"])

        return (result["value"], result["message"])

    def update_plugin(self, plugin_id, plugin_payload):
        data = {"plugin-id": plugin_id}
        files = {"plugin": plugin_payload}
        r = requests.post(self.url + "/update-plugin/", data=data, files=files,
            verify=self.verify_certs)

        self._check_request_status(r)

        result = json.loads(r.text)
        if not result["success"]:
            raise CommandUnsuccessfulError(result["message"])

        return True

if __name__ == "__main__":
    a = Agent("localhost", auth_key="a9b8fdd73d03bd7b54f31adb8bb2424e52fff"
        "09feb37a98defdf6d1f3bf4f2db", verify_certs=False)
    with open("../../plugins/test_plugin.tar.gz", "rb") as f:
        print(a.update_plugin("me.camerongray.proj.test_plugin", f))
