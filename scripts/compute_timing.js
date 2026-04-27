#!/usr/bin/env node
/*
 * compute_timing.js
 *
 * voices/ 폴더의 mp3 길이를 ffprobe로 측정하여 Remotion 합성에 쓸
 * script/timing.json을 생성한다.
 *
 * 출력 구조:
 *   {
 *     fps, width, height,
 *     gap_between_lines_sec, gap_between_scenes_sec,
 *     total_duration_sec, total_duration_frames,
 *     scenes: [
 *       {
 *         scene_id, title, setting, image,
 *         start_sec, duration_sec,
 *         lines: [
 *           { line_id, speaker, text, audio,
 *             start_sec_in_scene, duration_sec }
 *         ]
 *       }
 *     ]
 *   }
 */

const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');

const ROOT = path.resolve(__dirname, '..');
const PARSED_PATH = path.join(ROOT, 'script', 'parsed.json');
const VOICES_DIR = path.join(ROOT, 'voices');
const OUTPUT_PATH = path.join(ROOT, 'script', 'timing.json');

const FPS = 30;
const WIDTH = 1920;
const HEIGHT = 1080;
const GAP_BETWEEN_LINES_SEC = 0.3;
const GAP_BETWEEN_SCENES_SEC = 1.0;

function getDurationSec(filePath) {
  return new Promise((resolve, reject) => {
    const proc = spawn('ffprobe', [
      '-v', 'error',
      '-show_entries', 'format=duration',
      '-of', 'csv=p=0',
      filePath,
    ]);
    let stdout = '';
    let stderr = '';
    proc.stdout.on('data', (c) => { stdout += c.toString(); });
    proc.stderr.on('data', (c) => { stderr += c.toString(); });
    proc.on('error', (err) => {
      if (err.code === 'ENOENT') {
        reject(new Error('ffprobe을 PATH에서 찾을 수 없습니다 (ffmpeg 설치에 포함됨).'));
      } else {
        reject(err);
      }
    });
    proc.on('close', (code) => {
      if (code !== 0) {
        reject(new Error(`ffprobe exited ${code}: ${stderr.trim()}`));
        return;
      }
      const sec = Number.parseFloat(stdout.trim());
      if (!Number.isFinite(sec)) {
        reject(new Error(`duration 파싱 실패: "${stdout.trim()}"`));
        return;
      }
      resolve(sec);
    });
  });
}

async function main() {
  const parsed = JSON.parse(fs.readFileSync(PARSED_PATH, 'utf8'));

  const out = {
    fps: FPS,
    width: WIDTH,
    height: HEIGHT,
    gap_between_lines_sec: GAP_BETWEEN_LINES_SEC,
    gap_between_scenes_sec: GAP_BETWEEN_SCENES_SEC,
    total_duration_sec: 0,
    total_duration_frames: 0,
    scenes: [],
  };

  let cursorSec = 0;
  let missing = 0;

  for (const sc of parsed.scenes) {
    const sceneStart = cursorSec;
    const sceneEntry = {
      scene_id: sc.scene_id,
      title: sc.title,
      setting: sc.setting,
      image: `scene_${sc.scene_id}.png`,
      start_sec: sceneStart,
      duration_sec: 0,
      lines: [],
    };

    let inSceneCursor = 0;

    for (const line of sc.lines) {
      if (line.type !== 'dialogue') continue;
      const audioName = `${sc.scene_id}_${line.line_id}_${line.speaker}.mp3`;
      const audioPath = path.join(VOICES_DIR, audioName);

      if (!fs.existsSync(audioPath)) {
        console.warn(`[WARN] 음성 파일 없음, 스킵: ${audioName}`);
        missing++;
        continue;
      }

      const dur = await getDurationSec(audioPath);

      sceneEntry.lines.push({
        line_id: line.line_id,
        speaker: line.speaker,
        text: line.text,
        audio: audioName,
        start_sec_in_scene: inSceneCursor,
        duration_sec: dur,
      });

      inSceneCursor += dur + GAP_BETWEEN_LINES_SEC;
    }

    // 마지막 라인 뒤의 line-gap은 빼고 scene duration 산정
    sceneEntry.duration_sec = Math.max(
      0,
      inSceneCursor - GAP_BETWEEN_LINES_SEC,
    );

    if (sceneEntry.lines.length === 0) {
      console.warn(`[WARN] scene ${sc.scene_id}: dialogue 라인 0개, 스킵`);
      continue;
    }

    out.scenes.push(sceneEntry);
    cursorSec = sceneStart + sceneEntry.duration_sec + GAP_BETWEEN_SCENES_SEC;
  }

  // 마지막 scene 뒤의 scene-gap은 총길이에서 제외
  out.total_duration_sec = Math.max(0, cursorSec - GAP_BETWEEN_SCENES_SEC);
  out.total_duration_frames = Math.round(out.total_duration_sec * FPS);

  fs.writeFileSync(OUTPUT_PATH, JSON.stringify(out, null, 2));

  const mins = Math.floor(out.total_duration_sec / 60);
  const secs = Math.round(out.total_duration_sec % 60);
  console.log(`[OK] timing.json 생성: ${OUTPUT_PATH}`);
  console.log(`     scenes=${out.scenes.length}, lines=${out.scenes.reduce((n, s) => n + s.lines.length, 0)}, missing=${missing}`);
  console.log(`     total=${out.total_duration_sec.toFixed(2)}s (${mins}m ${secs}s) = ${out.total_duration_frames} frames @${FPS}fps`);
}

main().catch((err) => {
  console.error('[FATAL]', err.message);
  process.exit(1);
});
