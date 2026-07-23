# 도구와 모듈 — 무엇이 무엇을 하는가

이 저장소가 제공하는 실행 명령 3개와, 그것들이 쓰는 내부 모듈의 역할을 정리했다.
"어디를 고쳐야 하나"를 찾을 때 여기부터 보면 된다.

## 실행 명령

| 명령 | 하는 일 |
|------|---------|
| `ros2 run dual_arm_assembler assembler` | 조립 GUI. 파트를 고르고 결합 위치를 맞춰 `mounts.yaml` 저장 |
| `ros2 run dual_arm_assembler compose_urdf` | `mounts.yaml` → 통합 URDF 1개 |
| `ros2 run dual_arm_assembler mesh2urdf` | 3D 파일 → 강체 1링크 URDF + 모델 폴더 등록 → [상세](mesh2urdf.md) |
| `bash scripts/setup_vendor_models.sh` | 모델 라이브러리(UR·Robotiq·Clearpath …)를 각 원저작 저장소에서 clone·빌드 |

### assembler (GUI)

```bash
ros2 run dual_arm_assembler assembler
```

- 왼쪽: 슬롯별 모델 선택 + `3D에 표시` 체크(=조립·저장 포함 여부)
- 가운데: 3D 뷰. 선택 중인 파트는 주황, 충돌 파트는 빨강
- 오른쪽: 붙일 파트 · 부착 프레임 · XYZ/RPY · 관절 초기 자세
- 아래: 배경 기준 로봇 위치(작업 환경 안에서 베이스를 옮길 때)

저장(`Ctrl+S`)하면 `mounts.yaml` 이 만들어진다. 위치는 `RDA_MOUNTS_FILE` 로 바꿀 수 있고,
기본은 저장소 루트다.

**자충돌 표시**: 파트 메시가 실제로 교차하면 빨갛게 칠하고 상태줄에 쌍을 적는다.
설계상 원래 겹치는 결합(플랜지가 상판에 얹히는 등)은 `현재 겹침 무시` 로 기준에 등록하면
그 뒤로는 **새로 생긴** 겹침만 경고한다. 슬롯을 새로 켜면 그 파트의 겹침은 자동으로 기준에
들어간다(처음부터 켜져 있던 파트와 같은 대우).

### compose_urdf

```bash
ros2 run dual_arm_assembler compose_urdf --mounts mounts.yaml -o robot.urdf [--name my_robot]
```

`mounts.yaml` 의 슬롯별 모델·부모·부착 프레임·오프셋을 읽어 URDF 하나로 합친다.
GUI 와 **같은 모델 정의**를 읽으므로 앱 화면과 결과 형상이 일치한다.

조립 절차(자세한 이유는 `composer.py` 머리말):

1. 슬롯별로 xacro → URDF 생성
2. **re-root** — 모델이 자체적으로 만든 `world` 루트 등 anchor 위쪽 조상을 잘라낸다
   (URDF 는 루트가 하나여야 한다). 자를 조인트가 가동관절이거나 다른 서브트리를 잃게 되면
   **즉시 실패**한다 — 조용히 형상이 바뀌는 것보다 낫다
3. **접두사** — 링크·조인트·머티리얼 이름에 슬롯 접두사를 붙여 충돌 회피
4. 병합 + 슬롯별 마운트 조인트 생성(부모 슬롯의 부착 프레임 → 자식 anchor)
5. 이름 충돌·루트 다중 검사

## 내부 모듈

| 파일 | 역할 | 고칠 일이 생기는 경우 |
|------|------|----------------------|
| `app.py` | 조립 GUI(PyQt5 + pyvista). 슬롯 패널·3D 뷰·결합값 편집·저장/불러오기 | UI 동작, 기본 결합값 |
| `composer.py` | 통합 URDF 조립(re-root · 접두사 · 마운트 조인트 · 검증) | 조립 규칙, 실패 메시지 |
| `collision.py` | 실시간 자충돌 검사(trimesh + python-fcl). 링크 단위, 파트 변환만 갱신 | 무시 규칙, 성능 |
| `urdf_loader.py` | xacro → URDF → yourdfpy 로드, `package://` 해석, 링크별 메시 추출 | 모델 로드 실패 대응 |
| `part_registry.py` | 슬롯·모델 레지스트리. 모델 폴더 스캔(yaml/urdf/xacro), 접두사 규칙 | 모델 인식 규칙 |
| `paths.py` | 모델 폴더 경로 해석(환경변수 → 소스 트리 → 설치 share) | 폴더 위치 정책 |
| `mesh2urdf.py` | 3D 파일 → 강체 URDF 변환 | 변환 옵션 |
| `assembly.py` | 슬롯 트리에서 각 파트의 world 변환 계산 | 결합 수학 |
| `configs/dual.py` | **슬롯 구성**(목록·라벨·기본 결합값·접두사 규칙) | 구성 변경 — 아래 참조 |

