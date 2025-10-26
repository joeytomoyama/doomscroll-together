// index.js (anonymous, read-only chat -> link queue -> Playwright player)
require('dotenv').config();
const tmi = require('tmi.js');
const { chromium } = require('playwright');
const readline = require('readline');

// ---------- Config ----------
// const CHANNEL_URL = 'https://www.twitch.tv/doomscrolltogether';
const CHANNEL_URL = 'https://www.twitch.tv/skuuii';

const CHANNEL = (process.env.TWITCH_CHANNEL || '').trim().toLowerCase();
if (!CHANNEL) {
  console.error('Set TWITCH_CHANNEL in .env');
  process.exit(1);
}

let ALLOW = {
  youtube: (process.env.ALLOW_YOUTUBE || 'true') === 'true',
  tiktok: (process.env.ALLOW_TIKTOK || 'true') === 'true',
  instagram: (process.env.ALLOW_INSTAGRAM || 'false') === 'true',
};

let MAX_DURATION = parseInt(process.env.MAX_DURATION_SECONDS || '60', 10);
const USER_COOLDOWN = parseInt(process.env.USER_COOLDOWN_SECONDS || '45', 10);

// ---------- State ----------
const urlRegex = /\bhttps?:\/\/[^\s<>"']+/ig;
const queue = [];
const lastSubmitAt = new Map(); // user -> ts
let playing = false;
let paused = false;
let currentItem = null;
let stopTimer = null;
let browser, context, page;

// ---------- Helpers ----------
function domainType(u) {
  try {
    const host = new URL(u).hostname.replace(/^www\./,'').toLowerCase();
    if (host.endsWith('youtube.com') || host === 'youtu.be') return 'youtube';
    if (host.endsWith('tiktok.com')) return 'tiktok';
    if (host.endsWith('instagram.com')) return 'instagram';
    return null;
  } catch { return null; }
}

function allowed(u) {
  const t = domainType(u);
  return t && ALLOW[t];
}

function normalizeUrl(u) {
  try {
    const url = new URL(u);
    if (domainType(u) === 'youtube') {
      let id = null;
      if (url.hostname === 'youtu.be') id = url.pathname.slice(1);
      else if (url.pathname.startsWith('/watch')) id = url.searchParams.get('v');
      else if (url.pathname.startsWith('/shorts/')) id = url.pathname.split('/')[2];
      if (id) return `https://www.youtube.com/embed/${id}?autoplay=1&controls=1&modestbranding=1&rel=0`;
    }
  } catch {}
  return u;
}

async function ensureBrowser() {
  if (browser) return;
  browser = await chromium.launch({
    headless: false,
    args: [
      // keep these
      '--disable-notifications',
      '--disable-features=Translate',
      '--no-default-browser-check',
      // OPTIONAL: you can drop this when idling on Twitch to avoid it trying to autoplay
      // '--autoplay-policy=no-user-gesture-required',
    ],
  });
  context = await browser.newContext({
    viewport: { width: 1280, height: 720 },
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36',
  });
  page = await context.newPage();

  await page.goto(CHANNEL_URL, { waitUntil: 'domcontentloaded' });
//   await ensureChannelMutedAndPaused();
  console.log('Chromium on channel page. Select it in OBS.');
}

async function stopCurrent() {
  if (!page) return;
  clearTimeout(stopTimer);
  try {
    await page.goto(CHANNEL_URL, { waitUntil: 'domcontentloaded', timeout: 15000 });
    await ensureChannelMutedAndPaused();
  } catch {}
}

async function stopCurrent() {
  if (!page) return;
  clearTimeout(stopTimer);
  try { await page.goto('about:blank', { waitUntil: 'domcontentloaded', timeout: 15000 }); } catch {}
}

async function playNext() {
  if (playing || paused) return;
  if (!queue.length) { currentItem = null; return; }

  currentItem = queue.shift();
  playing = true;

  const url = normalizeUrl(currentItem.url);
  console.log(`▶️ Now playing (${currentItem.user}): ${url}`);

  try {
    await ensureBrowser();
    await page.bringToFront();
    await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 45000 });

    // Try to kick autoplay if needed
    await page.evaluate(() => {
      const v = document.querySelector('video');
      if (v) { v.muted = false; v.play?.().catch(()=>{}); }
    }).catch(()=>{});

    // Provider nudges
    const t = domainType(url);
    if (t === 'tiktok' || t === 'instagram') {
      await page.mouse.click(200, 200).catch(()=>{});
    }

    stopTimer = setTimeout(async () => {
      console.log(`⏱️ Max duration reached (${MAX_DURATION}s).`);
      await stopCurrent();
      playing = false;
      currentItem = null;
      setTimeout(playNext, 400);
    }, MAX_DURATION * 1000);

  } catch (e) {
    console.log('⚠️ Failed to load:', url);
    playing = false;
    currentItem = null;
    setTimeout(playNext, 400);
  }
}

