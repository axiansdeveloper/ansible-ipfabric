[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)
![Release](https://img.shields.io/github/v/release/axiansdeveloper/ansible-ipfabric)

# Ansible Collection - axiansdeveloper.ipfabric

[IPFabric](https://ipfabric.io/) inventory for [Ansible](https://github.com/ansible/ansible).

> This collection is currently heavily inspired by the great work over at the [Netbox Ansible](https://github.com/netbox-community/ansible_modules) collection.

## Requirements
The axiansdeveloper.ipfabric collection only supports IPFabric versions of 3.7 and greater due to support for [API tokens](https://ipfabric.atlassian.net/wiki/spaces/ND/pages/1448575064/API+tokens).

- IPFabric 3.7+
- Python 3.6+
- Ansible 2.9+
- IPFabric read-only token for `inventory`

## Installing axiansdeveloper.ipfabric

Run the following command to install the axiansdeveloper.ipfabric collection:

```bash
ansible-galaxy collection install axiansdeveloper.ipfabric
```

## Inventory

```yaml
# ipfabric_inventory.yml file in YAML format
# Example command line: ansible-inventory -v --list -i ipfabric_inventory.yml

---
plugin: axiansdeveloper.ipfabric.inventory
api_endpoint: "https://192.168.3.1/api/v1"
validate_certs: True
token: 1234567890abcdefghijklmnop

# group_by allows for grouping based on different items such as sites, vendors etc
group_by:
  - sites
```
