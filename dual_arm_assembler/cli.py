#!/usr/bin/env python3
"""실행 진입점 — 구성(단팔/양팔)을 골라 코어를 띄운다.

  dual-assembler            양팔 GUI            (= ros2 run dual_arm_assembler assembler)
  dual-assembler --single   단팔 GUI
  dual-compose-urdf …       통합 URDF 생성(기본 양팔 구성, --single 로 단팔)
"""
import sys


def _pick_config(argv):
    """--single / --dual 플래그를 소비하고 구성 모듈을 돌려준다(기본=양팔)."""
    single = "--single" in argv
    argv[:] = [a for a in argv if a not in ("--single", "--dual")]
    if single:
        from dual_arm_assembler.configs import single as cfg
    else:
        from dual_arm_assembler.configs import dual as cfg
    return cfg


def gui(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    cfg = _pick_config(argv)
    core_app = cfg.apply_gui()
    return core_app.main()


def compose(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    cfg = _pick_config(argv)
    cfg.apply()
    from dual_arm_assembler import composer
    return composer.main(argv)


if __name__ == "__main__":
    gui()
