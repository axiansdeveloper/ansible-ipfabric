IPFABRIC_ARG_SPEC = dict(
    ipfabric_url=dict(type="str", required=True),
    ipfabric_token=dict(type="str", required=True, no_log=True),
    state=dict(
        required=False,
        default="present",
        choices=["present", "absent"],
    ),
    validate_certs=dict(type="raw", default=True),
)
