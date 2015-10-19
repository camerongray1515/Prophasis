import requests
import json

class AuthenticationError(Exception):
    pass

class RequestError(Exception):
    pass

class Agent():
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

        return json.loads(r.text)

    def get_plugin_data(self, plugin_id):
        payload = {"plugin-id": plugin_id}
        r = requests.get(self.url + "/get-plugin-data/", params=payload,
            verify=self.verify_certs)

        self._check_request_status(r)

        return json.loads(r.text)

    def update_plugin(self, plugin_id, plugin_payload):
        data = {"plugin-id": plugin_id}
        files = {"plugin": plugin_payload}
        r = requests.post(self.url + "/update-plugin/", data=data, files=files,
            verify=self.verify_certs)

        self._check_request_status(r)

        return json.loads(r.text)

if __name__ == "__main__":
    a = Agent("localhost", auth_key="a9b8fdd73d03bd7b54f31adb8bb2424e52fff"
        "09feb37a98defdf6d1f3bf4f2db", verify_certs=True)
    with open("../../plugins/test_plugin.tar.gz", "rb") as f:
        print(a.update_plugin("me.camerongray.proj.test_plugin", f))
