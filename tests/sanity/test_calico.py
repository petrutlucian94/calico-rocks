#
# Copyright 2024 Canonical, Ltd.
# See LICENSE file for licensing details
#

import pytest
from k8s_test_harness.util import docker_util, env_util

# In the future, we may also test ARM
IMG_PLATFORM = "amd64"

CALICO_VERSIONS = ["v3.28.0"]
OPERATOR_VERSIONS = ["v1.34.0"]


@pytest.mark.parametrize("version", CALICO_VERSIONS)
def test_apiserver(version: str):
    rock = env_util.get_build_meta_info_for_rock_version(
        "calico-apiserver", version, IMG_PLATFORM
    )

    expected_helpstr = "run a calico api server"

    docker_run = docker_util.run_in_docker(rock.image, ["/code/apiserver", "--help"])
    assert expected_helpstr in docker_run.stdout


@pytest.mark.parametrize("version", CALICO_VERSIONS)
def test_cni(version: str):
    rock = env_util.get_build_meta_info_for_rock_version(
        "calico-cni", version, IMG_PLATFORM
    )

    expected_files = [
        "/opt/cni/bin/calico",
        "/opt/cni/bin/install",
        "/opt/cni/bin/calico-ipam",
    ]
    docker_util.ensure_image_contains_paths(rock.image, expected_files)

    docker_run = docker_util.run_in_docker(
        rock.image, ["/opt/cni/bin/calico", "--help"]
    )
    assert "Usage of Calico:" in docker_run.stderr

    docker_run = docker_util.run_in_docker(
        rock.image, ["/opt/cni/bin/calico-ipam", "--help"]
    )
    assert "Usage of calico-ipam:" in docker_run.stderr


@pytest.mark.parametrize("version", CALICO_VERSIONS)
def test_csi(version: str):
    rock = env_util.get_build_meta_info_for_rock_version(
        "calico-csi", version, IMG_PLATFORM
    )

    docker_run = docker_util.run_in_docker(
        rock.image, ["/usr/bin/csi-driver", "--help"]
    )
    assert "Kubelet communicates with the CSI plugin" in docker_run.stderr


@pytest.mark.parametrize("version", CALICO_VERSIONS)
def test_ctl(version: str):
    rock = env_util.get_build_meta_info_for_rock_version(
        "calico-ctl", version, IMG_PLATFORM
    )

    docker_run = docker_util.run_in_docker(rock.image, ["/usr/bin/ctl", "--help"])
    assert "The calicoctl command line tool is used to" in docker_run.stdout


@pytest.mark.parametrize("version", CALICO_VERSIONS)
def test_kube_controllers(version: str):
    rock = env_util.get_build_meta_info_for_rock_version(
        "calico-kube-controllers", version, IMG_PLATFORM
    )

    docker_run = docker_util.run_in_docker(
        rock.image, ["/usr/bin/kube-controllers", "--help"]
    )
    assert "Usage of /usr/bin/kube-controllers" in docker_run.stderr

    docker_run = docker_util.run_in_docker(
        rock.image,
        ["/usr/bin/check-status", "--help"],
        check_exit_code=False,
    )
    assert "Usage of check-status:" in docker_run.stderr


@pytest.mark.parametrize("version", CALICO_VERSIONS)
def test_node(version: str):
    rock = env_util.get_build_meta_info_for_rock_version(
        "calico-node", version, IMG_PLATFORM
    )

    expected_files = [
        "/etc/rc.local",
        "/etc/nsswitch.conf",
        "/etc/calico/felix.cfg",
        "/etc/service/available/cni/run",
        "/usr/lib/calico/bpf/filter.o",
        "/sbin/start_runit",
        "/sbin/restart-calico-confd",
        "/bin/bird",
        "/bin/bird6",
        "/bin/birdcl",
        "/bin/birdcl6",
        "/bin/bpftool",
        "/bin/calico-node",
        "/bin/mountns",
    ]
    docker_util.ensure_image_contains_paths(rock.image, expected_files)

    docker_run = docker_util.run_in_docker(
        rock.image, ["/bin/calico-node", "--help"], check_exit_code=False
    )
    assert "Usage of Calico:" in docker_run.stderr

    docker_run = docker_util.run_in_docker(rock.image, ["/bin/bird", "--help"])
    assert "Usage: bird" in docker_run.stderr

    docker_run = docker_util.run_in_docker(rock.image, ["/bin/bird6", "--help"])
    assert "Usage: bird6" in docker_run.stderr

    docker_run = docker_util.run_in_docker(rock.image, ["/bin/bpftool", "--help"])
    assert "Usage: bpftool" in docker_run.stderr


@pytest.mark.parametrize("version", CALICO_VERSIONS)
def test_flexvol(version: str):
    rock = env_util.get_build_meta_info_for_rock_version(
        "calico-pod2daemon-flexvol", version, IMG_PLATFORM
    )

    docker_run = docker_util.run_in_docker(
        rock.image, ["/usr/local/bin/flexvol", "--help"]
    )
    assert "flexvoldrv [command]" in docker_run.stdout

    docker_run = docker_util.run_in_docker(
        rock.image, ["/usr/local/bin/flexvol.sh", "--help"], check_exit_code=False
    )
    assert "usage: /usr/local/bin/flexvol.sh" in docker_run.stdout


@pytest.mark.parametrize("version", CALICO_VERSIONS)
def test_typha(version: str):
    rock = env_util.get_build_meta_info_for_rock_version(
        "calico-typha", version, IMG_PLATFORM
    )

    expected_files = [
        "/etc/calico/typha.cfg",
        "/usr/bin/calico-typha",
    ]
    docker_util.ensure_image_contains_paths(rock.image, expected_files)

    docker_run = docker_util.run_in_docker(
        rock.image, ["/usr/bin/calico-typha", "--help"]
    )
    assert "Typha, Calico's fan-out proxy." in docker_run.stdout


@pytest.mark.parametrize("version", CALICO_VERSIONS)
def test_key_cert_provisioner(version: str):
    rock = env_util.get_build_meta_info_for_rock_version(
        "calico-key-cert-provisioner", version, IMG_PLATFORM
    )

    docker_run = docker_util.run_in_docker(rock.image, ["/usr/bin/key-cert-provisioner", "--help"])
    assert "Usage of /usr/bin/key-cert-provisioner" in docker_run.stderr


@pytest.mark.parametrize("version", CALICO_VERSIONS)
def test_node_driver_registrar(version: str):
    rock = env_util.get_build_meta_info_for_rock_version(
        "calico-node-driver-registrar", version, IMG_PLATFORM
    )

    docker_run = docker_util.run_in_docker(rock.image, ["node-driver-registrar", "--help"])
    assert "Usage of node-driver-registrar" in docker_run.stderr


@pytest.mark.parametrize("version", OPERATOR_VERSIONS)
def test_operator(version: str):
    rock = env_util.get_build_meta_info_for_rock_version(
        "calico-tigera-operator", version, IMG_PLATFORM
    )

    docker_run = docker_util.run_in_docker(rock.image, ["/usr/bin/operator", "--help"])
    assert "Usage of /usr/bin/operator" in docker_run.stderr