function enqueue(url, user) {
  queue.push({ url, user });
  console.log(`✅ Added (#${queue.length}) from ${user}: ${url}`);
}

// ---------- Twitch (anonymous, read-only) ----------
const client = new tmi.Client({
  connection: { secure: true, reconnect: true },
  channels: [CHANNEL],   // No identity => anonymous "justinfan" user
});

client.on('message', (_channel, tags, message, self) => {
  if (self) return;
  const user = (tags['display-name'] || tags.username || 'someone').trim();
  const urls = message.match(urlRegex) || [];
  if (!urls.length) return;

  const now = Date.now();
  const last = lastSubmitAt.get(user) || 0;
  const left = USER_COOLDOWN*1000 - (now - last);
  if (left > 0) {
    const s = Math.ceil(left/1000);
    console.log(`⌛ ${user} on cooldown (${s}s). Ignored message.`);
    return;
  }

  for (const raw of urls) {
    if (!allowed(raw)) {
      const t = domainType(raw) || 'unknown';
      console.log(`🚫 Blocked (${t}) from ${user}: ${raw}`);
      continue;
    }
    enqueue(raw, user);
    lastSubmitAt.set(user, now);
  }

  setTimeout(playNext, 100);
});

client.connect().then(async () => {
  console.log(`Listening to #${CHANNEL} anonymously… paste links in chat!`);
  await ensureBrowser();
});

// ---------- CLI controls (type commands in this terminal) ----------
const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
console.log(`
Commands:
  queue           -> show first items
  skip            -> skip current
  pause           -> pause after current item
  resume          -> resume playback
  allow <k> on/off   (k: youtube|tiktok|instagram)
  duration <sec>  -> set max duration (6..300)
  help            -> show commands
`);

rl.on('line', async (line) => {
  const [cmd, ...rest] = line.trim().split(/\s+/);
  if (!cmd) return;

  if (cmd === 'queue') {
    if (!queue.length) console.log('Queue is empty.');
    else {
      console.log(`In queue (${queue.length}):`);
      queue.slice(0, 8).forEach((q, i) => console.log(`  ${i+1}. ${q.url} (${q.user})`));
      if (queue.length > 8) console.log('  ...');
    }
  }

  if (cmd === 'skip') {
    await stopCurrent();
    playing = false;
    currentItem = null;
    console.log('⏭️ Skipped.');
    setTimeout(playNext, 300);
  }

  if (cmd === 'pause') {
    paused = true;
    console.log('⏸️ Will pause after current item.');
  }

  if (cmd === 'resume') {
    if (paused) {
      paused = false;
      console.log('▶️ Resumed.');
      setTimeout(playNext, 300);
    }
  }

  if (cmd === 'allow') {
    const [key, onoff] = rest;
    if (!['youtube','tiktok','instagram'].includes((key||'').toLowerCase()) || !['on','off'].includes((onoff||'').toLowerCase())) {
      console.log('Usage: allow youtube|tiktok|instagram on|off');
    } else {
      ALLOW[key.toLowerCase()] = (onoff.toLowerCase() === 'on');
      console.log(`Allow ${key.toLowerCase()}: ${ALLOW[key.toLowerCase()] ? 'ON' : 'OFF'}`);
    }
  }

  if (cmd === 'duration') {
    const n = parseInt(rest[0], 10);
    if (!Number.isFinite(n) || n < 6 || n > 300) {
      console.log('Usage: duration <seconds 6..300>');
    } else {
      MAX_DURATION = n;
      console.log(`Max duration set to ${n}s (applies to next item).`);
    }
  }

  if (cmd === 'help') {
    console.log('Commands: queue | skip | pause | resume | allow <k> on/off | duration <sec> | help');
  }
});

// ---------- Nice shutdown ----------
process.on('SIGINT', async () => {
  console.log('\nShutting down…');
  try { await browser?.close(); } catch {}
  process.exit(0);
});
