# 아르카디의 침묵 (Arcadi's Silence)

김재준 작 단막극 「아르카디의 침묵」을 AI 기술로 영상화하는 프로젝트입니다.
대본 파싱, AI 음성 합성(TTS), 이미지 생성, 영상 합성을 자동화 파이프라인으로
구성하여 단막극을 시각적 작품으로 재해석합니다.

## 프로젝트 개요

- **원작**: 「아르카디의 침묵」 (김재준)
- **목표**: 단막극 대본을 AI 기반 영상 콘텐츠로 제작
- **방식**: 대본 파싱 → TTS 음성 생성 → 장면 이미지 생성 → 영상 합성

## 폴더 구조

```
arcadis-silence/
├── script/      대본 원본(PDF) 및 파싱된 구조화 데이터(JSON)
├── voices/      OpenAI TTS로 생성한 등장인물별 음성 파일
├── images/      DALL-E 3로 생성한 장면 이미지
├── remotion/    Remotion 기반 영상 합성 프로젝트 (예정)
├── tests/       파이프라인 검증용 프로토타입 클립
├── config/      등장인물별 음성 매핑 등 설정 파일
└── scripts/     파싱·생성·합성 등 파이프라인 스크립트
```

## 기술 스택

- **TTS**: OpenAI `tts-1-hd` (등장인물별 음색·속도·이펙트 매핑)
- **이미지 생성**: OpenAI DALL-E 3
- **오디오/영상 처리**: ffmpeg
- **영상 합성**: Remotion (예정)
- **런타임**: Node.js

## 사용법

### 1. 환경 변수 설정

레포 루트의 `.env.example`을 복사해 `.env`를 만들고 OpenAI API 키를 입력합니다.

```bash
cp .env.example .env
# .env 파일을 열어 OPENAI_API_KEY 값을 채운다
```

`.env` 자체는 `.gitignore`에 등록되어 있어 커밋되지 않습니다.

### 2. 의존성 설치

```bash
npm install
```

ARKADI 라인은 `aecho` 기반 deep reverb 후처리를 거치므로 **ffmpeg이 PATH에
등록되어 있어야 합니다.** Windows는 https://www.gyan.dev/ffmpeg/builds/ 의
essentials 빌드를 받아 `bin` 폴더를 PATH에 추가하면 됩니다.
설치 확인: `ffmpeg -version`

### 3. 음성 생성 (`scripts/generate_voices.js`)

`script/parsed.json`의 모든 `dialogue` 라인을 OpenAI `tts-1-hd`로 합성합니다.
파이프라인은 두 단계로 동작합니다.

1. **TTS 원본**을 `voices/raw/{scene_id}_{line_id}_{speaker}.mp3`에 저장
2. `config/voices.json`에서 `post_fx`가 지정된 경우 ffmpeg으로 후처리하여
   **최종본**을 `voices/{scene_id}_{line_id}_{speaker}.mp3`로 저장
   (지정되지 않은 경우 원본을 그대로 복사)

최종본이 이미 존재하면 전체 단계를 건너뜁니다. 리버브 톤만 다시 튜닝하고
싶다면 최종본만 삭제하고 재실행하세요 — 원본이 보존되어 있어 OpenAI
호출 없이 ffmpeg만 다시 돕니다.

```bash
# 전체 dialogue 합성
node scripts/generate_voices.js
# 또는
npm run voices

# 처음 5개 라인만 (스모크 테스트용)
node scripts/generate_voices.js --limit 5

# 특정 장면만
node scripts/generate_voices.js --scene 1

# 특정 인물만
node scripts/generate_voices.js --speaker ARKADI

# 옵션 조합도 가능 (scene 2의 K 라인만 처음 3개)
node scripts/generate_voices.js --scene 2 --speaker K --limit 3
```

#### 옵션 요약

| 옵션 | 설명 |
| --- | --- |
| (없음) | parsed.json의 모든 dialogue 라인을 처리 |
| `--limit N` | 처음 N개 라인까지만 처리 |
| `--scene N` | `scene_id`가 N인 장면의 라인만 처리 |
| `--speaker S` | `speaker`가 S인 라인만 처리 (예: `K`, `M`, `ARKADI`) |

