# ad_evaluation

Pitt Ads Dataset을 사용한 광고 창의성·실용성 평가 AI 백엔드 파이프라인.

## 개요

피츠버그 대학교 Adriana Kovashka 교수 연구실의 **Pitt Ads Dataset** (약 64,000개 이미지 광고, 약 3,000개 비디오 광고)을 수령하여, 멀티모달 임베딩(CLIP) 및 로컬 벡터 DB(FAISS) 기반의 유사도 검색 파이프라인을 구축한다.

- 원본: <http://pitt.edu/~akovashka/ads/>

## 폴더 구조

```
ad_evaluation/
├── download_pitt_ads.sh          # Linux/macOS/WSL 다운로드 스크립트
├── download_pitt_ads.ps1         # Windows PowerShell 다운로드 스크립트
├── pitt_ads_parser.py            # 메타데이터 파싱 & 이미지 매핑
├── build_vector_index.py         # CLIP 임베딩 + FAISS 인덱스 구축
├── requirements.txt              # Python 의존성
├── .gitignore
└── pitt_ads_dataset/             # (다운로드 후 자동 생성, git 제외)
    ├── annotations/
    │   ├── topics.txt
    │   ├── emotions.txt
    │   ├── qa.json
    │   └── symbolism.json
    └── images/
```

## 실행 순서

### 1단계: 의존성 설치

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 2단계: 데이터셋 다운로드

**Windows (PowerShell):**
```powershell
.\download_pitt_ads.ps1
```
`curl.exe`와 `tar.exe`는 Windows 10 1803+ 및 Windows 11에 기본 포함되어 있다.

**Linux/macOS/WSL:**
```bash
chmod +x download_pitt_ads.sh
./download_pitt_ads.sh
```

### 3단계: 메타데이터 파싱

```powershell
python pitt_ads_parser.py
```
- `pitt_ads_dataset/parsed_records.json` 생성

### 4단계: FAISS 벡터 인덱스 구축

```powershell
python build_vector_index.py
```
- `pitt_ads_dataset/pitt_ads_faiss.index` 생성
- `pitt_ads_dataset/pitt_ads_id_map.json` 생성 (인덱스 → ad_id 매핑)

## 운영 참고 사항

- **대용량 다운로드 재개**: `wget -c` / `curl.exe -C -` 이어받기 옵션 사용. 네트워크 단절 시 재실행하면 이어서 받는다.
- **미디어 유실 검증**: 파서의 `is_valid_media` 플래그로 파일이 실제로 존재하는 레코드만 인덱싱 대상으로 필터링한다.
- **주기적 무결성 검증**: 학술 서버 특성상 파일 유실 가능성이 있으므로 Cron/작업 스케줄러로 정기 검증 권장.

## 라이선스 및 사용 조건

Pitt Ads Dataset은 학술 연구 목적으로 배포된다. 사용 전 원본 웹페이지에서 라이선스와 이용약관을 확인할 것.
