#
# Copyright 2024 Canonical, Ltd.
# See LICENSE file for licensing details
#

import json
import platform
import subprocess

import pytest
from k8s_test_harness import harness
from k8s_test_harness.util import env_util, k8s_util


def get_image_platform():
    arch = platform.machine()
    match arch:
        case "x86_64":
            return "amd64"
        case "aarch64":
            return "arm64"
        case _:
            raise Exception(f"Unsupported cpu platform: {arch}")


IMG_PLATFORM = get_image_platform()
INSTALL_NAME = "calico"

OPERATOR_NS = "default"
CALICO_SYSTEM_NS = "calico-system"
CALICO_API_NS = "calico-apiserver"

APISERVER_SPEC = r"""
# This section configures the Calico API server.
# For more information, see:
# https://docs.tigera.io/calico/latest/reference/installation/api
apiVersion: operator.tigera.io/v1
kind: APIServer
metadata:
  name: default
spec: {}
"""


def get_installation_spec(registry, repo):
    return f"""
# This section includes base Calico installation configuration.
# For more information, see: https://docs.tigera.io/calico/latest/reference/installation/api#operator.tigera.io/v1.Installation
apiVersion: operator.tigera.io/v1
kind: Installation
metadata:
  name: default
spec:
  # Image format:<registry>/<imagePath>/<imagePrefix><imageName>:<image-tag>
  registry: {registry}
  imagePath: "{repo}"
  imagePrefix: calico-

  # Configures Calico networking.
  calicoNetwork:
    ipPools:
    - name: default-ipv4-ippool
      blockSize: 26
      cidr: 192.168.0.0/16
      encapsulation: VXLANCrossSubnet
      natOutgoing: Disabled
      nodeSelector: !all()
"""


def get_image_sha256_digest(image):
    cmd = ["docker", "manifest", "inspect", image, "-v"]
    proc = subprocess.run(cmd, check=True, capture_output=True)
    out_json = json.loads(proc.stdout.decode("utf8"))
    return out_json["Descriptor"]["digest"]


def get_imageset_spec(operator_version, calico_version):
    spec = {
        "apiVersion": "operator.tigera.io/v1",
        "kind": "ImageSet",
        "metadata": {"name": f"calico-{calico_version}"},
        "spec": {"images": []},
    }

    # The Calico operator will error out if we pass other images than the ones
    # that it expects.
    calico_images = [
        "calico-node",
        "calico-cni",
        "calico-typha",
        "calico-kube-controllers",
        "calico-csi",
        "calico-apiserver",
        "calico-ctl",
        "calico-pod2daemon-flexvol",
        "calico-key-cert-provisioner",
        "calico-node-driver-registrar",
    ]
    images = list(zip(calico_images, [calico_version] * len(calico_images)))
    images.append(("calico-tigera-operator", operator_version))

    for image, version in images:
        rock = env_util.get_build_meta_info_for_rock_version(
            image, version, IMG_PLATFORM
        )
        sha256_digest = get_image_sha256_digest(rock.image)
        prefix = rock.image.split("/")[1]

        spec["spec"]["images"].append(
            {
                "image": f"{prefix}/{image}",
                "digest": sha256_digest,
            }
        )

    return json.dumps(spec)


def parse_image(image):
    # We expect the image to look like this:
    # ghcr.io/$repo/$name:$tag
    parts = image.split("/")
    return {
        "registry": parts[0],
        "repo": parts[1],
        "name": parts[2].split(":")[0],
        "tag": parts[2].split(":")[1],
    }


@pytest.mark.parametrize("operator_version,calico_version", [("v1.34.0", "v3.28.0")])
def test_calico(
    function_instance: harness.Instance, operator_version: str, calico_version: str
):
    operator_rock = env_util.get_build_meta_info_for_rock_version(
        "calico-tigera-operator", operator_version, IMG_PLATFORM
    )
    calicoctl_rock = env_util.get_build_meta_info_for_rock_version(
        "calico-ctl", calico_version, IMG_PLATFORM
    )

    op_img_info = parse_image(operator_rock.image)
    ctl_img_info = parse_image(calicoctl_rock.image)

    registry = op_img_info["registry"]
    repo = op_img_info["repo"]

    helm_command = k8s_util.get_helm_install_command(
        name=INSTALL_NAME,
        chart_name="tigera-operator",
        repository="https://docs.tigera.io/calico/charts",
        namespace=OPERATOR_NS,
        set_configs=[
            f"tigeraOperator.image={op_img_info['repo']}/{op_img_info['name']}",
            f"tigeraOperator.version={op_img_info['tag']}",
            f"tigeraOperator.registry={op_img_info['registry']}",
            f"calicoctl.image={ctl_img_info['registry']}/{ctl_img_info['name']}/{ctl_img_info['tag']}",
            f"calicoctl.tag={ctl_img_info['tag']}",
            # We'll use a custom installation spec, so we need to disable
            # the default one.
            "installation.enabled=false",
            "apiServer.enabled=false",
        ],
    )
    function_instance.exec(helm_command)

    k8s_util.wait_for_deployment(function_instance, "tigera-operator", OPERATOR_NS)

    installation_spec = get_installation_spec(registry, repo)
    imageset_spec = get_imageset_spec(operator_version, calico_version)
    apiserver_spec = APISERVER_SPEC

    function_instance.exec(
        ["k8s", "kubectl", "apply", "-f", "-"], input=bytes(installation_spec, "utf8")
    )
    function_instance.exec(
        ["k8s", "kubectl", "apply", "-f", "-"], input=bytes(imageset_spec, "utf8")
    )
    function_instance.exec(
        ["k8s", "kubectl", "apply", "-f", "-"], input=bytes(apiserver_spec, "utf8")
    )

    k8s_util.wait_for_deployment(
        function_instance,
        "calico-kube-controllers",
        CALICO_SYSTEM_NS,
        retry_delay_s=10,
        retry_times=12,
    )
    k8s_util.wait_for_deployment(
        function_instance,
        "calico-typha",
        CALICO_SYSTEM_NS,
        retry_delay_s=10,
        retry_times=12,
    )
    k8s_util.wait_for_deployment(
        function_instance,
        "calico-apiserver",
        CALICO_API_NS,
        retry_delay_s=10,
        retry_times=12,
    )
