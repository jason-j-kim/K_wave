# download_pitt_ads.ps1 - Pitt Ads Dataset 자동 수집 스크립트 (Windows PowerShell)
$ErrorActionPreference = "Stop"

$DatasetDir     = ".\pitt_ads_dataset"
$AnnotationsDir = Join-Path $DatasetDir "annotations"
$ImagesDir      = Join-Path $DatasetDir "images"
$BaseUrl        = "http://pitt.edu/~akovashka/ads"

Write-Host "[1/4] 디렉터리 구조 생성 중..."
New-Item -ItemType Directory -Path $AnnotationsDir -Force | Out-Null
New-Item -ItemType Directory -Path $ImagesDir      -Force | Out-Null

function Get-FileResume {
    param([string]$Url, [string]$OutFile)
    if (Test-Path $OutFile) {
        Write-Host "  이미 존재: $OutFile (스킵)"
        return
    }
    Write-Host "  다운로드: $Url"
    # 이어받기 지원을 위해 curl.exe 사용 (Windows 10+ 기본 포함)
    & curl.exe -L -C - -o $OutFile $Url
    if ($LASTEXITCODE -ne 0) { throw "다운로드 실패: $Url" }
}

Write-Host "[2/4] 메타데이터(Annotations) 다운로드 중..."
Get-FileResume "$BaseUrl/annotations/topics.txt"    (Join-Path $AnnotationsDir "topics.txt")
Get-FileResume "$BaseUrl/annotations/emotions.txt"  (Join-Path $AnnotationsDir "emotions.txt")
Get-FileResume "$BaseUrl/annotations/qa.json"       (Join-Path $AnnotationsDir "qa.json")
Get-FileResume "$BaseUrl/annotations/symbolism.json" (Join-Path $AnnotationsDir "symbolism.json")

Write-Host "[3/4] 대용량 이미지 아카이브 다운로드 중..."
$ArchivePath = Join-Path $DatasetDir "images.tar.gz"
Get-FileResume "$BaseUrl/images.tar.gz" $ArchivePath

Write-Host "[4/4] 이미지 아카이브 압축 해제 중..."
& tar.exe -xzf $ArchivePath -C $ImagesDir
if ($LASTEXITCODE -ne 0) { throw "압축 해제 실패" }
Remove-Item $ArchivePath

Write-Host "데이터 수집 프로세스가 완료되었습니다."
