# 모델 드롭 폴더 — 코드 편집 없이 조립기에 모델 추가

이 폴더의 **슬롯 하위 폴더**(`base/ torso/ arm/ endeffector/ sensor1/ sensor2/`)에 파일을
넣으면 조립기가 자동으로 인식해 그 슬롯의 드롭다운에 추가한다. Python 코드 편집 불필요.
앱 실행 중이면 **`🔄 모델 새로고침`**(`F5`)으로 재시작 없이 다시 스캔한다.

> 2번 팔·그리퍼·센서 3(`arm2`·`endeffector2`·`sensor3`)은 각각 `arm/`·`endeffector/`·
> `sensor1/` 폴더를 **공유**한다. 같은 모델을 두 번 넣을 필요가 없다.

## 함께 쓸 수 있는 모델 라이브러리

아래 모델들은 이 저장소에 **포함돼 있지 않다**. `bash scripts/setup_vendor_models.sh` 가
각 원저작 저장소에서 `vendor/` 로 clone 하며, 각자의 라이선스를 따른다(→ NOTICE).

| 슬롯 | 모델 | 라이선스 |
|------|------|----------|
| **base** | AgileX Scout 2.0 · box_base(동봉, 테스트용) | Apache-2.0 |
| | Robotnik RB-Theron · RB-Summit · RB-Kairos · RB-Vogui | BSD-3 |
| | Clearpath Ridgeback · Jackal · Husky · Dingo-D/O | BSD-3 |
| | TurtleBot4 | Apache-2.0 |
| **torso** | column_torso · tbar_torso (동봉) | Apache-2.0 |
| **arm** | Rainbow RB5-850e · RB10-1300e | Apache-2.0 |
| | UR5e · UR10e · UF850 · xArm6 | BSD-3 |
| **endeffector** | OnRobot RG2(동봉) · RG6 | BSD / MIT |
| | Robotiq 2F-85 · 2F-140 | BSD-3 |
| | Franka Hand · Allegro Hand V5 | Apache-2.0 / BSD-2 |
| **sensor** | RealSense D405 · D435i | Apache-2.0 |

**등록하지 않은 모델과 사유**는 `scripts/setup_vendor_models.sh` 하단 주석에 있다
(catkin 전용 · mesh 라이선스 부재 · 상류 트리 버그 등).

> ⚠ **적재 하중을 확인할 것.** 팔+그리퍼+센서 조합은 쉽게 20kg 를 넘는다. Dingo(20kg)·
> TurtleBot4(9kg) 같은 소형 베이스는 구성 실험용으로만 쓰는 편이 안전하다.

---

이 폴더의 **슬롯 하위 폴더**(`base/ arm/ endeffector/ sensor1/ sensor2/`)에
> **바로가기:** 조립기 왼쪽 **`📂 모델 폴더 열기`**(`Ctrl+M`, 도구 메뉴에도 있음)를 누르면
> 이 폴더가 파일 관리자로 열립니다. **폴더 열기 → 파일 드롭 → `F5`** 순서로 쓰면 됩니다.

## 외부 3D 파일(CAD)에서 모델 만들기

> **핵심:** 3D 파일에는 **형상만** 있고 **관절 정보가 없다.** 그래서 경로가 갈린다.

