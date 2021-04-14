#!/usr/bin/python

from __future__ import absolute_import, division, print_function
import json
from ansible.module_utils._text import to_text
from ansible.module_utils.six.moves.urllib import error as urllib_error
from ansible.module_utils.urls import open_url
from ansible.module_utils.basic import AnsibleModule
from copy import deepcopy
from ansible_collections.axiansdeveloper.ipfabric.plugins.module_utils.ipfabric_utils import (  # noqa: E501
    IPFABRIC_ARG_SPEC,
)


__metaclass__ = type

DOCUMENTATION = r"""
---
module: ipfabric_snapshot

short_description: Create, Update or Delete Snapshots within IPFabric

version_added: "0.0.2"

description: Create, Update or Delete Snapshots within IPFabric

options:
    ipfabric_url:
      description:
        - URL of the IPFabric instance resolvable by the Ansible consol host
      required: true
      type: str
    ipfabric_token:
      description:
        - The token created within IPFabric to Authorize API access (must have snapshot permissions)  # noqa: E501
      required: true
      type: str
    validate_certs:
      description:
        - IF C(no), SSL certificates will not be calidated. This should only be used on personally controlles sites using self-signed certificates.  # noqa: E501
      default: true
      type: raw
    data:
      description: This is the message to send to the test module.
      required: true
      type: dict
      suboptions:
        id:
          description: Snapshot ID
          required: False
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
      ipfabric_snapshot:
        ipfabric_url: https://ipfabric.local
        ipfabric_token: thisIsMyToken
        state: present
"""

RETURN = r"""
msg:
  description: Message indicating failure or info about what has happened.
  returned: always
  type: str
"""


def request(**kwargs):
    module = kwargs["module"]
    try:
        response = open_url(
            kwargs["url"],
            headers=kwargs["headers"],
            validate_certs=kwargs["validate_certs"],
            method=kwargs["method"],
            timeout=5,
        )
    except urllib_error.HTTPError as e:
        message = json.loads(e.fp.read())
        module.fail_json(msg=f"{message['code']} {message['message']}")

    return response


def _get_snapshots(module, headers):
    url = module.params["ipfabric_url"] + "/api/v1/snapshots"
    response = request(
        headers=headers,
        url=url,
        validate_certs=module.params["validate_certs"],
        method="GET",
        module=module,
    )
    return json.loads(response.read())


def _does_snapshot_exist(module, headers):
    snapshots = _get_snapshots(module, headers)
    for snapshot in snapshots:
        if module.params["data"]["snapshot_id"] == snapshot["id"]:
            return True
    return False


def main():
    module_args = deepcopy(IPFABRIC_ARG_SPEC)
    module_args.update(
        dict(
            data=dict(
                type="dict",
                required=False,
                options=dict(
                    snapshot_id=dict(required=True, type="str"),
                ),
            ),
        ),
    )

    required_if = [("state", "absent", ["data"])]

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_if=required_if,
    )

    result = dict(changed=False, msg="")

    headers = {"X-API-Token": module.params["ipfabric_token"]}
    url = module.params["ipfabric_url"] + "/api/v1/snapshots"
    if module.params["state"] == "present":
        response = request(
            headers=headers,
            url=url,
            validate_certs=module.params["validate_certs"],
            method="POST",
            module=module,
        )

        response_json = json.loads(response.read())

        if response.status == 200 and response_json["success"]:
            snapshots = _get_snapshots(module=module, headers=headers)

            result[
                "msg"
            ] = f"Successfully kicked off a snapshot discovery ID: {snapshots[0]['id']}"  # noqa: E501
            result["info"] = snapshots[0]
            result["changed"] = True
        else:
            module.fail_json(msg=to_text(response.read()))

    elif module.params["state"] == "absent":
        if module.params["data"]:
            if _does_snapshot_exist(module, headers):

                url += f"/{module.params['data']['snapshot_id']}"
                response = request(
                    headers=headers,
                    url=url,
                    validate_certs=module.params["validate_certs"],
                    method="DELETE",
                    module=module,
                )
                if response.status == 204:
                    result[
                        "msg"
                    ] = f"Snapshot {module.params['data']['snapshot_id']} has been successfully deleted."  # noqa: E501
                    result["changed"] = True
            else:
                result[
                    "msg"
                ] = f"Snapshot {module.params['data']['snapshot_id']} does not exist."  # noqa: E501
        else:
            module.fail_json(msg="snapshot_id not set")

    module.exit_json(**result)


if __name__ == "__main__":
    main()
