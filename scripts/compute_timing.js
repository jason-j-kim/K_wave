#!/usr/bin/env node
/*
 * compute_timing.js
 *
 * voices/ 폴더의 mp3 길이를 ffprobe로 측정하여 Remotion 합성에 쓸
 * script/timing.json을 생성한다.
 *
 * Phase 2: stage_direction 라인도 포함시킨다 (음성 없음, 화면 중앙
 * 이탤릭 오버레이로 표시). duration은 텍스트 길이 기반 추정값
 * (0.12 sec/char, 2.5~6s clamp + 0.5s 여유).
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
 *           { type: "dialogue", line_id, speaker, text, audio,
 *             start_sec_in_scene, duration_sec },
 *           { type: "stage_direction", line_id, speaker: null, text,
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
const TITLES_PATH = path.join(ROOT, 'config', 'titles.json');
const OUTPUT_PATH = path.join(ROOT, 'script', 'timing.json');

const FPS = 30;
const WIDTH = 1920;
const HEIGHT = 1080;
const GAP_BETWEEN_LINES_SEC = 0.3;
const GAP_BETWEEN_SCENES_SEC = 1.0;

// stage_direction 표시 시간 추정
const STAGE_DIR_SEC_PER_CHAR = 0.12;
const STAGE_DIR_MIN_SEC = 2.5;
const STAGE_DIR_MAX_SEC = 6.0;
const STAGE_DIR_TAIL_SEC = 0.5; // 페이드 여유

function estimateStageDirectionDuration(text) {
  const chars = (text || '').length;
  const raw = chars * STAGE_DIR_SEC_PER_CHAR + STAGE_DIR_TAIL_SEC;
  return Math.min(STAGE_DIR_MAX_SEC, Math.max(STAGE_DIR_MIN_SEC, raw));
}

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

  const titles = fs.existsSync(TITLES_PATH)
    ? JSON.parse(fs.readFileSync(TITLES_PATH, 'utf8'))
    : { intro: { duration_sec: 0 }, outro: { duration_sec: 0 }, ambience: { enabled: false } };

  const introDur = Math.max(0, Number(titles.intro?.duration_sec) || 0);
  const outroDur = Math.max(0, Number(titles.outro?.duration_sec) || 0);

  const out = {
    fps: FPS,
    width: WIDTH,
    height: HEIGHT,
    gap_between_lines_sec: GAP_BETWEEN_LINES_SEC,
    gap_between_scenes_sec: GAP_BETWEEN_SCENES_SEC,
    intro: introDur > 0
      ? {
          start_sec: 0,
          duration_sec: introDur,
          fade_in_sec: Number(titles.intro?.fade_in_sec) || 1.0,
          fade_out_sec: Number(titles.intro?.fade_out_sec) || 1.0,
          title: titles.intro?.title || '',
          subtitle: titles.intro?.subtitle || '',
        }
      : null,
    outro: null,
    ambience: titles.ambience?.enabled
      ? {
          file: titles.ambience.file || 'audio/ambience.mp3',
          volume: Number(titles.ambience.volume) || 0.12,
          available: fs.existsSync(path.join(ROOT, titles.ambience.file || 'audio/ambience.mp3')),
        }
      : null,
    total_duration_sec: 0,
    total_duration_frames: 0,
    scenes: [],
  };

  // 인트로 끝나고 0.5초 휴지 후 첫 장면
  const INTRO_TAIL_SEC = introDur > 0 ? 0.5 : 0;
  let cursorSec = introDur + INTRO_TAIL_SEC;
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
    let dialogueCount = 0;

    for (const line of sc.lines) {
      if (line.type === 'dialogue') {
        const audioName = `${sc.scene_id}_${line.line_id}_${line.speaker}.mp3`;
        const audioPath = path.join(VOICES_DIR, audioName);

        if (!fs.existsSync(audioPath)) {
          console.warn(`[WARN] 음성 파일 없음, 스킵: ${audioName}`);
          missing++;
          continue;
        }

        const dur = await getDurationSec(audioPath);

        sceneEntry.lines.push({
          type: 'dialogue',
          line_id: line.line_id,
          speaker: line.speaker,
          text: line.text,
          audio: audioName,
          start_sec_in_scene: inSceneCursor,
          duration_sec: dur,
        });

        inSceneCursor += dur + GAP_BETWEEN_LINES_SEC;
        dialogueCount++;
      } else if (line.type === 'stage_direction') {
        const dur = estimateStageDirectionDuration(line.text);
        sceneEntry.lines.push({
          type: 'stage_direction',
          line_id: line.line_id,
          speaker: null,
          text: line.text,
          start_sec_in_scene: inSceneCursor,
          duration_sec: dur,
        });
        inSceneCursor += dur + GAP_BETWEEN_LINES_SEC;
      }
    }

    // 마지막 라인 뒤의 line-gap은 빼고 scene duration 산정
    sceneEntry.duration_sec = Math.max(
      0,
      inSceneCursor - GAP_BETWEEN_LINES_SEC,
    );

    if (dialogueCount === 0 && sceneEntry.lines.length === 0) {
      console.warn(`[WARN] scene ${sc.scene_id}: 라인 0개, 스킵`);
      continue;
    }

    out.scenes.push(sceneEntry);
    cursorSec = sceneStart + sceneEntry.duration_sec + GAP_BETWEEN_SCENES_SEC;
  }

  // 마지막 scene 뒤의 scene-gap을 빼고 → 아웃트로 진입 전 휴지 포함 → 아웃트로 추가
  const lastSceneEnd = Math.max(0, cursorSec - GAP_BETWEEN_SCENES_SEC);
  const OUTRO_HEAD_SEC = outroDur > 0 ? 0.5 : 0;
  const outroStart = lastSceneEnd + OUTRO_HEAD_SEC;

  if (outroDur > 0) {
    out.outro = {
      start_sec: outroStart,
      duration_sec: outroDur,
      fade_in_sec: Number(titles.outro?.fade_in_sec) || 1.0,
      fade_out_sec: Number(titles.outro?.fade_out_sec) || 1.5,
      title: titles.outro?.title || '',
      subtitle: titles.outro?.subtitle || '',
    };
  }

  out.total_duration_sec = outroStart + outroDur;
  out.total_duration_frames = Math.round(out.total_duration_sec * FPS);

  fs.writeFileSync(OUTPUT_PATH, JSON.stringify(out, null, 2));

  const mins = Math.floor(out.total_duration_sec / 60);
  const secs = Math.round(out.total_duration_sec % 60);
  console.log(`[OK] timing.json 생성: ${OUTPUT_PATH}`);
  console.log(`     scenes=${out.scenes.length}, lines=${out.scenes.reduce((n, s) => n + s.lines.length, 0)}, missing=${missing}`);
  if (out.intro) console.log(`     intro=${introDur}s "${out.intro.title}"`);
  if (out.outro) console.log(`     outro=${outroDur}s "${out.outro.title}"`);
  if (out.ambience) {
    console.log(`     ambience=${out.ambience.file} vol=${out.ambience.volume} ${out.ambience.available ? '(OK)' : '(파일 없음, 생략됨)'}`);
  }
  console.log(`     total=${out.total_duration_sec.toFixed(2)}s (${mins}m ${secs}s) = ${out.total_duration_frames} frames @${FPS}fps`);
}

main().catch((err) => {
  console.error('[FATAL]', err.message);
  process.exit(1);
});
