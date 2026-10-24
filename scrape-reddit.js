const { chromium } = require('playwright');
const fs = require('fs');
const OUT = process.argv[2];
const SRC = 'https://www.reddit.com/r/ClaudeAI/';
const MAX_POSTS = 50, MAX_THREADS = 10, MAX_COMMENTS = 50;
const ND = 'not displayed';
const cols = ['row_type','source_url','checked_at','access_status','title','text','permalink','subreddit','author','date_or_relative_time','score','comment_count','parent_post_permalink','note'];
const esc = v => { v = (v === undefined || v === null || v === '') ? ND : String(v); return /[",\n\r]/.test(v) ? '"' + v.replace(/"/g, '""') + '"' : v; };
const abs = u => u ? new URL(u, 'https://www.reddit.com').href : ND;
const rows = [];
const now = () => new Date().toISOString().replace(/\.\d+Z$/, 'Z');
const blockedCheck = async p => {
  const t = (await p.locator('body').innerText().catch(() => '')).toLowerCase();
  if (/prove your humanity|are you a robot|blocked by network security|verify you are human|whoa there, pardner/.test(t)) return 'blocked:robot_check';
  return null;
};
(async () => {
  const b = await chromium.launch({ proxy: { server: process.env.HTTPS_PROXY } });
  const ctx = await b.newContext({ userAgent: 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36', viewport: { width: 1280, height: 2000 } });
  const p = await ctx.newPage();
  const checked = now();
  let status = 'ok', note = '';
  try {
    const r = await p.goto(SRC, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForTimeout(4000);
    const bc = await blockedCheck(p);
    if (bc || r.status() >= 400) { status = bc || `blocked:http_${r.status()}`; }
  } catch (e) { status = 'blocked:navigation_error'; note = e.message.split('\n')[0]; }
  const posts = [];
  if (status === 'ok') {
    let stale = 0, last = 0;
    while (stale < 6) {
      const n = await p.locator('shreddit-post').count();
      if (n >= MAX_POSTS) break;
      stale = n === last ? stale + 1 : 0; last = n;
      await p.mouse.wheel(0, 4000); await p.waitForTimeout(1500);
      if (await blockedCheck(p)) { status = 'blocked:robot_check'; break; }
    }
    const data = await p.$$eval('shreddit-post', els => els.map(e => ({
      title: e.getAttribute('post-title'), permalink: e.getAttribute('permalink'),
      subreddit: e.getAttribute('subreddit-prefixed-name'), author: e.getAttribute('author'),
      created: e.getAttribute('created-timestamp'), score: e.getAttribute('score'),
      comments: e.getAttribute('comment-count'),
      text: (e.querySelector('[slot="text-body"]')?.innerText || '').trim(),
      promoted: e.hasAttribute('is-promoted') || e.getAttribute('promoted') !== null,
    })));
    const seen = new Set();
    for (const d of data) { if (d.promoted || !d.permalink || seen.has(d.permalink)) continue; seen.add(d.permalink); posts.push(d); if (posts.length >= MAX_POSTS) break; }
  }
  rows.push({ row_type: 'status', source_url: SRC, checked_at: checked, access_status: status, subreddit: 'r/ClaudeAI', note: note || `feed posts recorded: ${posts.length}` });
  for (const d of posts) rows.push({ row_type: 'post', source_url: SRC, checked_at: checked, access_status: 'ok', title: d.title, text: d.text, permalink: abs(d.permalink), subreddit: d.subreddit, author: d.author, date_or_relative_time: d.created, score: d.score, comment_count: d.comments, note: 'feed card; text is feed preview if shown' });
  const threads = [];
  for (const d of posts.slice(0, MAX_THREADS)) {
    if (status !== 'ok') break;
    const url = abs(d.permalink); const t = now();
    try {
      const r = await p.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 });
      await p.waitForTimeout(4000);
      const bc = await blockedCheck(p);
      if (bc || r.status() >= 400) { status = bc || `blocked:http_${r.status()}`; rows.push({ row_type: 'status', source_url: url, checked_at: t, access_status: status, subreddit: d.subreddit, note: 'run stopped here' }); break; }
      for (let i = 0; i < 4; i++) { await p.mouse.wheel(0, 4000); await p.waitForTimeout(1200); }
      const body = await p.$eval('shreddit-post [slot="text-body"]', e => e.innerText.trim()).catch(() => '');
      const cs = await p.$$eval('shreddit-comment', els => els.map(e => { const own = sel => [...e.querySelectorAll(sel)].find(x => x.closest('shreddit-comment') === e); return {
        author: e.getAttribute('author'), permalink: e.getAttribute('permalink'), score: e.getAttribute('score'),
        depth: e.getAttribute('depth'), time: own('time')?.getAttribute('datetime') || own('faceplate-timeago')?.getAttribute('ts'),
        text: (own('[slot="comment"]')?.innerText || '').trim(),
      }; }));
      const kept = cs.slice(0, MAX_COMMENTS);
      threads.push({ url, total: cs.length, kept: kept.length });
      if (body) { const pr = rows.find(x => x.row_type === 'post' && x.permalink === url); if (pr) { pr.text = body; pr.note = 'feed card; text from opened thread'; } }
      for (const c of kept) rows.push({ row_type: 'comment', source_url: url, checked_at: t, access_status: 'ok', text: c.text, permalink: abs(c.permalink), subreddit: d.subreddit, author: c.author, date_or_relative_time: c.time, score: c.score, parent_post_permalink: url, note: `depth ${c.depth ?? '?'}` });
    } catch (e) { rows.push({ row_type: 'status', source_url: url, checked_at: t, access_status: 'error:navigation', subreddit: d.subreddit, note: e.message.split('\n')[0] }); }
    await p.waitForTimeout(2000);
  }
  rows[0].access_status = status;
  fs.writeFileSync(OUT, '﻿' + cols.join(',') + '\n' + rows.map(r => cols.map(c => esc(r[c])).join(',')).join('\n') + '\n');
  console.log(JSON.stringify({ status, posts: posts.length, threads, comments: rows.filter(r => r.row_type === 'comment').length, checked }, null, 1));
  await b.close();
})();
