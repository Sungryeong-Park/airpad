# airpad — 설계 문서

**날짜:** 2026-06-12  
**저장소:** airpad  
**요약:** MacBook 웹캠으로 손 제스처를 인식해 트랙패드 및 마우스를 대체하는 macOS 데스크탑 앱

---

## 1. 목표

- 웹캠 기반 손 제스처로 macOS 트랙패드 제스처를 완전히 대체
- Rectangle 창 분할(2/4/6분할) 제어
- 마우스 포인터 모드 지원
- 시스템 리소스에 최소한의 영향

---

## 2. 아키텍처

### 프로세스 구조

```
[Main Process] (항상 실행, ~20MB)
  rumps 메뉴바 앱 + pynput 단축키 감지
  │
  │ 토글 신호 (multiprocessing.Queue)
  ▼
[Vision Subprocess] (nice +10, 낮은 우선순위)
  대기 루프 ──토글 ON──▶ PyAV 카메라 열기
                          MediaPipe Hands Lite
                          Gesture Classifier
                          Action Executor
                          Overlay
           ◀──토글 OFF── 카메라 닫기 → 대기 복귀
```

- Vision subprocess는 앱 시작 시 한 번 spawn, 평소엔 대기 (CPU ~0%)
- MediaPipe는 메모리에 유지 (토글마다 재초기화 없음)
- 단축키는 홀딩이 아닌 토글 방식 (1회 ON, 1회 OFF)
- 메뉴바 아이콘: 활성/비활성 상태 표시

---

## 3. 기술 스택

| 역할 | 라이브러리 |
|------|-----------|
| 카메라 캡처 | PyAV |
| 손 랜드마크 | MediaPipe Hands (Lite 모델) |
| 트랙패드 이벤트 시뮬레이션 | Quartz (PyObjC) CGEventPost |
| Rectangle 단축키 주입 | pynput |
| 단축키 감지 | pynput |
| 오버레이 UI | tkinter |
| 메뉴바 앱 | rumps |

---

## 4. 모드

### 모드 전환

메뉴바 아이콘 클릭 → 드롭다운에서 선택:
- **스와이프 모드** (기본)
- **포인터 모드**

Rectangle 제스처(주먹, 3손가락)는 스와이프 모드 내에서 항상 사용 가능 — 별도 모드 전환 불필요.

---


### 4-1. 스와이프 모드 (macOS 트랙패드 동일)

| 제스처 | 동작 |
|--------|------|
| 2 fingers 스크롤 (상/하/좌/우) | 수직/수평 스크롤 |
| 2 fingers 핀치 open/close | 확대/축소 |
| 3 fingers swipe up | Mission Control |
| 3 fingers swipe down | App Exposé |
| 3 fingers swipe left/right | 전체화면 앱 전환 |
| 4 fingers swipe up | Mission Control |
| 4 fingers swipe down | 데스크탑 전체 보기 |
| 4 fingers swipe left/right | 데스크탑 전환 |

### 4-2. Rectangle 모드

**2분할 — 주먹(0 fingers) + 스와이프**

| 제스처 | 동작 | 단축키 |
|--------|------|--------|
| 주먹 + ← | 왼쪽 절반 | `^⌥←` |
| 주먹 + → | 오른쪽 절반 | `^⌥→` |

**4분할 — 주먹 + 대각선 스와이프**

| 제스처 | 동작 | 단축키 |
|--------|------|--------|
| 주먹 + ↖ | 왼쪽 위 | `^⌥U` |
| 주먹 + ↗ | 오른쪽 위 | `^⌥I` |
| 주먹 + ↙ | 왼쪽 아래 | `^⌥J` |
| 주먹 + ↘ | 오른쪽 아래 | `^⌥K` |

**6분할 — 3손가락(중지+약지+소지) + 스와이프**

