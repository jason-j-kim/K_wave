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

// 다중 탭 에코로 잔향을 흉내내고, lowpass로 거리감을 더한다.
// 파라미터 의미:
//   aecho=in_gain:out_gain:delays(ms)|...:decays|...
//   - delays  60 / 180 / 500 / 1200 ms 4개 탭
//   - decays  0.5 / 0.4 / 0.3 / 0.2 (멀어질수록 감쇠)
//   lowpass=f=3500  3.5kHz 이상 컷 → 멀리서 들리는 듯한 톤
//   volume=1.1      잔향 합산 후 약간 보강
const DEEP_REVERB_FILTER =
  'aecho=0.8:0.88:60|180|500|1200:0.5|0.4|0.3|0.2,lowpass=f=3500,volume=1.1';

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
