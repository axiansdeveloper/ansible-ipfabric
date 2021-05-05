#!/usr/bin/python

from __future__ import absolute_import, division, print_function
from ansible.module_utils.basic import AnsibleModule
from ..module_utils import ipfabric_utils
from ..module_utils import errors
from ..module_utils import client


DOCUMENTATION = r"""
---
module: snapshot

short_description: Create, Update or Delete Snapshots within IPFabric

version_added: "0.0.2"
extends_documentation_fragment:
  - axiansdeveloper.ipfabric.ipfabric

description: Create, Update or Delete Snapshots within IPFabric

options:
  state:
    description:
      - State of snapshot.
    choices: [ present, absent, load, unload ]
    type: str
  snapshot_id:
    description: Snapshot ID
    required: false
    type: str
  devices:
    description:
      - List of serial numbers of devices to
      - rediscover in existing snapshot.
    required: false
    type: list
  ips:
    description:
      - List of IP addresses to discover in a new snapshot.
      - I(settings) permission is required for API token.
    required: false
    type: list

author:
    - Alex Gittings (@minitriga)
"""

EXAMPLES = r"""
- name: "Test IPFabric modules"
  connection: local
  hosts: localhost
  gather_facts: False

  tasks:
    - name: Create a New Ipfabric Snapshot
      snapshot:
        ipfabric:
          host: https://ipfabric.local
          token: thisIsMyToken

    - name: Delete IPFabric Snapshot
      snapshot:
        ipfabric:
          host: https://ipfabric.local
          token: thisIsMyToken
        state: absent
        snapshot_id: 91da47aa-4843-4562-a86f-acc0012d63fd

    - name: Rediscover Device in Existing Snapshot
      snapshot:
        ipfabric:
          host: https://ipfabric.local
          token: thisIsMyToken
        snapshot_id: 91da47aa-4843-4562-a86f-acc0012d63fd
        devices:
          - ABCDE1234

    - name: Rediscover Devices in New Snapshot
      snapshot:
        ipfabric:
          host: https://ipfabric.local
          token: thisIsMyToken
        ips:
          - 192.168.1.1
          - 192.168.1.2

    - name: Load Unloaded Snapshot
      snapshot:
        ipfabric:
          host: https://ipfabric.local
          token: thisIsMyToken
      state: load
      snapshot_id: 91da47aa-4843-4562-a86f-acc0012d63fd

    - name: Unload loaded Snapshot
      snapshot:
        ipfabric:
          host: https://ipfabric.local
          token: thisIsMyToken
      state: unload
      snapshot_id: 91da47aa-4843-4562-a86f-acc0012d63fd
"""


def ensure_present(module, client):
    resp = client.create_snapshot(
        snapshot_id=module.params["snapshot_id"],
        devices=module.params["devices"],
        ips=module.params["ips"],
    )
    module.fail_json(msg=resp)
    if resp:
        msg = "Successfully initiated snapshot: {0}.".format(resp["id"])
        return True, msg, resp


def ensure_absent(module, client):
    snapshot_id = module.params["snapshot_id"]
    resp = client.delete_snapshot(
        snapshot_id=snapshot_id,
    )
    data = client.get_snapshots()
    if resp:
        msg = "Successfully deleted snapshot: {0}".format(snapshot_id)
        return True, msg, data


def ensure_loaded(module, client):
    snapshot_id = module.params["snapshot_id"]
    state = module.params["state"]
    resp = client.snapshot_load(snapshot_id=snapshot_id, state=state)
    snapshot = client.get_snapshots(snapshot_id=snapshot_id)
    if resp:
        return (
            True,
            "Snapshot {0} successfully {1}ed".format(
                snapshot_id,
                state,
            ),
            snapshot,
        )


def run(module, client):
    if module.params["state"] == "absent":
        return ensure_absent(module, client)
    elif module.params["state"] in ["load", "unload"]:
        return ensure_loaded(module, client)
    return ensure_present(module, client)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            ipfabric_utils.get_spec("ipfabric"),
            snapshot_id=dict(
                required=False,
                type="str",
            ),
            state=dict(
                required=False,
                default="present",
                choices=["present", "absent", "load", "unload"],
                type="str",
            ),
            devices=dict(
                required=False,
                type="list",
            ),
            ips=dict(
                required=False,
                type="list",
            ),
        ),
        supports_check_mode=True,
        required_if=[
            ("state", "absent", ["snapshot_id"]),
            ("state", "load", ["snapshot_id"]),
            ("state", "unload", ["snapshot_id"]),
        ],
    )

    try:
        ipf_client = client.Client(**module.params["ipfabric"])
        changed, msg, data = run(module, ipf_client)
        module.exit_json(changed=changed, msg=msg, data=data)
    except errors.IPFabricError as e:
        module.fail_json(msg=str(e))


if __name__ == "__main__":
    main()
