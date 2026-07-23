#!/usr/bin/env python3
"""실행 진입점.

  ros2 run dual_arm_assembler assembler        양팔 조립 GUI
  ros2 run dual_arm_assembler compose_urdf …   mounts.yaml → 통합 URDF

슬롯 구성은 configs/dual.py 가 정의한다. 다른 구성(팔 3개 등)을 쓰고 싶으면 그 파일을
본떠 configs/ 에 하나 더 만들고 아래 _config() 가 그걸 고르게 하면 된다 — 코어는 슬롯
이름을 모르므로 코어 코드는 손대지 않는다.
"""
import sys


def _config():
    from dual_arm_assembler.configs import dual
    return dual


def gui(argv=None):
    cfg = _config()
    core_app = cfg.apply_gui()
    return core_app.main()


def compose(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    _config().apply()
    from dual_arm_assembler import composer
    return composer.main(argv)


if __name__ == "__main__":
    gui()
