from sys import version as python_version

from ansible.module_utils.ansible_release import __version__ as ansible_version
from ansible.module_utils.urls import open_url
from ansible.plugins.inventory import BaseInventoryPlugin


class InventoryModule(BaseInventoryPlugin):
    NAME = "axians.ipfabric.inventory"

    def parse(self, inventory, loader, path, cache=True):
        super(InventoryModule, self).parse(inventory, loader, path)
        config = self._read_config_data(path)
        self.use_cache = cache
        print("hi")

        token = self.get_option("token")
        self.api_endpoint = self.get_option("api_endpoint").strip("/")
        self.timeout = self.get_option("timeout")
        self.validate_certs = self.get_option("validate_certs")

        self.headers = {"User-Agent": "ansible %s Python %s"
                        % (anisble_version, python_version.split(" ")[0]),
                        "Content-Type": "application/json"}

        if token:
            self.headers.update({"X-API-Token": token})



if __name__ == "__main__":
    test = InventoryModule()
    test.parse()
