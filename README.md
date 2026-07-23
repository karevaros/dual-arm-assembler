# dual-arm-assembler

**양팔 로봇을 마우스로 조립해 통합 URDF 를 만드는 도구.**
모바일 베이스 · 상체(토르소) · 로봇팔 2 · 그리퍼 2 · 센서 2 를 골라 결합 위치를 맞추면,
하나의 URDF 로 합쳐 준다. 결합 중 자충돌은 실시간으로 빨갛게 표시된다.

ROS 2 Humble · Python · PyQt5.

```bash
ros2 run dual_arm_assembler assembler              # 양팔 조립 GUI
ros2 run dual_arm_assembler assembler --single     # 단팔 구성으로
ros2 run dual_arm_assembler compose_urdf --mounts mounts.yaml -o robot.urdf
```

---

## 왜 이 도구인가

로봇을 새로 구성할 때마다 xacro 에 분기를 추가하고, 링크 이름 충돌을 손으로 피하고,
결합 오프셋을 숫자로 찍어 넣는 일이 반복된다. 이 도구는 그 과정을 **모델 폴더 + GUI +
컴포저**로 바꾼다.

- **모델은 폴더에 떨어뜨리면 끝** — `models/<슬롯>/` 에 urdf·xacro·yaml 을 넣으면 드롭다운에
  자동 등록된다. 코드 수정도 재빌드도 필요 없다.
- **이름 충돌은 자동 회피** — 슬롯별 접두사를 붙인다. 같은 팔 모델을 양쪽에 써도 안전하다.
- **표준 URDF 를 그대로 먹는다** — 모델이 자체 `world` 루트를 만들어도 anchor 기준으로
  re-root 해서 단일 트리로 합친다(URDF 는 루트가 하나여야 한다).
- **조용한 실패를 안 만든다** — 모델을 못 찾거나 이름이 충돌하면 그 자리에서 원인과 조치를
  적어 실패한다. 절반만 조립된 URDF 를 내놓지 않는다.

## 슬롯 구성

```
base ── torso ─┬─ arm  ── endeffector  ── sensor1     1번 팔 + 손목 센서
               │                                       sensor2 = 전역/머리 센서
               └─ arm2 ── endeffector2 ── sensor3     2번 팔 + 손목 센서
```

| 슬롯 | 설명 |
|------|------|
| ① base | 모바일 베이스(루트) |
| ② torso | 상체 — 두 팔의 어깨 위치를 만든다 *(기본 꺼짐)* |
| ③ arm / ④ endeffector | 1번 팔·그리퍼 |
| ⑤ arm2 / ⑥ endeffector2 | 2번 팔·그리퍼 *(기본 꺼짐)* |
| ⑦ sensor1 | 1번 팔 손목 센서 |
| ⑧ sensor2 | 전역/머리 센서 (상체의 `torso_head_link` 에 붙이면 시야가 좋다) |
| ⑨ sensor3 | 2번 팔 손목 센서 *(기본 꺼짐)* |

- ②⑤⑥⑨는 체크해야 조립·저장에 들어간다 → 단팔로 저장해 둔 설정을 열어도 없던 파트가 생기지 않는다.
- ⑤⑥⑨는 ③④⑦과 **같은 모델 폴더**를 읽는다. 팔·센서 모델을 하나 넣으면 양쪽 드롭다운에 나온다.
- ⑤⑥의 링크에는 접두사가 **강제**된다(`arm2_link0`, `endeffector2_rg2_hand` …).
  같은 모델을 두 팔에 쓰면 `link0`·`tcp` 가 그대로 충돌하기 때문이다.

## 설치

### 1) 요구 환경

- Ubuntu 22.04 + **ROS 2 Humble**(`ros-humble-desktop`) — xacro·ament 를 쓴다
- Python 3.10

### 2) 워크스페이스에 clone

```bash
mkdir -p ~/ros2_ws/src && cd ~/ros2_ws/src
git clone https://github.com/<your-account>/dual-arm-assembler.git
```

### 3) 파이썬 의존

```bash
python3 -m pip install --user pyvista pyvistaqt trimesh yourdfpy pycollada python-fcl PyQt5
```

### 4) 모델 라이브러리 받기 (선택이지만 권장)

기본 제공 모델 외의 로봇(UR·xArm·Robotiq·Franka·Allegro·Husky·Jackal·TurtleBot4 …)은
각 원저작 저장소에서 받아 쓴다. 이 저장소에는 포함돼 있지 않다.

```bash
bash ~/ros2_ws/src/dual-arm-assembler/scripts/setup_vendor_models.sh
```

### 5) 빌드

```bash
source /opt/ros/humble/setup.bash
cd ~/ros2_ws && colcon build --symlink-install --packages-select dual_arm_assembler
source install/setup.bash
```

## 사용

### 조립 GUI

```bash
ros2 run dual_arm_assembler assembler
```

1. **② 상체** 체크 → 모델 선택 → 베이스 상판 위 위치 조정
2. **③ 로봇팔 1** 의 '붙일 파트'를 상체로, 부착 프레임을 `torso_shoulder_l_link` 로
3. **⑤ 로봇팔 2** 체크 → 부착 프레임 `torso_shoulder_r_link`, Roll −90°(바깥을 보게)
4. **④⑥ 엔드이펙터** 를 각 팔의 `tcp` 에 부착. 손목 카메라를 쓰면 **⑦⑨ 센서**를
   각 그리퍼의 `rg2_hand` 에, 전역 카메라(**⑧**)는 상체의 `torso_head_link` 에 붙인다
   ⚠ 부착 프레임은 **모델 로컬 이름**(`tcp`)으로 적는다. 접두사는 컴포저가 붙인다
   (`arm2_tcp` 라고 쓰면 두 번 붙는다).
