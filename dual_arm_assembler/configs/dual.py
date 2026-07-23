"""양팔 구성 — 이 프로젝트의 기본 구성.

    base ── torso ─┬─ arm  ── endeffector  ── sensor1   1번 팔(+손목 센서)
                   │                                     sensor2 = 전역/머리 센서
                   └─ arm2 ── endeffector2 ── sensor3   2번 팔(+손목 센서, arm2_ 접두사)

코어(GUI·컴포저·충돌검사)는 슬롯 이름을 모른다. 이 파일이 슬롯 목록과 기본값만 정의하면
같은 코어가 단팔·양팔·그 밖의 구성으로 동작한다(→ configs/single.py 와 비교).

접두사를 강제하는 이유: 같은 모델(RB5·RG2)을 두 팔에 쓰면 `link0`·`tcp`·`rg2_hand` 가
그대로 충돌해 조립이 실패한다. 1번 팔은 모델 원래 이름을 유지하고(하위 산출물 계약),
2번 팔에만 슬롯 접두사를 붙인다.
"""
import math

from dual_arm_assembler import part_registry as reg

NAME = "양팔"
APP_NAME = "Dual-Arm Assembler — 양팔 로봇 어셈블러"

SLOTS = ["base", "torso", "arm", "endeffector", "arm2", "endeffector2",
         "sensor1", "sensor2", "sensor3"]

SLOT_LABELS = {
    "base": "① 베이스(모바일)",
    "torso": "② 상체(토르소)",
    "arm": "③ 로봇팔 1",
    "endeffector": "④ 엔드이펙터 1",
    "arm2": "⑤ 로봇팔 2",
    "endeffector2": "⑥ 엔드이펙터 2",
    "sensor1": "⑦ 센서 1 (1번 손목)",
    "sensor2": "⑧ 센서 2 (전역/머리)",
    "sensor3": "⑨ 센서 3 (2번 손목)",
}

# 체크해야 조립·저장에 들어가는 슬롯(기본 꺼짐).
#   단팔로 저장해 둔 mounts.yaml 을 열었을 때 없던 파트가 갑자기 생기지 않게 한다.
#   sensor3 도 여기 넣는다 — 2번 팔이 꺼져 있으면 붙일 곳이 없기 때문.
OPTIONAL_SLOTS = {"torso", "arm2", "endeffector2", "sensor3"}

# 2번 팔/그리퍼는 1번과 같은 모델 폴더를 읽는다(모델을 두 번 넣을 필요 없음).
#   센서 3 도 센서 1 폴더를 공유한다(센서 모델을 세 번 넣을 필요 없음).
SLOT_MODEL_ALIAS = {"arm2": "arm", "endeffector2": "endeffector", "sensor3": "sensor1"}

# 링크명 계약(prefix: "")을 무시하고 슬롯 접두사를 강제할 슬롯.
NO_CONTRACT_SLOTS = {"arm2", "endeffector2"}

BUILTIN_SLOT_MODELS = {
    "torso": [],                     # 폴더 드롭 모델만(models/torso/)
    "arm2": ["rb5_850e"],
    "endeffector2": ["onrobot_rg2"],
    "sensor3": ["d405", "d435i"],    # 2번 손목 카메라(기본 근접용 D405)
}

SLOT_COLORS = {
    "torso": "#6f7d8c",
    "arm2": "#d9a441",
    "endeffector2": "#6bb58a",
    "sensor3": "#c96a92",            # 센서 1(#c04a5e) 과 같은 계열, 구분되는 톤
}


def extra_mounts():
    """양팔 슬롯의 기본 결합값(켰을 때의 출발점). GUI 에서 조정하는 값이다."""
    from dual_arm_assembler.app import Mount
    return {
        # 상판 뒤쪽에 세운다 — 앞쪽(0,0,0.25)의 1번 팔 기본값과 부딪히지 않게.
        "torso": Mount("base", "base_link", [-0.20, 0.0, 0.115], [0, 0, 0]),
        # 우측 어깨(−Y)에서 팔이 바깥을 보도록 roll −90°. (좌측 어깨면 +90°)
        "arm2": Mount("torso", "torso_shoulder_r_link", [0.0, 0.0, 0.0],
                      [-math.pi / 2, 0, 0]),
        # ⚠ parent_frame 은 **모델 로컬 이름**을 쓴다 — 접두사는 컴포저가 붙인다
        #   (arm2 → arm2_tcp). 여기에 arm2_tcp 라고 적으면 접두사가 두 번 붙는다.
        "endeffector2": Mount("arm2", "tcp", [0.0, 0.0, 0.0], [0, 0, 0]),
        # 2번 손목 카메라 — 1번 손목 센서(sensor1)와 같은 자리에 대칭으로.
        #   parent_frame 은 모델 로컬 이름(rg2_hand) → 컴포저가 endeffector2_ 를 붙인다.
        "sensor3": Mount("endeffector2", "rg2_hand", [0.02, 0.0, 0.03], [0, 0, 0]),
    }


def apply():
    """레지스트리에 이 구성을 적용(멱등). 컴포저·GUI 공통."""
    reg.SLOTS[:] = list(SLOTS)
    reg.SLOT_LABELS.clear()
    reg.SLOT_LABELS.update(SLOT_LABELS)
    reg.OPTIONAL_SLOTS.clear()
    reg.OPTIONAL_SLOTS.update(OPTIONAL_SLOTS)
    reg.SLOT_MODEL_ALIAS.clear()
    reg.SLOT_MODEL_ALIAS.update(SLOT_MODEL_ALIAS)
    reg.NO_CONTRACT_SLOTS.clear()
    reg.NO_CONTRACT_SLOTS.update(NO_CONTRACT_SLOTS)
    for slot, ids in BUILTIN_SLOT_MODELS.items():
        reg.BUILTIN_SLOT_MODELS.setdefault(slot, list(ids))
    reg.reload_models()          # 슬롯이 늘었으니 모델 폴더를 다시 스캔
    return reg


def apply_gui():
    """GUI 까지 쓸 때: 색상·기본 결합값·앱 이름도 등록."""
    apply()
    from dual_arm_assembler import app as core_app
    core_app.SLOT_COLORS.update(SLOT_COLORS)
    core_app.EXTRA_DEFAULT_MOUNTS.clear()
    core_app.EXTRA_DEFAULT_MOUNTS.update(extra_mounts())
    core_app.APP_NAME = APP_NAME
    return core_app
