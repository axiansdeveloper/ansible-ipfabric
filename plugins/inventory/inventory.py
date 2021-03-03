__metaclass__ = type

import json
import re
from sys import version as python_version

from ansible.errors import AnsibleError
from ansible.module_utils._text import to_native, to_text
from ansible.module_utils.ansible_release import __version__ as ansible_version
from ansible.module_utils.six.moves.urllib import error as urllib_error
from ansible.module_utils.urls import open_url
from ansible.plugins.inventory import BaseInventoryPlugin, Cacheable

DOCUMENTATION = """
    name: inventory
    plugin_type: inventory
    author:
      - Alex Gittings (https://github.com/minitriga)
    short_description: IPFabric inventory source
    description:
      - Get inventory from IPFabric
    extends_documentation_fragment:
      - inventory_cache
    options:
        plugin:
            description: token that ensures this is a source file for the 'ipfabric' plugin.
            required: True
            choices: ['axians.ipfabric.inventory']
        api_endpoint:
            description: Endpoint of the IPFabric API.
            required: True
            env:
              - name: IPFABRIC_API
        validate_certs:
            description:
              - Allows connections when SSL certificates are not valid. Set to C(false) when certificates are not trusted.
            default: True
            type: boolean
        token:
            description:
              - IPFabric API
            required: True
            env:
              - name: IPFABRIC_TOKEN
        timeout:
            description: Timeout for IPFabric requests in seconds.
            type: int
            default: 60
        snapshot:
            description: Snapshot ID
            type: str
            default: $last
        group_by:
            description: Keys used to create groups.
            type: list
            choices:
              - family
              - platform
              - platforms
              - site
              - sites
              - vendor
              - vendors
        group_names_raw:
            description: Will not add the group_by choice name to the group names
            default: False
            type: boolean
        plurals:
            description:
                - If True, all host vars are contained inside single-element arrays.
                - Group names will be plural (ie. "sites_mysite" instead of "site_mysite")
                - The choices of I(group_by) will be changed by this option.
            default: True
            type: boolean
"""  # noqa: E501


class InventoryModule(BaseInventoryPlugin, Cacheable):
    NAME = "axians.ipfabric.ipf_inventory"

    def _fetch_information(self, url, data=None, method=None):
        method = method or ("POST" if data else "GET")
        results = None
        cache_key = self.get_cache_key(url)

        user_cache_setting = self.get_option("cache")
        attempt_to_read_cache = user_cache_setting and self.use_cache

        if attempt_to_read_cache:
            try:
                results = self._cache[cache_key]
                need_to_fetch = False
            except KeyError:
                # occurs if the cache_key is not
                # in the cache or if the cache_key expired
                # we need to fetch the URL now
                need_to_fetch = True

        else:
            # not reading from cache so do fetch
            need_to_fetch = True

        if need_to_fetch:
            self.display.v("Fetching: " + url)

            try:
                response = open_url(
                    url,
                    headers=self.headers,
                    timeout=self.timeout,
                    validate_certs=self.validate_certs,
                    method=method,
                    data=data,
                )
            except urllib_error.HTTPError as e:
                # TODO
                raise AnsibleError(
                    to_native(e.fp.read()),
                )

            try:
                raw_data = to_text(
                    response.read(),
                    errors="surrogate_or_strict",
                )

            except UnicodeError:
                raise AnsibleError(
                    "Incorrect encoding of fetched payload from IPFabric API.",
                )

            try:
                results = json.loads(raw_data)
            except ValueError:
                raise AnsibleError(
                    "Incorrect JSON payload: %s" % raw_data,
                )

            if user_cache_setting:
                self._cache[cache_key] = results

            return results

    def fetch_api_info(self):
        version = self._fetch_information(self.api_endpoint + "/os/version")
        self.version = version["version"]

    def fetch_devices(self):
        self.devices_list = []
        payload = {
            "columns": [
                "loginIp",
                "family",
                "hostname",
                "platform",
                "loginType",
                "sn",
                "siteName",
                "vendor",
                "version",
            ],
            "snapshot": self.snapshot,
        }
        self.devices_list = self._fetch_information(
            self.api_endpoint + "/tables/inventory/devices",
            data=json.dumps(payload),
        )["data"]
        return self.devices_list

    def _pluralize_group_by(self, group_by):
        mapping = {
            "platform": "platforms",
            "vendor": "vendors",
            "site": "sites",
        }

        if self.plurals:
            mapped = mapping.get(group_by)
            return mapped or group_by
        else:
            return group_by

    def extract_ip(self, device):
        return device.get("loginIp")

    def extract_platform(self, device):
        return self.slugify(device.get("platform"))

    def slugify(self, name):
        removed_chars = re.sub(r"[^\-\.\w\s]", "", name)
        convert_chars = re.sub(r"[\-\.\s]+", "_", removed_chars)

        return convert_chars.strip().lower()

    def extract_site(self, device):
        return self.slugify(device.get("siteName"))

    def extract_family(self, device):
        return self.slugify(device.get("family"))

    def extract_vendor(self, device):
        return self.slugify(device.get("vendor"))

    @property
    def group_extractors(self):
        extractors = {
            "loginIp": self.extract_ip,
            self._pluralize_group_by("platform"): self.extract_platform,
            self._pluralize_group_by("site"): self.extract_site,
            self._pluralize_group_by("vendor"): self.extract_vendor,
            "family": self.extract_family,
        }

        return extractors

    def generate_group_name(self, group, group_for_host):
        if isinstance(group, bool):
            if group:
                return group
            else:
                return None

        if self.group_names_raw:
            return group
        else:
            return "_".join([group, group_for_host])

    def add_device_to_groups(self, device, hostname):
        for group in self.group_by:
            if group not in self.group_extractors:
                raise AnsibleError(
                    'group_by option "%s" is not valid. (Maybe check the plurals option? It can determine what group_by options are valid)'  # noqa: E501
                    % group,
                )  # pylint disable=raise-missing-from

            group_for_device = self.group_extractors[group](device)

            if not group_for_device:
                continue

            if not isinstance(group_for_device, list):
                group_for_device = [group_for_device]

            for group_for_device in group_for_device:
                group_name = self.generate_group_name(group, group_for_device)

                if not group_name:
                    continue

                transformed_group_name = self.inventory.add_group(
                    group=group_name,
                )
                self.inventory.add_host(
                    group=transformed_group_name,
                    host=hostname,
                )

    def main(self):
        self.fetch_api_info()

        self.fetch_devices()

        for device in self.devices_list:
            print(device)
            hostname = device["hostname"]
            self.inventory.add_host(hostname)
            self.inventory.set_variable(
                hostname,
                "ansible_host",
                device["loginIp"],
            )
            self.add_device_to_groups(device=device, hostname=hostname)

    def parse(self, inventory, loader, path, cache=True):
        super(InventoryModule, self).parse(
            inventory,
            loader,
            path,
        )

        self._read_config_data(path=path)
        self.use_cache = cache

        token = self.get_option("token")
        self.api_endpoint = self.get_option("api_endpoint").strip("/")
        self.timeout = self.get_option("timeout")
        self.validate_certs = self.get_option("validate_certs")
        self.snapshot = self.get_option("snapshot")
        self.group_by = self.get_option("group_by")
        self.group_names_raw = self.get_option("group_names_raw")
        self.plurals = self.get_option("plurals")

        self.headers = {
            "User-Agent": "ansible %s Python %s"
            % (ansible_version, python_version.split(" ")[0]),
            "Content-Type": "application/json",
        }

        if token:
            self.headers.update({"X-API-Token": token})

        self.main()
