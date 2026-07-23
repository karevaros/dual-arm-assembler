# mesh2urdf — 3D 파일을 조립 가능한 모델로 만들기

브래킷·플레이트·센서 케이스처럼 **관절이 없는 강체 파트**를 STL/STEP 등에서 URDF 로 바꿔
모델 폴더에 바로 등록한다. 변환 후 조립기에서 **`🔄 모델 새로고침`**(F5) 하면 드롭다운에 뜬다.

```bash
ros2 run dual_arm_assembler mesh2urdf bracket.stl --slot sensor1
```

---

## 되는 것과 안 되는 것

**핵심: 3D 파일에는 형상만 있고 관절 정보가 없다.** 그래서 경로가 갈린다.

| 입력 | 방법 | 관절 |
|------|------|------|
| STL · OBJ · DAE · GLB/GLTF · PLY · 3MF · OFF | `mesh2urdf` — 바로 됨 | ❌ 강체만 |
| STEP · IGES | `sudo apt install freecad` 후 `mesh2urdf`(자동 테셀레이션) | ❌ 강체만 |
| SolidWorks | [sw_urdf_exporter](https://github.com/ros/solidworks_urdf_exporter) | ✅ 보존 |
| Fusion 360 | [fusion2urdf](https://github.com/syuntoku14/fusion2urdf) | ✅ 보존 |
| Onshape | [onshape-to-robot](https://github.com/Rhoban/onshape-to-robot) | ✅ 보존 |

관절이 있는 파트를 STL 로 뽑으면 관절이 사라진다. 전용 익스포터를 쓰거나, 부품별로 각각
변환한 뒤 xacro 로 joint 를 직접 엮어야 한다.

## 옵션

| 옵션 | 기본 | 설명 |
|------|------|------|
| `mesh` | (필수) | 입력 3D 파일 |
| `--slot` | (필수) | `base` · `torso` · `arm` · `endeffector` · `sensor1` · `sensor2` |
| `--name` | 파일명 | 모델 id (파일 이름이 된다) |
| `--label` | name | 드롭다운 표시 이름 |
| `--scale` | 자동 | 단위 배율. mm 도면이면 `0.001` |
| `--density` | 2700 | 관성 계산용 밀도 kg/m³ (알루미늄 2700 · 강철 7850 · 플라스틱 1200) |
| `--origin` | `keep` | 링크 원점: `keep`(원본) · `center` · `bottom`(바닥을 z=0) · `com`(무게중심) |
| `--collision` | `hull` | 충돌 메시: `hull` · `simplify` · `same` |
| `--max-faces` | 2000 | `--collision simplify` 목표 면수 |
| `--out-dir` | 저장소 `models/` | 모델 폴더 루트(또는 `RDA_MODELS_DIR`) |

> `arm2` · `endeffector2` · `sensor3` 는 슬롯 목록에 없다. 각각 `arm` · `endeffector` ·
> `sensor1` 폴더를 **공유**하므로, 그 슬롯으로 넣으면 2번 팔 쪽 드롭다운에도 함께 나온다.

## 예시

```bash
# 1) 센서 브래킷 — 기본값으로 충분한 경우
ros2 run dual_arm_assembler mesh2urdf bracket.stl --slot sensor1

# 2) STEP 파일 + 강철 + 바닥 기준 원점 + 이름 지정
ros2 run dual_arm_assembler mesh2urdf tool.step --slot endeffector \
    --name tool_x --label "커스텀 툴 X" --density 7850 --origin bottom

# 3) 오목한 파트라 충돌 메시를 원본 그대로 써야 하는 경우
ros2 run dual_arm_assembler mesh2urdf frame.stl --slot torso --collision same

# 4) mm 도면인데 자동 추정이 빗나갈 때
ros2 run dual_arm_assembler mesh2urdf plate.obj --slot base --scale 0.001
```

## 자동으로 처리하는 것 (그리고 그 한계)

### 단위

CAD 는 보통 mm, URDF 는 m 다. 최대 치수가 **10 m 를 넘으면 mm 로 그린 것**으로 보고
0.001 배 한다(로봇 파트가 10 m 를 넘을 일은 없고, mm 로 그린 1 m 파트는 1000 이 된다).
경계에 걸리는 파트는 `--scale` 로 못 박는 편이 안전하다.

### 관성(inertia)

`--density` 로 trimesh 질량특성을 계산해 `<inertial>` 을 채운다.
메시가 **닫혀 있지 않으면**(watertight=False) 부피를 정의할 수 없어 **볼록껍질로 근사하고
경고**한다. 그 값은 참고치이므로, 동역학이 중요한 파트라면 나중에 손으로 고칠 것.

### 충돌 메시 — 여기서 가장 많이 실수한다

원본 메시를 그대로 충돌에 쓰면 면수가 많아 자충돌 검사가 느려진다. 그래서 기본이
볼록껍질(`hull`)인데, **오목한 파트에서는 부풀어 오른다.**

실측(L자 + 구멍이 있는 브래킷):

| 모드 | 면수 | 부피(원본 대비) | 쓸 때 |
|------|------|------------------|-------|
| `hull` (기본) | 16 | **260 %** | 볼록한 파트, 속도 우선 |
| `simplify` | 1030 | 87 % | 오목 + 면수를 줄이고 싶을 때 |
| `same` | 1036 | 100 % | **오목한 파트 — 가장 정확** |

`hull` 부피가 원본의 1.5 배를 넘으면 변환기가 경고한다. 그 경고가 뜨면 실제로는 닿지
않는데 충돌로 잡히는 상황이 생기므로 `--collision same` 을 쓰는 편이 낫다.

`simplify` 는 `pip install --user fast_simplification` 이 필요하다. 다만 **CAD 테셀레이션은
감쇠가 잘 안 된다** — 위 예에서도 목표 300면을 줬는데 1030면에서 멈췄다(라이브러리 한계).
목표에 못 미치면 경고를 띄우며, 그 경우 `same` 과 실익 차이가 거의 없다.

### 원점

| 값 | 의미 |
|----|------|
| `keep`(기본) | 원본 좌표 유지 — CAD 에서 원점을 이미 맞춰 뒀을 때 |
| `bottom` | 바닥을 z=0 으로 — 무언가 위에 얹는 파트(베이스·상체)에 편하다 |
| `center` | 바운딩박스 중심 |
| `com` | 무게중심 |

조립기에서 결합 위치를 잡을 때 이 원점이 기준이 된다. `bottom` 으로 뽑아 두면 "상판 위
z=0" 같은 값을 그대로 쓸 수 있어 편하다.

## 생성물

```
models/<슬롯>/<name>.urdf                    링크 1개 URDF (visual · collision · inertial)
models/<슬롯>/<name>.yaml                    조립기 등록용 디스크립터(label · file · anchor)
models/<슬롯>/meshes/<name>_visual.stl       표시용 메시(단위 변환·원점 적용됨)
models/<슬롯>/meshes/<name>_collision.stl    충돌용 메시(--collision 결과)
```

바로 확인:

```bash
check_urdf ~/dual-arm-assembler/models/sensor1/bracket.urdf
```

조립기가 켜져 있으면 **`🔄 모델 새로고침`**, 꺼져 있으면 그냥 실행하면 드롭다운에 있다.

## 문제가 생기면

| 증상 | 원인·해결 |
|------|-----------|
| `STEP/IGES 를 읽으려면 FreeCAD 가 필요합니다` | `sudo apt install freecad` |
| 파트가 **1000배 크게/작게** 뜸 | 단위 추정 실패 → `--scale 0.001`(mm 도면) 또는 `--scale 1` |
| `watertight 가 아닙니다` 경고 | 메시에 구멍이 있다 → 관성은 볼록껍질 근사값. CAD 에서 솔리드로 다시 내보내면 정확해진다 |
| 닿지 않는데 충돌로 잡힘 | 볼록껍질이 부푼 것 → `--collision same` |
| 드롭다운에 안 뜸 | `🔄 모델 새로고침` 을 눌렀는지 확인. 그래도 없으면 `models/<슬롯>/` 에 파일이 실제로 생겼는지 확인 |
