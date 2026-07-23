"""파트 슬롯 & 모델 레지스트리.

슬롯: base / arm / endeffector / sensor1 / sensor2
각 모델은 xacro 소스(패키지 상대경로 또는 파일 직접) + xacro args
+ anchor(부모에 붙는 프레임)로 정의.
anchor 가 root 와 다르면(예: RG2 는 world 루트지만 rg2_hand 로 붙음) 로더가 오프셋 보정.

■ 코드 편집 없이 모델 추가하기 (폴더 드롭)
  모델 폴더(`<저장소>/models/<슬롯>/`,
  환경변수 RDA_MODELS_DIR 로 변경 가능)에 파일만 넣으면 조립기가 자동 인식한다.
  이 폴더가 **정본**이라 재빌드 없이 즉시 반영된다(경로 해석 근거는 paths.py).
    · <슬롯>/이름.urdf 또는 이름.xacro  → 무설정 등록(라벨=파일명, anchor=root)
    · <슬롯>/이름.yaml                  → 세밀 설정(label·anchor·args·소스 지정)
  yaml 스키마:
    label: "표시 이름"        # 생략 시 파일명
    file: my_arm.urdf         # 같은 폴더 파일(또는 절대경로)  ┐ 둘 중 하나
    pkg: myarm_description     # ament 패키지                   │
    xacro: urdf/my_arm.xacro   # share 기준 상대경로            ┘
    args: {use_x: "true"}     # (선택) xacro 인자
    anchor: tool0             # (선택) 부모에 붙는 프레임, 생략 시 root
    prefix: "arm_"            # (선택) 통합 URDF 에서 링크/조인트 이름 앞에 붙일 접두사.
                              #   생략 시 슬롯 자동("<슬롯>_") — 모델끼리 base_link 가
                              #   겹쳐도 안전. ""(빈 문자열) 이면 접두사 없음.
                              #   "{slot}" 은 슬롯명으로 치환된다. (composer.py 참조)
  조립기의 '모델 새로고침' 버튼으로 재시작 없이 다시 스캔한다.
"""
import os
import glob
import yaml

from dual_arm_assembler import paths as _paths

# 슬롯 순서(왼쪽 탭 순서). base 는 루트(부모 없음).
#   ★ 이 값은 **기본 구성(단팔)** 이고, 실행 시 configs.dual / configs.single 이 갈아끼운다.
#     코어는 슬롯 이름을 모른다 — 아래 목록과 훅만 보고 동작한다.
SLOTS = ["base", "arm", "endeffector", "sensor1", "sensor2"]

SLOT_LABELS = {
    "base": "① 베이스(모바일)",
    "arm": "② 로봇팔",
    "endeffector": "③ 엔드이펙터",
    "sensor1": "④ 센서 1",
    "sensor2": "⑤ 센서 2",
}

# ── 확장 훅 (다른 패키지가 슬롯 구성을 갈아끼울 때 쓰는 자리) ──────────────
#   이 파일 자체는 **단팔 구성**이 정본이다. 양팔 구성은 별도 패키지
#   `rda_dual_assembler` 가 아래 값들을 채워 넣어 만든다(코드 복제 없이 구성만 교체).
#
# 기본값이 '꺼짐'인 슬롯 — 체크해야 조립·저장에 들어간다.
OPTIONAL_SLOTS = set()
# 모델 목록을 빌려오는 슬롯: {빌리는 슬롯: 원본 슬롯 폴더}
SLOT_MODEL_ALIAS = {}
# 링크명 계약(prefix: "")을 적용하지 않고 슬롯 접두사를 강제할 슬롯.
#   같은 모델을 두 슬롯에 쓰면 link0·tcp 같은 계약 이름이 그대로 충돌하기 때문.
NO_CONTRACT_SLOTS = set()

# 내장 모델 레지스트리: id -> dict
#   pkg          : ament 패키지명 (mesh package:// 및 xacro 위치 기준)
#   xacro        : 패키지 share 기준 상대 경로
#   file         : (pkg/xacro 대신) urdf/xacro 파일 절대경로 — 폴더 드롭용
#   args         : xacro 인자 dict
#   anchor       : 부모에 부착되는 프레임(=mount joint 의 child). None 이면 root 사용.
BUILTIN_MODELS = {
    "scout_v2": {
        "label": "Agilex Scout 2.0",
        "pkg": "scout_description",
        "xacro": "urdf/scout_v2.xacro",
        "args": {},
        "anchor": None,  # base_link
        # 통합 URDF 링크명 계약(base_link) 보존 → prefix 없음. composer.resolve_prefix 참조.
        "prefix": "",
    },
    "rb5_850e": {
        "label": "Rainbow RB5-850e",
        "pkg": "rbpodo_description",
        "xacro": "robots/rb5_850e.urdf.xacro",
        "args": {},
        "anchor": None,  # link0
        # 통합 URDF 링크명 계약(link0..6·tcp) 보존 → prefix 없음. composer.resolve_prefix 참조.
        "prefix": "",
    },
    "onrobot_rg2": {
        "label": "OnRobot RG2",
        "pkg": "dual_arm_assembler",
        "xacro": "urdf/rg2/onrobot_rg2_standalone.urdf.xacro",
        "args": {},
        "anchor": "rg2_hand",  # world 루트지만 rg2_hand 로 부착
        # 통합 URDF 링크명 계약(rg2_hand) 보존 → prefix 없음. composer.resolve_prefix 참조.
        "prefix": "",
    },
    "d405": {
        "label": "RealSense D405 (eye-in-hand)",
        "pkg": "realsense2_description",
        "xacro": "urdf/test_d405_camera.urdf.xacro",
        "args": {"use_nominal_extrinsics": "true"},
        "anchor": None,  # base_link
    },
    "d435i": {
        "label": "RealSense D435i (eye-to-hand)",
        "pkg": "realsense2_description",
        "xacro": "urdf/test_d435i_camera.urdf.xacro",
        "args": {"use_nominal_extrinsics": "true"},
        "anchor": None,  # base_link
    },
}

