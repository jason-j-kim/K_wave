#!/bin/bash
# download_pitt_ads.sh - Pitt Ads Dataset 자동 수집 스크립트 (Linux/macOS/WSL)
set -euo pipefail

DATASET_DIR="./pitt_ads_dataset"
ANNOTATIONS_DIR="${DATASET_DIR}/annotations"
IMAGES_DIR="${DATASET_DIR}/images"
BASE_URL="http://pitt.edu/~akovashka/ads"

echo "[1/4] 디렉터리 구조 생성 중..."
mkdir -p "${ANNOTATIONS_DIR}"
mkdir -p "${IMAGES_DIR}"

echo "[2/4] 메타데이터(Annotations) 다운로드 중..."
wget -c "${BASE_URL}/annotations/topics.txt"    -P "${ANNOTATIONS_DIR}/"
wget -c "${BASE_URL}/annotations/emotions.txt"  -P "${ANNOTATIONS_DIR}/"
wget -c "${BASE_URL}/annotations/qa.json"       -P "${ANNOTATIONS_DIR}/"
wget -c "${BASE_URL}/annotations/symbolism.json" -P "${ANNOTATIONS_DIR}/"

echo "[3/4] 대용량 이미지 아카이브 다운로드 중..."
wget -c "${BASE_URL}/images.tar.gz" -O "${DATASET_DIR}/images.tar.gz"

echo "[4/4] 이미지 아카이브 압축 해제 중..."
tar -xzf "${DATASET_DIR}/images.tar.gz" -C "${IMAGES_DIR}/"
rm "${DATASET_DIR}/images.tar.gz"

echo "데이터 수집 프로세스가 완료되었습니다."
