from monitoring.logs.cloudwatch import install


def test_install_noop_without_aws():
    install()
