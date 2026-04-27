#!/usr/bin/env node
/*
 * generate_voices.js
 *
 * parsed.json의 모든 dialogue 라인을 OpenAI tts-1-hd로 합성하여
 * voices/{scene_id}_{line_id}_{speaker}.mp3 로 저장한다.
 *
 * 옵션:
 *   --limit N        처음 N개 라인만 처리
 *   --scene N        scene_id가 N인 장면만 처리
 *   --speaker S      speaker가 S인 라인만 처리 (예: ARKADI)
 */

require('dotenv').config();

const fs = require('fs');
const path = require('path');
const OpenAI = require('openai');
const { applyDeepReverb, isFfmpegAvailable } = require('./post_fx');

const ROOT = path.resolve(__dirname, '..');
const PARSED_PATH = path.join(ROOT, 'script', 'parsed.json');
const VOICES_CONFIG_PATH = path.join(ROOT, 'config', 'voices.json');
const OUTPUT_DIR = path.join(ROOT, 'voices');
const RAW_DIR = path.join(OUTPUT_DIR, 'raw');

const TTS_MODEL = 'tts-1-hd';
const TTS_SPEED_MIN = 0.25;
const TTS_SPEED_MAX = 4.0;

function parseArgs(argv) {
  const args = { limit: null, scene: null, speaker: null };
  for (let i = 0; i < argv.length; i++) {
    const flag = argv[i];
    const value = argv[i + 1];
    if (flag === '--limit') {
      args.limit = Number.parseInt(value, 10);
      i++;
    } else if (flag === '--scene') {
      args.scene = Number.parseInt(value, 10);
      i++;
    } else if (flag === '--speaker') {
      args.speaker = value;
      i++;
    }
  }
  return args;
}

function clampSpeed(speed) {
  if (typeof speed !== 'number' || Number.isNaN(speed)) return 1.0;
  return Math.min(TTS_SPEED_MAX, Math.max(TTS_SPEED_MIN, speed));
}

function collectDialogueLines(parsed, { scene, speaker }) {
  const collected = [];
  for (const sc of parsed.scenes) {
    if (scene !== null && sc.scene_id !== scene) continue;
    for (const line of sc.lines) {
      if (line.type !== 'dialogue') continue;
      if (speaker && line.speaker !== speaker) continue;
      collected.push({ scene_id: sc.scene_id, line });
    }
  }
  return collected;
}

async function synthesizeLine(openai, { scene_id, line }, voicesConfig) {
  const speakerKey = line.speaker;
  const config = voicesConfig[speakerKey];
  if (!config) {
    throw new Error(`config/voices.json에 "${speakerKey}" 매핑이 없습니다.`);
  }

  const fileName = `${scene_id}_${line.line_id}_${speakerKey}.mp3`;
  const finalPath = path.join(OUTPUT_DIR, fileName);
  const rawPath = path.join(RAW_DIR, fileName);

  if (fs.existsSync(finalPath)) {
    return { fileName, status: 'skip' };
  }

  if (!fs.existsSync(rawPath)) {
    const response = await openai.audio.speech.create({
      model: TTS_MODEL,
      voice: config.voice,
      input: line.text,
      speed: clampSpeed(config.speed),
      response_format: 'mp3',
    });
    const buffer = Buffer.from(await response.arrayBuffer());
    fs.writeFileSync(rawPath, buffer);
  }

  if (config.post_fx === 'deep_reverb') {
    await applyDeepReverb(rawPath, finalPath);
    return { fileName, status: 'fx' };
  }

  fs.copyFileSync(rawPath, finalPath);
  return { fileName, status: 'ok' };
}

async function main() {
  const args = parseArgs(process.argv.slice(2));

  if (!process.env.OPENAI_API_KEY) {
    console.error('[ERROR] OPENAI_API_KEY가 설정되지 않았습니다. .env를 확인하세요.');
    process.exit(1);
  }

  fs.mkdirSync(RAW_DIR, { recursive: true });

  const parsed = JSON.parse(fs.readFileSync(PARSED_PATH, 'utf8'));
  const voicesConfig = JSON.parse(fs.readFileSync(VOICES_CONFIG_PATH, 'utf8'));

  let targets = collectDialogueLines(parsed, {
    scene: args.scene,
    speaker: args.speaker,
  });
  if (args.limit !== null) {
    targets = targets.slice(0, args.limit);
  }

  console.log(`[INFO] 대상 라인 수: ${targets.length}`);
  if (args.scene !== null) console.log(`[INFO] --scene ${args.scene}`);
  if (args.speaker) console.log(`[INFO] --speaker ${args.speaker}`);
  if (args.limit !== null) console.log(`[INFO] --limit ${args.limit}`);

  const needsFfmpeg = targets.some(({ line }) => {
    const cfg = voicesConfig[line.speaker];
    return cfg && cfg.post_fx === 'deep_reverb';
  });
  if (needsFfmpeg && !(await isFfmpegAvailable())) {
    console.warn(
      '[WARN] post_fx가 필요한 라인이 있지만 ffmpeg을 PATH에서 찾지 못했습니다. ' +
      '해당 라인은 실패로 표시됩니다. https://www.gyan.dev/ffmpeg/builds/ 에서 ' +
      'essentials 빌드 설치 후 새 터미널에서 다시 실행하세요.'
    );
  }

  const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

  let ok = 0;
  let skipped = 0;
  let failed = 0;

  for (let i = 0; i < targets.length; i++) {
    const item = targets[i];
    const tag = `[${i + 1}/${targets.length}] scene=${item.scene_id} line=${item.line.line_id} speaker=${item.line.speaker}`;
    try {
      const result = await synthesizeLine(openai, item, voicesConfig);
      if (result.status === 'skip') {
        console.log(`${tag} SKIP (이미 존재) -> ${result.fileName}`);
        skipped++;
      } else if (result.status === 'fx') {
        console.log(`${tag} OK+FX (deep_reverb) -> ${result.fileName}`);
        ok++;
      } else {
        console.log(`${tag} OK -> ${result.fileName}`);
        ok++;
      }
    } catch (err) {
      console.error(`${tag} FAIL: ${err.message}`);
      failed++;
    }
  }

  console.log(`\n[DONE] 생성 ${ok} / 스킵 ${skipped} / 실패 ${failed}`);
  if (failed > 0) process.exitCode = 1;
}

main().catch((err) => {
  console.error('[FATAL]', err);
  process.exit(1);
});
