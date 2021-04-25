from ansible.module_utils.urls import Request
from ansible.module_utils.six.moves.urllib.error import HTTPError, URLError
from .errors import IPFabricError, AuthError, UnexpectedAPIResponse
import json


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
