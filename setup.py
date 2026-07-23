from glob import glob
import os

from setuptools import setup

package_name = "dual_arm_assembler"


def data_tree(src_root, dst_root):
    """폴더 트리를 data_files 형식으로 (설치 share 에 그대로 복사)."""
    out = []
    for d, _dirs, files in os.walk(src_root):
        if not files:
            continue
        rel = os.path.relpath(d, src_root)
        dst = os.path.join(dst_root, "" if rel == "." else rel)
        out.append((dst, [os.path.join(d, f) for f in files]))
    return out


setup(
    name=package_name,
    version="0.1.0",
    packages=[package_name, package_name + ".configs"],
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml", "README.md", "LICENSE", "NOTICE"]),
        ("share/" + package_name + "/scripts", glob("scripts/*")),
    ] + data_tree("models", "share/" + package_name + "/models")
      + data_tree("meshes", "share/" + package_name + "/meshes")
      + data_tree("urdf", "share/" + package_name + "/urdf"),
    install_requires=["setuptools", "PyQt5", "pyvista", "pyvistaqt", "trimesh",
                      "yourdfpy", "pycollada", "python-fcl", "numpy", "PyYAML"],
    zip_safe=False,
    maintainer="kim",
    maintainer_email="akswnddl255@gmail.com",
    description="양팔 로봇 조립기 — GUI 로 파트를 결합해 통합 URDF 를 만든다",
    license="Apache-2.0",
    entry_points={
        "console_scripts": [
            # ROS2 워크스페이스: ros2 run dual_arm_assembler <이름>
            "assembler = dual_arm_assembler.cli:gui",
            "compose_urdf = dual_arm_assembler.cli:compose",
            "mesh2urdf = dual_arm_assembler.mesh2urdf:main",
            # pip 설치 시 쓰는 짧은 이름
            "dual-assembler = dual_arm_assembler.cli:gui",
            "dual-compose-urdf = dual_arm_assembler.cli:compose",
        ],
    },
)
