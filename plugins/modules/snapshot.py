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
    choices: [ present, absent ]
    type: str
  snapshot_id:
    description: Snapshot ID
    required: false
    type: str
  devices:
    description: Serial numbers of devices to rediscover
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
"""


def ensure_present(module, client):
    resp = client.create_snapshot(
        snapshot_id=module.params["snapshot_id"],
    )
    if resp:
        msg = "Successfully initiated snapshot: {0}.".format(resp["id"])
        return True, msg, resp
    return False, "Failed to initiate snapshot."


def ensure_absent(module, client):
    snapshot_id = module.params["snapshot_id"]
    data = []
    resp = client.delete_snapshot(
        snapshot_id=snapshot_id,
    )
    if resp:
        msg = "Successfully deleted snapshot: {0}".format(snapshot_id)
        return True, msg, data
    return False, "Failed to delete snapshot", data


def run(module, client):
    if module.params["state"] == "absent":
        return ensure_absent(module, client)
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
                choices=["present", "absent"],
                type="str",
            ),
            devices=dict(
                required=False,
                type="list",
            ),
        ),
        supports_check_mode=True,
        required_if=[("state", "absent", ["snapshot_id"])],
    )

    try:
        ipf_client = client.Client(**module.params["ipfabric"])
        changed, msg, data = run(module, ipf_client)
        module.exit_json(changed=changed, msg=msg, data=data)
    except errors.IPFabricError as e:
        module.fail_json(msg=str(e))


if __name__ == "__main__":
    main()