| 입력 | 방법 | 관절 |
|------|------|------|
| **STL·OBJ·DAE·GLB·PLY·3MF** | `mesh2urdf` (아래) — 바로 됨 | ❌ 강체만 |
| **STEP·IGES** | `sudo apt install freecad` 후 `mesh2urdf` (자동 테셀레이션) | ❌ 강체만 |
| **SolidWorks** | [sw_urdf_exporter](https://github.com/ros/solidworks_urdf_exporter) (Windows/SolidWorks 내부) | ✅ 보존 |
| **Fusion360** | [fusion2urdf](https://github.com/syuntoku14/fusion2urdf) 스크립트 | ✅ 보존 |
| **Onshape** | [onshape-to-robot](https://github.com/Rhoban/onshape-to-robot) | ✅ 보존 |

**관절이 있는 파트**는 STL/STEP 으로 뽑으면 관절이 사라진다 → 위 전용 익스포터를 쓰거나,
부품별로 각각 `mesh2urdf` 한 뒤 xacro 로 joint 를 직접 엮어야 한다.

### `mesh2urdf` — 강체 파트 자동 변환
메시를 링크 1개 URDF 로 만들고 **관성(inertia)까지 계산**해 이 폴더에 바로 등록한다.
```bash
# 기본 (단위·관성·충돌메시 자동)
ros2 run dual_arm_assembler mesh2urdf bracket.stl --slot sensor1

# 이름·라벨·재질·원점 지정
ros2 run dual_arm_assembler mesh2urdf part.step --slot endeffector \
    --name tool_x --label "커스텀 툴 X" --density 7850 --origin bottom
```
자동 처리:
- **단위**: CAD 는 보통 mm → 최대 치수가 10m 를 넘으면 mm 로 보고 ×0.001. `--scale 0.001` 로 강제 가능.
- **관성**: `--density`(기본 2700 알루미늄 / 강철 7850 / 플라스틱 1200)로 계산.
  메시가 닫혀있지 않으면(watertight=False) 볼록껍질로 근사하고 **경고**를 띄운다.
- **충돌 메시**: 기본 볼록껍질(`--collision hull`) — 빠르지만 **오목한 파트는 부풀어 오른다.**
  실측(L자+구멍 브래킷): `hull` 부피가 원본의 **260%** → 실제로 안 닿는데 충돌로 잡힌다.
  1.5배를 넘으면 변환기가 **경고**하니, 그때는 `--collision same` 을 쓸 것.

  | 모드 | 면수 | 부피(원본 대비) | 쓸 때 |
  |------|------|------------------|-------|
  | `hull`(기본) | 16 | 260% | 볼록한 파트, 속도 우선 |
  | `simplify` | 1030 | 87% | 오목 + 면수 줄이고 싶을 때 |
  | `same` | 1036 | 100% | **오목한 파트 — 가장 정확** |

  `simplify` 는 `pip install --user fast_simplification` 필요. 단 **CAD 테셀레이션은 감쇠가
  잘 안 된다**(위 예: 목표 300면인데 1030면에서 멈춤 — 라이브러리 한계). 목표에 못 미치면
  경고를 띄우며, 그 경우 `same` 과 실익 차이가 거의 없다.
- **원점**: `--origin keep`(기본, 원본 유지) / `center` / `bottom`(바닥을 z=0 — 위에 얹는 파트에 편함) / `com`.

생성물: `<슬롯>/<name>.urdf` + `<name>.yaml` + `<슬롯>/meshes/<name>_{visual,collision}.stl`
→ 조립기에서 **`🔄 모델 새로고침`** 하면 드롭다운에 뜬다.

## 두 가지 넣는 방법

### 1) 무설정 드롭 — URDF/xacro 파일만
`arm/` 에 `my_arm.urdf` 또는 `my_arm.xacro` 를 그냥 넣습니다.
- 라벨 = 파일명, `anchor` = 루트 링크(자동).
- mesh 는 `package://<빌드된 패키지>/...` 참조를 권장(colcon build 되어 있어야 함).
  URDF 옆에 상대경로로 둔 mesh 도 인식합니다(`meshes/foo.stl` 등).

### 2) yaml 디스크립터 — 세밀 설정
`anchor`(부착 프레임)나 `args`, 예쁜 라벨이 필요하면 `.yaml` 을 넣습니다.

```yaml
# endeffector/my_gripper.yaml
label: "제조사 그리퍼 X"     # 생략 시 파일명
# ── 소스: 둘 중 하나 ──
file: my_gripper.urdf        # 같은 폴더 파일(또는 절대경로)
# 또는 ↓ 빌드된 패키지 참조
# pkg: mygripper_description
# xacro: urdf/my_gripper.urdf.xacro
args: {}                     # (선택) xacro 인자, 예: {use_nominal_extrinsics: "true"}
anchor: gripper_base         # (선택) 부모에 붙는 프레임, 생략 시 루트 링크
```
같은 이름의 `.urdf`/`.xacro` 가 함께 있으면 yaml 설정이 우선합니다.

## anchor 정하는 법
`anchor` = 이 파트가 **부모에 맞닿는 링크**(mount joint 의 child).
- 베이스/팔: 보통 루트 링크가 접점 → **생략(=None)**.
- 그리퍼: 자체 `world` 루트를 갖는 모델이 많음 → **손바닥 링크명**을 지정.
- 애매하면 `check_urdf my_model.urdf` 로 트리를 보고 부모에 닿는 링크를 고릅니다.

## 폴더 위치 바꾸기
환경변수로 다른 폴더를 쓸 수 있습니다:
```bash
export RDA_MODELS_DIR=~/my_models   # 하위에 base/ arm/ ... 를 두면 됨
```

## 통합(최종) 로봇에 반영
조립기에서 고른 모델·결합값은 `mounts.yaml` 로 저장되고, **모든 슬롯이 그대로 통합
URDF 에 반영**됩니다. 컴포저가 조립기와 같은 모델 정의를 읽으므로 앱 화면과 RViz 형상이
일치합니다.

```bash
ros2 run dual_arm_assembler compose_urdf --mounts mounts.yaml -o /tmp/robot.urdf
check_urdf /tmp/robot.urdf
```

**링크 이름 규칙:** 모델 링크에는 기본으로 슬롯 접두사가 붙습니다(`arm_`, `sensor1_` …).
서로 다른 모델이 흔히 같은 이름(`base_link`)을 써서 충돌하기 때문입니다. 하위 도구가
특정 링크 이름에 의존하는 경우(SRDF·기구학 스크립트 등) 모델 yaml 에 `prefix: ""` 를 주면
원래 이름이 보존됩니다 — 동봉된 Scout/RB5/RG2 가 그렇게 설정돼 있습니다.
단 **2번 팔·그리퍼에는 접두사가 강제**됩니다(같은 모델을 두 팔에 쓰면 충돌하므로).



---

## 양팔 구성 (torso · arm2 · endeffector2)

이 저장소의 기본 구성이 양팔이다. 단팔 구성은 `--single` 로 전환한다.

```bash
ros2 run dual_arm_assembler assembler             # 양팔(상체 + 팔·그리퍼 2조 + 센서 3)
ros2 run dual_arm_assembler assembler --single    # 단팔
```

- 상체 모델은 `torso/` 에 있다(`column_torso` 기둥형 440mm · `tbar_torso` T자형 600mm).
- 2번 팔/그리퍼/센서 3 은 **`arm/`·`endeffector/`·`sensor1/` 폴더를 그대로 공유**한다 —
  모델을 새로 넣으면 양쪽 드롭다운에 함께 나온다. `arm2/` 같은 폴더는 만들 필요 없다.
- 자세한 절차·주의사항 → 저장소 최상위 [`README.md`](../README.md)
