#
# Copyright 2024 Canonical, Ltd.
# See LICENSE file for licensing details
#

import pytest
from k8s_test_harness import harness
from k8s_test_harness.util import env_util, k8s_util

IMG_PLATFORM = "amd64"
INSTALL_NAME = "calico"
OPERATOR_NS = "tigera-operator"


@pytest.mark.parametrize("version", ["v1.34.0"])
def test_calico(function_instance: harness.Instance, version: str):
    rock = env_util.get_build_meta_info_for_rock_version(
        "calico-tigera-operator", version, IMG_PLATFORM
    )

    # This helm chart requires the registry to be separated from the image.
    rock_image = rock.image
    registry = "docker.io"
    parts = rock_image.split("/")
    if len(parts) > 1:
        registry = parts[0]
        rock_image = "/".join(parts[1:])

    helm_command = k8s_util.get_helm_install_command(
        name=INSTALL_NAME,
        chart_name="tigera-operator",
        repository="https://docs.tigera.io/calico/charts",
        images=[k8s_util.HelmImage(uri=rock_image)],
        namespace=OPERATOR_NS,
        set_configs=[f"image.registry={registry}"],
    )
    function_instance.exec(helm_command)

    k8s_util.wait_for_deployment(function_instance, "tigera-operator", OPERATOR_NS)

    # TODO: use the calico operator to deploy the other components
