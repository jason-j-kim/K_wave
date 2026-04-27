/*
 * post_fx.js
 *
 * 합성된 TTS 음성에 후처리 이펙트를 적용한다.
 * 현재는 함수 시그니처와 골격만 정의하며, 실제 ffmpeg 명령은
 * 다음 단계에서 구현한다.
 */

const { spawn } = require('child_process');

/**
 * 입력 음성에 깊은 리버브를 적용해 출력 경로에 저장한다.
 * 아르카디(영원한 관객)의 목소리에 사용할 공간감 효과.
 *
 * @param {string} inputPath  처리 전 mp3/wav 경로
 * @param {string} outputPath 결과 파일 경로
 * @returns {Promise<void>}
 */
function applyDeepReverb(inputPath, outputPath) {
  // TODO: ffmpeg을 spawn하여 aecho 또는 reverb 필터를 적용한다.
  //   예시 (확정 전):
  //     ffmpeg -i <input> -af "aecho=0.8:0.9:1000:0.3" <output>
  //   또는 SoX의 reverb를 ffmpeg afir/freeverb 등으로 대체.
  //   파라미터(딜레이/감쇠/믹스)는 실제 청취 후 튜닝.
  void spawn;
  void inputPath;
  void outputPath;
  return Promise.reject(new Error('applyDeepReverb: not implemented yet'));
}

module.exports = {
  applyDeepReverb,
};