5. `Ctrl+S` 저장 → `mounts.yaml`

왼쪽에서 슬롯을 고르고, 오른쪽에서 부착 프레임·XYZ·RPY·관절 초기 자세를 조정한다.
파트가 서로 파고들면 빨갛게 표시되고 상태줄에 충돌 쌍이 나온다. 설계상 원래 겹치는 결합은
'현재 겹침 무시'로 기준에 등록하면 이후에는 새로 생긴 겹침만 경고한다.

### 통합 URDF 만들기

```bash
ros2 run dual_arm_assembler compose_urdf --mounts mounts.yaml -o robot.urdf
check_urdf robot.urdf
```

### 모델 추가

`models/<슬롯>/` 에 파일을 넣으면 끝이다(슬롯 = `base`·`torso`·`arm`·`endeffector`·`sensor1`·`sensor2`).
2번 팔·그리퍼·센서 3 은 각각 `arm`·`endeffector`·`sensor1` 폴더를 공유하므로 따로 넣지 않는다.

```yaml
# models/arm/my_arm.yaml
label: 우리 팔 (6축)
pkg: my_arm_description        # ament 패키지  ┐ 둘 중 하나
xacro: urdf/my_arm.urdf.xacro  #               │
file: my_arm.urdf              # 같은 폴더 파일 ┘
args: {use_gripper: "false"}   # (선택) xacro 인자
anchor: base_link              # (선택) 부모에 붙는 프레임. 생략 시 URDF 루트
prefix: "arm_"                 # (선택) 생략 시 슬롯 접두사 자동. ""이면 접두사 없음
```

yaml 없이 `.urdf`/`.xacro` 만 넣어도 등록된다(라벨=파일명, anchor=루트).
GUI 의 **모델 새로고침** 버튼으로 재시작 없이 다시 스캔한다.

### 상체 모델

`models/torso/` 에 두 종류가 들어 있다.

| 모델 | 어깨 간격 | 어깨 높이 | 제공 프레임 |
|------|-----------|-----------|-------------|
| `column_torso` 기둥형 | 440 mm | 0.62 m | `torso_shoulder_l_link` · `torso_shoulder_r_link` · `torso_head_link` |
| `tbar_torso` T자형 | 600 mm | 0.33 m | `tbar_shoulder_l_link` · `tbar_shoulder_r_link` · `tbar_head_link` |

⚠ 형상 잡기용 **기본 치수**다(실측 아님). 실제 기구 도면이 있으면 URDF 의 숫자만 고치면 된다.
어깨 프레임은 빈 링크(`<link name="..."/>`)로 두면 부착점으로 바로 쓸 수 있다.

## 구조

```
dual_arm_assembler/
├── app.py            조립 GUI (PyQt5 + pyvista)
├── composer.py       통합 URDF 컴포저 (re-root · 접두사 · 마운트 조인트 · 충돌 검사)
├── collision.py      실시간 자충돌 검사 (trimesh + python-fcl)
├── urdf_loader.py    xacro → URDF → yourdfpy 로드
├── part_registry.py  슬롯·모델 레지스트리 (폴더 스캔)
├── paths.py          모델 폴더 경로 해석
├── mesh2urdf.py      STL/STEP → 단일 링크 URDF 변환기
└── configs/
    ├── dual.py       ← 양팔 구성 (기본)
    └── single.py     ← 단팔 구성
models/               모델 드롭 폴더(정본)
urdf/ · meshes/       동봉 모델 자산(RG2)
scripts/              벤더 모델 clone 스크립트
```

**코어는 슬롯 이름을 모른다.** 슬롯 목록·라벨·기본 결합값은 `configs/` 가 정의하고, 코어는
그 목록만 보고 동작한다. 그래서 다른 구성(팔 3개, 상체 없는 구성 등)을 추가할 때 코어를
건드릴 필요가 없다 — `configs/` 에 파일 하나를 더 만들면 된다.

## 알아두면 좋은 것

- **모델 폴더는 소스 트리가 정본**이다. 설치본(share)을 읽으면 폴더에 모델을 넣어도
  `colcon build` 전까지 반영되지 않아 GUI 와 컴포저가 어긋난다. 다른 위치를 쓰려면
  `RDA_MODELS_DIR` 로 지정한다.
- **저장 위치**는 `RDA_MOUNTS_FILE` 로 바꿀 수 있다(기본: 저장소 루트의 `mounts.yaml`).
- **URDF 루트는 하나**여야 한다. 표준 모델이 만드는 `world` 루트는 anchor 기준으로 잘라낸다.
  잘라낼 조인트가 가동관절이거나 다른 서브트리를 잃게 되면 즉시 실패한다(조용히 형상이
  바뀌는 것보다 낫다).

## 현재 범위와 한계

- **조립 + 통합 URDF(형상·TF)** 까지가 이 도구의 범위다.
- **MoveIt 설정(SRDF/ACM)은 생성하지 않는다.** 양팔 계획 그룹(`arm_left`/`arm_right`)과
  양팔 간 ACM 생성은 별도 작업이 필요하다.
- 상체 모델 치수는 예시값이다(실측 아님).

## 라이선스

Apache-2.0 (LICENSE 참조). 동봉된 외부 산출물과 clone 해 오는 벤더 모델의 출처·라이선스는
[NOTICE](NOTICE) 에 정리했다.
