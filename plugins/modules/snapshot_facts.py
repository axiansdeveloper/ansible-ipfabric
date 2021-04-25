#!/usr/bin/python

from __future__ import absolute_import, division, print_function
from ansible.module_utils.basic import AnsibleModule
from ..module_utils import errors
from ..module_utils import client
from ..module_utils import ipfabric_utils

__metaclass__ = type

DOCUMENTATION = r"""
---
module: snapshot_facts

short_description: Gather Information about Snapshots within IPFabric

version_added: "0.0.2"
extends_documentation_fragment:
  - axiansdeveloper.ipfabric.ipfabric

description: Gather Information about Snapshots within IPFabric

options:
  snapshot_id:
    description: Snapshot ID
    required: false
    type: str

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
      snapshot_facts:
        ipfabric:
          host: https://ipfabric.local
          token: thisIsMyToken
"""

RETURN = r"""
msg:
  description: Message indicating failure or info about what has happened.
  returned: always
  type: str
data:
  description: Data returned from the module.
  returned: always
  type: list
"""

# def _return_snapshot(snapshots, snapshot_id):


def main():

    module = AnsibleModule(
        argument_spec=dict(
            ipfabric_utils.get_spec("ipfabric"),
            snapshot_id=dict(
                required=False,
                type="str",
            ),
        ),
        supports_check_mode=True,
    )

    result = dict(changed=False, msg="", data=[])

    try:
        ipf_client = client.Client(**module.params["ipfabric"])
        snapshots = ipf_client.get_snapshots(
            snapshot_id=module.params["snapshot_id"],
        )
        if snapshots:
            result["data"] = snapshots
            module.exit_json(**result)
        module.fail_json(
            msg="Failed to find snapshot with id: {0}".format(
                module.params["snapshot_id"],
            ),
        )
    except errors.IPFabricError as e:
        module.fail_json(msg=str(e))


if __name__ == "__main__":
    main()