## 구성을 바꾸고 싶을 때

코어는 슬롯 이름을 모른다. `configs/dual.py` 가 목록을 정의하고 코어는 그것만 본다.
그래서 **팔 3개**, **상체 없는 구성**, **센서 5개** 같은 변형은 코어를 건드리지 않고 만든다.

```python
# configs/triple.py (예시)
SLOTS = ["base", "torso", "arm", "endeffector", "arm2", "endeffector2", "arm3", "endeffector3"]
SLOT_LABELS = {...}
OPTIONAL_SLOTS = {"arm3", "endeffector3"}          # 기본 꺼짐
SLOT_MODEL_ALIAS = {"arm3": "arm", "endeffector3": "endeffector"}   # 모델 폴더 공유
NO_CONTRACT_SLOTS = {"arm2", "endeffector2", "arm3", "endeffector3"} # 접두사 강제
```

`cli.py` 의 `_config()` 가 이 모듈을 고르게 하면 끝이다.

**확장 훅 4개**가 코어에 뚫려 있다:

| 훅 | 의미 |
|----|------|
| `OPTIONAL_SLOTS` | 체크해야 조립·저장에 들어가는 슬롯(기본 꺼짐) |
| `SLOT_MODEL_ALIAS` | 모델 목록을 빌려올 폴더 `{빌리는 슬롯: 원본 슬롯}` |
| `NO_CONTRACT_SLOTS` | 모델이 `prefix: ""` 라도 슬롯 접두사를 강제할 슬롯 |
| `EXTRA_DEFAULT_MOUNTS` | 슬롯별 기본 결합값(app 모듈) |

## 링크 이름 규칙 (중요)

- 기본은 **슬롯 접두사 자동**(`arm_base_link`, `sensor1_camera_link` …). 서로 다른 모델이
  같은 이름(`base_link`)을 쓰는 일이 흔해서, 접두사가 없으면 조합할 때마다 충돌한다.
- 모델 yaml 에 `prefix: ""` 를 주면 **원래 이름이 보존**된다. 하위 도구(SRDF·기구학
  스크립트 등)가 특정 이름에 묶여 있을 때 쓴다. 동봉된 Scout/RB5/RG2 가 그렇게 돼 있다.
- **2번 팔·그리퍼·센서 3 은 접두사가 강제**된다(`NO_CONTRACT_SLOTS`). 같은 모델을 두 팔에
  쓰면 `link0`·`tcp`·`rg2_hand` 가 그대로 충돌하기 때문이다.
- **부착 프레임은 접두사 없는 모델 로컬 이름**으로 적는다. 접두사는 컴포저가 붙인다.
  예: 2번 그리퍼를 2번 팔에 붙일 때 `parent_frame: tcp` (❌ `arm2_tcp`).

## mounts.yaml 형식

```yaml
mounts:
  torso:
    model: torso__column_torso      # 모델 id
    parent_slot: base               # 어느 슬롯에 붙는지
    parent_frame: base_link         # 부모의 어느 프레임에(모델 로컬 이름)
    xyz: [-0.20, 0.0, 0.115]
    rpy: [0.0, 0.0, 0.0]
  arm:
    model: rb5_850e
    parent_slot: torso
    parent_frame: torso_shoulder_l_link
    xyz: [0.0, 0.0, 0.0]
    rpy: [1.570796, 0.0, 0.0]
models:                             # 슬롯별 선택 모델(구버전 호환 겸 요약)
  base: scout_v2
  torso: torso__column_torso
initial_pose:                       # 관절 시작 자세(joint 이름 → rad)
  shoulder: 0.0
base_placement:                     # 배경 안에서의 로봇 위치(선택)
  x: 0.0
  y: 0.0
  z: 0.0
  yaw_deg: 0.0
```

모델 id 규칙: 내장 모델은 `rb5_850e` 처럼 짧은 이름, 폴더 드롭 모델은 `<슬롯>__<파일명>`
(예: `torso__column_torso`). 슬롯을 공유하는 2번 팔에서는 `arm2__ur10e` 처럼 빌린 슬롯
이름이 붙는다.

## 환경변수

| 변수 | 기본 | 용도 |
|------|------|------|
| `RDA_MODELS_DIR` | 저장소 `models/` | 모델 폴더를 다른 곳에 둘 때 |
| `RDA_MOUNTS_FILE` | 저장소 루트 `mounts.yaml` | 조립 결과 저장 위치 |