음색·속도·후처리 매핑은 `config/voices.json`에서 관리합니다.

### 4. 단일 파일 후처리 (`scripts/post_fx.js`)

리버브 파라미터를 빠르게 실험하고 싶을 때 단일 파일에 직접 적용할 수 있습니다.

```bash
node scripts/post_fx.js voices/raw/3_3.5_ARKADI.mp3 voices/3_3.5_ARKADI.mp3
```

필터 식은 `scripts/post_fx.js`의 `DEEP_REVERB_FILTER` 상수에 정의되어 있습니다
(`aecho` 다중 탭 + `lowpass` + 볼륨 보정).

### 5. 장면 이미지 생성 (`scripts/generate_images.js`)

`script/parsed.json`의 각 scene에 대해 DALL-E 3로 1장씩 합성한 결과를
`images/scene_{N}.png`에 저장합니다. 같은 폴더에 `scene_{N}.prompt.txt`로
실제 전송된 프롬프트와 DALL-E의 `revised_prompt`도 함께 기록되어, 결과가
마음에 안 들 때 어디를 손볼지 추적하기 쉽습니다.

```bash
# 전체 scene 생성 (기본: 1792x1024, hd, 흑백+선택적 컬러)
node scripts/generate_images.js
# 또는
npm run images

# 비용 없이 프롬프트만 미리 확인
node scripts/generate_images.js --dry-run

# 특정 scene만
node scripts/generate_images.js --scene 1

# 처음 2개만 (스타일 검증용)
node scripts/generate_images.js --limit 2

# 비용 절감 (절반 가격)
node scripts/generate_images.js --quality standard
```

#### 옵션 요약

| 옵션 | 설명 |
| --- | --- |
| (없음) | 모든 scene을 처리, 이미 PNG가 있으면 스킵 |
| `--scene N` | `scene_id`가 N인 장면만 처리 |
| `--limit N` | 처음 N개 scene만 처리 |
| `--quality hd\|standard` | DALL-E 3 품질 (기본: config의 `hd`) |
| `--dry-run` | API 미호출, 프롬프트만 stdout 출력 |

스타일·해상도·품질 기본값은 `config/image_style.json`에서 관리합니다.
톤이 마음에 안 들면 `style_prefix`를 수정하고, 해당 PNG만 삭제 후 다시
실행하면 됩니다.

### 6. 타이밍 계산 (`scripts/compute_timing.js`)

`voices/*.mp3`의 길이를 ffprobe로 측정해 Remotion 합성에 쓸
`script/timing.json`을 생성합니다. 라인 사이 0.3초, 장면 사이 1.0초의
호흡 갭이 들어갑니다.

```bash
npm run timing
# 또는
node scripts/compute_timing.js
```

음성을 새로 만들거나 지웠을 때 다시 실행하세요.

### 7. 영상 합성 (Remotion)

```bash
cd remotion
npm install      # 최초 1회
npm run render   # → remotion/out/prototype.mp4 생성
```

`npm run dev`로 Remotion Studio 브라우저 미리보기도 가능합니다
(timeline에서 라인별 타이밍을 시각적으로 확인하고 자막/이미지 위치 튜닝).

#### 전체 파이프라인 순서 요약

1. `npm run voices` — TTS 합성
2. `npm run images` — 장면 이미지 생성
3. `npm run timing` — 타이밍 JSON 갱신
4. `cd remotion && npm run render` — mp4 출력

## 진행 상황 메모

- [x] 레포 초기 구조 셋업
- [x] TTS 음성 생성 파이프라인
- [x] 후처리 이펙트(`scripts/post_fx.js`) ffmpeg `aecho` 다단 체인 구현
- [x] 장면별 이미지 생성 파이프라인 (DALL-E 3, 1792×1024, 흑백+선택적 컬러)
- [x] 타이밍 계산 스크립트 (ffprobe 기반, dialogue + stage_direction)
- [x] Remotion 합성 프로젝트 (Phase 1: 정적 컷 + 자막)
- [x] Phase 2: Ken Burns 줌·드리프트, stage_direction 이탤릭 오버레이, 장면 페이드 인/아웃, ARKADI 리버브 명료도 튜닝
- [ ] 프로토타입 클립 렌더링 및 검수
