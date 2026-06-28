// 2GIS firm-id discovery (Step A), offline. Reads branches from a JSON file, drives a
// headless browser to read firm candidates near each branch from the 2gis.kz search page,
// and writes candidates back. Name+geo matching is done in Python (single source of truth).
//
//   node collect_firms.mjs <input.json> <output.json>
//
// input:  [{ branch_id, clinic, city_path, lat, lon }]
// output: [{ branch_id, firms: [{ firm_id, name, address, lat, lon, rating, reviews_count }] }]
//
// Chromium is resolved from the local ms-playwright cache (no browser download). This never
// runs in the user/search path — it is a background backfill tool.

import { chromium } from "playwright-core";
import { execSync } from "node:child_process";
import { readFileSync, writeFileSync } from "node:fs";

const [inPath, outPath] = process.argv.slice(2);
if (!inPath || !outPath) {
  console.error("usage: node collect_firms.mjs <input.json> <output.json>");
  process.exit(2);
}

function chromiumPath() {
  const fromEnv = process.env.CHROMIUM_PATH;
  if (fromEnv) return fromEnv;
  return execSync(
    "ls -d ~/Library/Caches/ms-playwright/chromium-*/chrome-mac/Chromium.app/Contents/MacOS/Chromium 2>/dev/null | tail -1",
    { shell: "/bin/zsh" },
  )
    .toString()
    .trim();
}

const UA =
  "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36";

function firmFromItem(it) {
  if (!it || !it.id || !it.point) return null;
  const rv = it.reviews || {};
  return {
    firm_id: String(it.id),
    name: it.name || it.full_name || "",
    address: it.address_name || it.full_name || null,
    lat: it.point.lat,
    lon: it.point.lon,
    rating: rv.general_rating ?? null,
    reviews_count: rv.general_review_count ?? null,
  };
}

async function collectForBranch(page, branch) {
  const firmsById = new Map();
  const onResponse = async (resp) => {
    const u = resp.url();
    if (!(u.includes("catalog.api.2gis") && u.includes("/items"))) return;
    try {
      const j = await resp.json();
      for (const it of j?.result?.items || []) {
        const f = firmFromItem(it);
        if (f) firmsById.set(f.firm_id, f);
      }
    } catch {
      /* non-json */
    }
  };
  page.on("response", onResponse);
  try {
    const url = `https://2gis.kz/${branch.city_path}/search/${encodeURIComponent(
      branch.clinic,
    )}/center/${branch.lon},${branch.lat}/zoom/16`;
    await page.goto(url, { waitUntil: "domcontentloaded", timeout: 45000 });
    await page.waitForTimeout(1200);
    const accept = await page.$("#acceptRiskButton");
    if (accept) {
      await accept.click().catch(() => {});
      await page.waitForTimeout(2000);
    }
    await page.waitForTimeout(2500);
    if (firmsById.size === 0) {
      await page.reload({ waitUntil: "domcontentloaded", timeout: 45000 }).catch(() => {});
      await page.waitForTimeout(4000);
    }
    // Fallback: read the firm-id-keyed profile map straight out of initialState.
    const fromState = await page.evaluate(() => {
      const prof = window.initialState?.data?.entity?.profile || {};
      return Object.values(prof)
        .map((p) => p?.data)
        .filter((d) => d && d.id && d.point && d.point.lat != null);
    });
    for (const d of fromState) {
      const f = firmFromItem(d);
      if (f && !firmsById.has(f.firm_id)) firmsById.set(f.firm_id, f);
    }
  } finally {
    page.off("response", onResponse);
  }
  return [...firmsById.values()];
}

const branches = JSON.parse(readFileSync(inPath, "utf-8"));
const browser = await chromium.launch({ executablePath: chromiumPath() });
const context = await browser.newContext({ userAgent: UA });
const page = await context.newPage();
const out = [];
let done = 0;
for (const branch of branches) {
  let firms = [];
  try {
    firms = await collectForBranch(page, branch);
  } catch (err) {
    console.error(`branch ${branch.branch_id} failed: ${err?.message || err}`);
  }
  out.push({ branch_id: branch.branch_id, firms });
  done += 1;
  if (done % 10 === 0) console.error(`  collected ${done}/${branches.length}`);
  await page.waitForTimeout(500);
}
await browser.close();
writeFileSync(outPath, JSON.stringify(out, null, 2));
console.error(`done: ${out.length} branches, wrote ${outPath}`);
