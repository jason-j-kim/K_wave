/*
 * post_fx.js
 *
 * 합성된 TTS 음성에 후처리 이펙트를 적용한다.
 *
 * 모듈 사용:
 *   const { applyDeepReverb } = require('./post_fx');
 *   await applyDeepReverb('voices/raw/3_3.5_ARKADI.mp3',
 *                         'voices/3_3.5_ARKADI.mp3');
 *
 * CLI 사용 (단일 파일 튜닝용):
 *   node scripts/post_fx.js <input.mp3> <output.mp3>
 */

const { spawn } = require('child_process');

// 다중 탭 에코로 잔향을 흉내내고, lowpass로 약간의 거리감만 더한다.
// Phase 2 튜닝: 대사 명료도를 우선해 wet 신호를 줄였다.
//   aecho=in_gain:out_gain:delays(ms)|...:decays|...
//   - in_gain  0.9     원본(dry)을 더 강하게 통과
//   - delays   60/150/400 ms  3개 탭 (가장 긴 1200ms는 제거)
//   - decays   0.30/0.20/0.12  잔향 꼬리 약화
//   lowpass=f=4500  4.5kHz 컷 → 약간의 거리감만, 대사는 또렷
const DEEP_REVERB_FILTER =
  'aecho=0.9:0.9:60|150|400:0.30|0.20|0.12,lowpass=f=4500,volume=1.0';

/**
 * 입력 음성에 깊은 리버브를 적용해 출력 경로에 저장한다.
 * 아르카디(영원한 관객)의 목소리에 사용할 공간감 효과.
 *
 * @param {string} inputPath  처리 전 mp3 경로
 * @param {string} outputPath 결과 파일 경로
 * @returns {Promise<void>}
 */
function applyDeepReverb(inputPath, outputPath) {
  return new Promise((resolve, reject) => {
    const args = [
      '-y',
      '-loglevel', 'error',
      '-i', inputPath,
      '-af', DEEP_REVERB_FILTER,
      outputPath,
    ];

    const proc = spawn('ffmpeg', args);

    let stderr = '';
    proc.stderr.on('data', (chunk) => { stderr += chunk.toString(); });

    proc.on('error', (err) => {
      if (err.code === 'ENOENT') {
        reject(new Error(
          'ffmpeg을 PATH에서 찾을 수 없습니다. ' +
          'https://www.gyan.dev/ffmpeg/builds/ 에서 essentials 빌드를 ' +
          '설치하고 PATH에 등록한 뒤 새 터미널에서 다시 시도하세요.'
        ));
      } else {
        reject(err);
      }
    });

    proc.on('close', (code) => {
      if (code === 0) {
        resolve();
      } else {
        reject(new Error(`ffmpeg exited ${code}: ${stderr.trim() || 'unknown error'}`));
      }
    });
  });
}

/**
 * ffmpeg이 PATH에 존재하는지 가볍게 확인. 없으면 false.
 * @returns {Promise<boolean>}
 */
function isFfmpegAvailable() {
  return new Promise((resolve) => {
    const proc = spawn('ffmpeg', ['-version']);
    proc.on('error', () => resolve(false));
    proc.on('close', (code) => resolve(code === 0));
  });
}

module.exports = {
  applyDeepReverb,
  isFfmpegAvailable,
  DEEP_REVERB_FILTER,
};

if (require.main === module) {
  const [input, output] = process.argv.slice(2);
  if (!input || !output) {
    console.error('Usage: node scripts/post_fx.js <input.mp3> <output.mp3>');
    process.exit(1);
  }
  applyDeepReverb(input, output)
    .then(() => console.log(`OK -> ${output}`))
    .catch((err) => {
      console.error('FAIL:', err.message);
      process.exit(1);
    });
}
