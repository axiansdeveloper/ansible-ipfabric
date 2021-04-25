from __future__ import absolute_import, division, print_function

__metaclass__ = type

from ansible.module_utils.basic import env_fallback

SHARED_SPECS = dict(
    ipfabric=dict(
        type="dict",
        apply_defaults=True,
        options=dict(
            host=dict(
                type="str",
                required=True,
                fallback=(env_fallback, ["IPF_HOST"]),
            ),
            token=dict(
                type="str",
                required=True,
                no_log=True,
                fallback=(env_fallback, ["IPF_TOKEN"]),
            ),
            validate_certs=dict(
                type="raw",
                default=True,
                fallback=(env_fallback, ["IPF_CERTS"]),
            ),
            timeout=dict(
                type="float",
                fallback=(env_fallback, ["IPF_TIMEOUT"]),
            ),
        ),
    ),
)


def get_spec(*param_names):
    return dict((p, SHARED_SPECS[p]) for p in param_names)