# 슬롯별 내장 모델 후보(첫 번째가 기본값). 외부 폴더 모델은 뒤에 append.
BUILTIN_SLOT_MODELS = {
    "base": ["scout_v2"],
    "arm": ["rb5_850e"],
    "endeffector": ["onrobot_rg2"],
    "sensor1": ["d405", "d435i"],
    "sensor2": ["d435i", "d405"],
}

# 통합 xacro 내보내기: 슬롯 -> 매크로 호출 정보.
# (rda_robot.urdf.xacro 가 mounts.yaml 을 읽어 parent/xyz/rpy 를 채운다)
EXPORT_MACRO = {
    "arm": {
        "kind": "rb_6dof",
        "include": "$(find rbpodo_description)/robots/rb_6dof.xacro",
    },
    "endeffector": {
        "kind": "onrobot_rg2",
        "include": "$(find dual_arm_assembler)/urdf/rg2/onrobot_rg2_macro.xacro",
    },
    "sensor1": {
        "kind": "sensor_d405",
        "include": "$(find realsense2_description)/urdf/_d405.urdf.xacro",
    },
    "sensor2": {
        "kind": "sensor_d435i",
        "include": "$(find realsense2_description)/urdf/_d435i.urdf.xacro",
    },
}


def models_dir():
    """모델 드롭 폴더(정본=소스 트리). 해석 규칙·근거는 paths.py 참조."""
    return _paths.models_dir()


def load_external_models():
    """models_dir/<슬롯>/ 스캔 → (models, slot_models_add).

    지원: *.yaml(디스크립터) / *.urdf·*.xacro(무설정 드롭, anchor=root).
    같은 이름의 yaml 이 있으면 urdf/xacro 대신 yaml 설정을 쓴다.
    """
    models, slot_add = {}, {s: [] for s in SLOTS}
    root = models_dir()
    for slot in SLOTS:
        # arm2/endeffector2 는 자기 폴더가 없으면 1번 팔 폴더를 그대로 빌려 쓴다.
        sd = os.path.join(root, slot)
        if not os.path.isdir(sd) and slot in SLOT_MODEL_ALIAS:
            sd = os.path.join(root, SLOT_MODEL_ALIAS[slot])
        if not os.path.isdir(sd):
            continue
        handled = set()   # yaml 이 이미 다룬 파일명
        # 1) yaml 디스크립터
        for y in sorted(glob.glob(os.path.join(sd, "*.yaml"))):
            stem = os.path.splitext(os.path.basename(y))[0]
            try:
                with open(y) as f:
                    d = yaml.safe_load(f) or {}
            except Exception:
                continue
            m = {"label": d.get("label", stem),
                 "args": d.get("args") or {},
                 "anchor": d.get("anchor")}
            # prefix 는 '미지정'과 '빈 문자열'이 다르다(미지정=슬롯 자동, ""=prefix 없음)
            if "prefix" in d:
                m["prefix"] = d["prefix"]
            if d.get("file"):
                fp = d["file"]
                if not os.path.isabs(fp):
                    fp = os.path.join(sd, fp)
                m["file"] = fp
                handled.add(os.path.basename(fp))
            elif d.get("pkg") and d.get("xacro"):
                m["pkg"], m["xacro"] = d["pkg"], d["xacro"]
            else:
                continue  # 소스 미지정 → 스킵
            mid = f"{slot}__{stem}"
            models[mid] = m
            slot_add[slot].append(mid)
            handled.add(stem + ".urdf")
            handled.add(stem + ".xacro")
        # 2) 무설정 urdf/xacro 드롭
        for ext in ("*.urdf", "*.xacro"):
            for fp in sorted(glob.glob(os.path.join(sd, ext))):
                if os.path.basename(fp) in handled:
                    continue
                stem = os.path.splitext(os.path.basename(fp))[0]
                mid = f"{slot}__{stem}"
                if mid in models:
                    continue
                models[mid] = {"label": stem, "file": fp,
                               "args": {}, "anchor": None}
                slot_add[slot].append(mid)
    return models, slot_add


# 런타임 레지스트리(내장 + 외부). reload_models 로 재스캔.
MODELS = {}
SLOT_MODELS = {}


def reload_models():
    """내장 + 외부 폴더 모델을 다시 읽어 MODELS/SLOT_MODELS 갱신."""
    global MODELS, SLOT_MODELS
    MODELS = dict(BUILTIN_MODELS)
    SLOT_MODELS = {s: list(v) for s, v in BUILTIN_SLOT_MODELS.items()}
    try:
        ext, add = load_external_models()
    except Exception:
        ext, add = {}, {}
    MODELS.update(ext)
    for s, ids in add.items():
        for i in ids:
            if i not in SLOT_MODELS.get(s, []):
                SLOT_MODELS.setdefault(s, []).append(i)
    return MODELS, SLOT_MODELS


reload_models()


def default_model(slot):
    """슬롯의 기본 모델 id. 후보가 하나도 없으면 None(예: torso 폴더가 비었을 때)."""
    cands = SLOT_MODELS.get(slot) or []
    return cands[0] if cands else None
