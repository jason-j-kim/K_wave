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

### 3. 음성 생성 (`scripts/generate_voices.js`)

`script/parsed.json`의 모든 `dialogue` 라인을 OpenAI `tts-1-hd`로 합성하여
`voices/{scene_id}_{line_id}_{speaker}.mp3` 형식으로 저장합니다.
이미 존재하는 파일은 자동으로 건너뜁니다(재실행 시 비용 절약).

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

## 진행 상황 메모

- [x] 레포 초기 구조 셋업
- [x] TTS 음성 생성 파이프라인 (스크립트 작성, 실행 대기)
- [ ] 후처리 이펙트(`scripts/post_fx.js`) ffmpeg 명령 구현
- [ ] 장면별 이미지 생성 파이프라인
- [ ] Remotion 합성 프로젝트 초기화
- [ ] 프로토타입 클립 제작
