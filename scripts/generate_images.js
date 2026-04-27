#!/usr/bin/env node
/*
 * generate_images.js
 *
 * parsed.json의 각 scene에 대해 DALL-E 3로 장면 이미지를 1장씩 생성한다.
 * 결과: images/scene_{N}.png + images/scene_{N}.prompt.txt
 *
 * 옵션:
 *   --scene N           특정 scene만 생성
 *   --limit N           처음 N개 scene만 생성
 *   --quality hd|standard  config 기본값(hd) 덮어쓰기
 *   --dry-run           API 호출 없이 프롬프트만 출력
 */

require('dotenv').config();

const fs = require('fs');
const path = require('path');
const OpenAI = require('openai');

const ROOT = path.resolve(__dirname, '..');
const PARSED_PATH = path.join(ROOT, 'script', 'parsed.json');
const STYLE_CONFIG_PATH = path.join(ROOT, 'config', 'image_style.json');
const OUTPUT_DIR = path.join(ROOT, 'images');

function parseArgs(argv) {
  const args = { scene: null, limit: null, quality: null, dryRun: false };
  for (let i = 0; i < argv.length; i++) {
    const flag = argv[i];
    const value = argv[i + 1];
    if (flag === '--scene') {
      args.scene = Number.parseInt(value, 10);
      i++;
    } else if (flag === '--limit') {
      args.limit = Number.parseInt(value, 10);
      i++;
    } else if (flag === '--quality') {
      args.quality = value;
      i++;
    } else if (flag === '--dry-run') {
      args.dryRun = true;
    }
  }
  return args;
}

function buildPrompt(scene, parsed, style) {
  const parts = [
    style.style_prefix,
    `Play: "${parsed.title}". Overall stage setting: ${parsed.setting_global}`,
    `Scene ${scene.scene_id} — "${scene.title}". Scene setting: ${scene.setting}`,
    style.negative_hints,
  ];
  return parts.filter(Boolean).join(' ');
}

async function generateScene(openai, scene, parsed, style, opts) {
  const fileName = `scene_${scene.scene_id}.png`;
  const outputPath = path.join(OUTPUT_DIR, fileName);
  const promptPath = path.join(OUTPUT_DIR, `scene_${scene.scene_id}.prompt.txt`);

  if (fs.existsSync(outputPath)) {
    return { fileName, status: 'skip' };
  }

  const prompt = buildPrompt(scene, parsed, style);

  if (opts.dryRun) {
    console.log(`---- scene ${scene.scene_id} prompt ----`);
    console.log(prompt);
    console.log('');
    return { fileName, status: 'dry' };
  }

  const result = await openai.images.generate({
    model: style.model || 'dall-e-3',
    prompt,
    size: style.size || '1792x1024',
    quality: opts.quality || style.quality || 'hd',
    n: 1,
    response_format: 'b64_json',
  });

  const item = result.data[0];
  const buffer = Buffer.from(item.b64_json, 'base64');
  fs.writeFileSync(outputPath, buffer);

  const promptRecord =
    `=== prompt sent ===\n${prompt}\n\n` +
    `=== DALL-E revised_prompt ===\n${item.revised_prompt || '(none)'}\n`;
  fs.writeFileSync(promptPath, promptRecord);

  return { fileName, status: 'ok' };
}

async function main() {
  const args = parseArgs(process.argv.slice(2));

  if (!args.dryRun && !process.env.OPENAI_API_KEY) {
    console.error('[ERROR] OPENAI_API_KEY가 설정되지 않았습니다. .env를 확인하세요.');
    process.exit(1);
  }

  fs.mkdirSync(OUTPUT_DIR, { recursive: true });

  const parsed = JSON.parse(fs.readFileSync(PARSED_PATH, 'utf8'));
  const style = JSON.parse(fs.readFileSync(STYLE_CONFIG_PATH, 'utf8'));

  let scenes = parsed.scenes;
  if (args.scene !== null) scenes = scenes.filter((s) => s.scene_id === args.scene);
  if (args.limit !== null) scenes = scenes.slice(0, args.limit);

  console.log(`[INFO] 대상 scene 수: ${scenes.length}`);
  if (args.scene !== null) console.log(`[INFO] --scene ${args.scene}`);
  if (args.limit !== null) console.log(`[INFO] --limit ${args.limit}`);
  if (args.quality) console.log(`[INFO] --quality ${args.quality}`);
  if (args.dryRun) console.log('[INFO] --dry-run (API 미호출)');

  const openai = args.dryRun
    ? null
    : new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

  let ok = 0;
  let skipped = 0;
  let dry = 0;
  let failed = 0;

  for (let i = 0; i < scenes.length; i++) {
    const sc = scenes[i];
    const tag = `[${i + 1}/${scenes.length}] scene=${sc.scene_id}`;
    try {
      const result = await generateScene(openai, sc, parsed, style, args);
      if (result.status === 'skip') {
        console.log(`${tag} SKIP (이미 존재) -> ${result.fileName}`);
        skipped++;
      } else if (result.status === 'dry') {
        dry++;
      } else {
        console.log(`${tag} OK -> ${result.fileName}`);
        ok++;
      }
    } catch (err) {
      console.error(`${tag} FAIL: ${err.message}`);
      failed++;
    }
  }

  console.log(`\n[DONE] 생성 ${ok} / 스킵 ${skipped} / 드라이 ${dry} / 실패 ${failed}`);
  if (failed > 0) process.exitCode = 1;
}

main().catch((err) => {
  console.error('[FATAL]', err);
  process.exit(1);
});
