from __future__ import absolute_import, division, print_function

__metaclass__ = type


class ModuleDocFragment(object):
    DOCUMENTATION = r"""
options:
  ipfabric:
    description:
      - IPFabric instance information.
    type: dict
    suboptions:
      host:
        description:
          - The IPFabric host name.
          - If not set, the value of the C(IPF_HOST) environment
            variable will be used.
        required: true
        type: str
      token:
        description:
          - The token created within IPFabric to
            Authorize API access (must have snapshot permissions).
          - If not set, the value of the C(IPF_TOKEN) environment
            variable will be used.
        required: true
        type: str
      validate_certs:
        description:
          - IF C(no), SSL certificates will not be calidated.
            This should only be used on personally controlled
            sites using self-signed certificates.
          - If not set, the value of the C(IPF_CERTS) environment
            variable will be used.
        required: false
        type: raw
      timeout:
        description:
          - Timeout in seconds for the connection with the IPFabric instance.
          - If not set, the value of the C(IPF_TIMEOUT) environment
            variable will be used.
        type: float
"""
