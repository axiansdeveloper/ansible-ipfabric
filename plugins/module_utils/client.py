from ansible.module_utils.urls import Request
from ansible.module_utils.six.moves.urllib.error import HTTPError
from ansible.module_utils.six.moves.urllib.error import URLError
from .errors import IPFabricError
from .errors import AuthError
from .errors import UnexpectedAPIResponse
import json
import time


class Response:
    def __init__(self, status, data, headers=None):
        self.status = status
        self.data = data
        self.headers = dict(headers) if headers else {}
        self._json = None

    @property
    def json(self):
        if self._json is None:
            try:
                self._json = json.loads(self.data)
            except ValueError:
                raise IPFabricError(
                    "Recieved invalid JSON response: {0}".format(self.data),
                )
        return self._json


class Client:
    def __init__(self, host, token, timeout=None, validate_certs=True):
        self.host = host
        self.token = token
        self.timeout = timeout
        self.validate_certs = validate_certs

        self._auth_header = None
        self._client = Request()

    @property
    def auth_header(self):
        if not self._auth_header:
            self._auth_header = self._login()
        return self._auth_header

    def _login(self):
        if self.token:
            return {"X-API-Token": self.token}

    def _request(self, method, path, data=None, headers=None):
        try:
            raw_resp = self._client.open(
                method,
                path,
                data=data,
                headers=headers,
                timeout=self.timeout,
                validate_certs=self.validate_certs,
            )
        except HTTPError as e:
            if e.code == 401:
                raise AuthError(
                    "Failed to authenticate with IPFabric: {0} {1}"
                    " (check token)".format(
                        e.code,
                        e.reason,
                    ),
                )
            elif e.code == 403:
                raise AuthError(
                    "Insufficient API Rights Check Permissions: "
                    "{0} {1}".format(
                        e.code,
                        e.reason,
                    ),
                )
            return Response(e.code, e.read(), e.headers)
        except URLError as e:
            raise IPFabricError(e.reason)

        return Response(raw_resp.status, raw_resp.read(), raw_resp.headers)

    def request(self, method, path, query=None, data=None):
        url = "{0}/api/v1/{1}".format(self.host, path)

        headers = dict(Accept="application/json", **self.auth_header)
        if data is not None:
            data = json.dumps(data, separators=(",", ":"))
            headers["Content-Type"] = "application/json"
        return self._request(method, url, data=data, headers=headers)

    def get(self, path):
        resp = self.request("GET", path)
        if resp.status in (200, 404):
            return resp
        raise UnexpectedAPIResponse(resp.status, resp.data)

    def post(self, path, data):
        resp = self.request("POST", path, data=data)
        if resp.status in (200, 201):
            return resp
        raise UnexpectedAPIResponse(resp.status, resp.data)

    def get_snapshots(self, snapshot_id=None):
        resp = self.request("GET", "snapshots")
        if resp.status == 200:
            if snapshot_id:
                single_snapshot = [
                    snapshot
                    for snapshot in resp.json
                    if snapshot_id == snapshot["id"]  # noqa E501
                ]

                if len(single_snapshot) == 0:
                    raise IPFabricError("Snapshot not found.")

                return single_snapshot
            return resp.json
        raise UnexpectedAPIResponse(resp.status, resp.data)

    def rediscover_existing_snapshot(
        self,
        snapshot_id,
        devices,
    ):
        data = {"snList": devices}
        url = "snapshots/{0}/devices".format(snapshot_id)
        resp = self.request("POST", url, data=data)
        return resp

    def rediscover_new_snapshot(self, ips):
        data = {
            "networks": {
                "include": ["{0}/32".format(ip) for ip in ips],
            },
            "seedList": ips,
        }
        resp = self.request("POST", "snapshots", data=data)
        return resp

    def create_snapshot(self, snapshot_id=None, devices=None, ips=None):
        if snapshot_id and devices:
            resp = self.rediscover_snapshot(snapshot_id, devices)
        elif ips:
            resp = self.rediscover_new_snapshot(ips)
        else:
            resp = self.request("POST", "snapshots")

        if resp.status == 200 and resp.json["success"]:
            time.sleep(1)
            iterations = 0
            snapshot = self.get_snapshots()[0]
            while snapshot["state"] != "discovering" and iterations >= 10:
                snapshot = self.get_snapshots()[0]["state"]
                iterations += 1
            return snapshot

        raise IPFabricError("Failed to create snapshot.")

    def delete_snapshot(self, snapshot_id):
        if self.get_snapshots(snapshot_id=snapshot_id):
            resp = self.request("DELETE", "snapshots/{0}".format(snapshot_id))
            if resp.status == 204:
                return True
            raise IPFabricError("Snapshot failed to delete.")

    def snapshot_load(self, snapshot_id, state):
        if self.get_snapshots(snapshot_id):
            url = "snapshots/{0}/{1}".format(snapshot_id, state)
            resp = self.request("POST", url)
            if resp.status == 204:
                return resp
            raise IPFabricError("Snapshot failed to {0}.".format(state))
