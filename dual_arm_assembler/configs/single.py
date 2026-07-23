"""단팔 구성 — 코어 기본값 그대로(base → arm → endeffector + 센서 2).

양팔 구성(configs/dual.py)과 같은 코어를 쓴다. 두 구성의 차이는 이 두 파일뿐이다.
"""
from dual_arm_assembler import part_registry as reg

NAME = "단팔"
APP_NAME = "Assembler — 로봇 어셈블러(단팔)"

SLOTS = ["base", "arm", "endeffector", "sensor1", "sensor2"]

SLOT_LABELS = {
    "base": "① 베이스(모바일)",
    "arm": "② 로봇팔",
    "endeffector": "③ 엔드이펙터",
    "sensor1": "④ 센서 1",
    "sensor2": "⑤ 센서 2",
}


def apply():
    reg.SLOTS[:] = list(SLOTS)
    reg.SLOT_LABELS.clear()
    reg.SLOT_LABELS.update(SLOT_LABELS)
    reg.OPTIONAL_SLOTS.clear()
    reg.SLOT_MODEL_ALIAS.clear()
    reg.NO_CONTRACT_SLOTS.clear()
    reg.reload_models()
    return reg


def apply_gui():
    apply()
    from dual_arm_assembler import app as core_app
    core_app.EXTRA_DEFAULT_MOUNTS.clear()
    core_app.APP_NAME = APP_NAME
    return core_app