| 제스처 | 동작 | 단축키 |
|--------|------|--------|
| 3fingers + ← | 처음 1/3 | `^⌥D` |
| 3fingers + → | 마지막 1/3 | `^⌥G` |
| 3fingers + ↑↓ 흔들기 | 가운데 1/3 (전체 높이) | `^⌥F` |
| 3fingers + ↑ | 위 가운데 1/6 | `^⌥;` |
| 3fingers + ↓ | 아래 가운데 1/6 | `^⌥.` |
| 3fingers + ↖ | 위 왼쪽 1/6 | `^⌥L` |
| 3fingers + ↗ | 위 오른쪽 1/6 | `^⌥'` |
| 3fingers + ↙ | 아래 왼쪽 1/6 | `^⌥,` |
| 3fingers + ↘ | 아래 오른쪽 1/6 | `^⌥/` |

### 4-3. 포인터 모드 (마우스 제어)

| 제스처 | 동작 |
|--------|------|
| 검지만 펴고 이동 | 마우스 포인터 이동 |
| 검지 빠르게 구부렸다 펴기 | 좌클릭 |
| 검지+중지 빠르게 구부렸다 펴기 | 우클릭 |
| 검지 구부린 채로 이동 | 드래그 |

---

## 5. 제스처 인식 파이프라인

```
PyAV 프레임 (320×240, 15fps)
    ↓
MediaPipe Hands Lite → 21개 랜드마크 좌표
    ↓
gesture/classifier.py
  - 손가락 상태 (펴짐/접힘) 분류
  - 손 이동 벡터 계산 (손목 기준 프레임 간 delta)
  - 제스처 매칭 (룰 기반)
    ↓
gesture/debouncer.py
  - 동일 제스처 연속 실행 방지 (500ms 쿨다운)
    ↓
action/executor.py
  - 현재 모드(스와이프/Rectangle/포인터)에 따라 분기
    ↓
trackpad.py / keyboard.py / pointer.py
    ↓
overlay/manager.py (피드백 레벨에 따라 표시)
```

---

## 6. 시각적 피드백 (온오프 가능)

| 레벨 | 내용 |
|------|------|
| 0 — 없음 | 피드백 없음 |
| 1 — 미니멀 | 화면 구석에 현재 인식 제스처 이름 표시 |
| 2 — 풀 | 카메라 피드 + 21개 랜드마크 + 제스처 이름 오버레이 |

---

## 7. 프로젝트 구조

```
airpad/
├── main.py                  # 진입점, rumps 메뉴바 앱
├── hotkey.py                # pynput 토글 감지
├── vision_worker.py         # subprocess: 카메라 + 제스처 인식 루프
├── gesture/
│   ├── classifier.py        # 손가락 상태 + 방향 분류
│   └── debouncer.py         # 연속 실행 방지
├── action/
│   ├── executor.py          # 모드별 분기
│   ├── trackpad.py          # CGEvent 트랙패드 이벤트
│   ├── keyboard.py          # Rectangle 단축키 주입
│   └── pointer.py           # 마우스 포인터/클릭/드래그
├── overlay/
│   ├── manager.py           # 피드백 레벨 관리
│   └── window.py            # tkinter 투명 오버레이
├── config.py                # 전체 설정값
├── .env                     # 환경변수 오버라이드
└── requirements.txt
```

---

## 8. 설정 (`config.py`)

```python
CAMERA_RESOLUTION = (320, 240)
CAMERA_FPS = 15
MEDIAPIPE_MODEL = "lite"       # lite / full
GESTURE_DEBOUNCE_MS = 500
HOTKEY = "<ctrl>+<space>"
OVERLAY_LEVEL = 0              # 0 / 1 / 2
PROCESS_NICE = 10
```

---

## 9. 에러 처리

| 상황 | 처리 |
|------|------|
| 카메라 접근 권한 없음 | 메뉴바 알림 후 비활성 유지 |
| 카메라 점유 중 | 토글 시 재시도 1회, 실패 시 알림 |
| MediaPipe 초기화 실패 | subprocess 재시작 1회 자동 시도 |
| 손 미감지 | 무동작 |
| vision subprocess 크래시 | main process 감지 후 자동 재spawn |

---

## 10. MVP 범위

- [ ] 스와이프 모드 (트랙패드 8개 제스처)
- [ ] Rectangle 2/4/6분할
- [ ] 포인터 모드 (이동/좌클릭/우클릭/드래그)
- [ ] 토글 단축키
- [ ] 시각적 피드백 3레벨
- [ ] 메뉴바 앱 (상태 표시 + 모드 전환)
- [ ] subprocess 격리 + nice +10
