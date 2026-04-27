#!/usr/bin/env node
/*
 * generate_ambience.js
 *
 * 텅 빈 오래된 소극장의 룸톤(에어컨/HVAC 잡음 + 낮은 공간 톤)을
 * ffmpeg의 anoisesrc로 합성해서 audio/ambience.mp3 로 저장한다.
 * 30초 길이로 만들고 Remotion에서 loop=true로 재생.
 *
 * 재실행 시 기존 파일은 덮어쓴다.
 */

const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');

const ROOT = path.resolve(__dirname, '..');
const OUTPUT_DIR = path.join(ROOT, 'audio');
const OUTPUT_PATH = path.join(OUTPUT_DIR, 'ambience.mp3');

const DURATION_SEC = 30;

// 브라운 노이즈 → 200Hz 이하만 통과 (저역 룸톤)
// + 60~120Hz 살짝 강조 (HVAC 저주파 험)
// + 전체 볼륨 줄여서 잔잔한 공간감
const FILTER =
  'lowpass=f=220,equalizer=f=80:width_type=h:w=40:g=4,volume=0.55';

function run() {
  return new Promise((resolve, reject) => {
    const args = [
      '-y',
      '-loglevel', 'error',
      '-f', 'lavfi',
      '-i', `anoisesrc=color=brown:amplitude=0.5:duration=${DURATION_SEC}`,
      '-af', FILTER,
      '-codec:a', 'libmp3lame',
      '-q:a', '4',
      OUTPUT_PATH,
    ];
    const proc = spawn('ffmpeg', args);
    let stderr = '';
    proc.stderr.on('data', (c) => { stderr += c.toString(); });
    proc.on('error', (err) => {
      if (err.code === 'ENOENT') {
        reject(new Error('ffmpeg을 PATH에서 찾을 수 없습니다. 설치 후 새 터미널에서 다시 시도하세요.'));
      } else {
        reject(err);
      }
    });
    proc.on('close', (code) => {
      if (code === 0) resolve();
      else reject(new Error(`ffmpeg exited ${code}: ${stderr.trim()}`));
    });
  });
}

async function main() {
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });
  console.log(`[INFO] ambience 생성 중... (${DURATION_SEC}s)`);
  await run();
  const stat = fs.statSync(OUTPUT_PATH);
  console.log(`[OK] ${OUTPUT_PATH} (${(stat.size / 1024).toFixed(1)} KB)`);
}

main().catch((err) => {
  console.error('[FATAL]', err.message);
  process.exit(1);
});
