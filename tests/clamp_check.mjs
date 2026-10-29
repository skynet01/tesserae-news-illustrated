// Plain-node self-check, run by tests/test_clamp_check.py (or: node tests/clamp_check.mjs).
// How much summary each screen gets.
import assert from "node:assert/strict";
import { layoutFor, smallArtBox, summaryLines } from "../client.js";

const title = 88; // characters
// The 32-inch portrait panel: the picture on top, a full summary below.
assert.ok(summaryLines(1440, 2560, false, true, title) >= 4);
// A 13-inch 1600x1200: side by side, a long summary.
const big = summaryLines(1600, 1200, true, true, title);
// A 7.5-inch 800x480: side by side, a shorter summary that still fits.
const small = summaryLines(800, 480, true, true, title);
assert.ok(small >= 2 && small < big, `${small} < ${big}`);
// ... and fits: headline (4 lines at most), source line and summary within
// the height.
const titleFont = Math.max(13, Math.min(64, 0.06 * 480));
const used = 4 * titleFont * 1.12 + small * Math.max(11, 0.034 * 480) * 1.45 + 0.17 * 480;
assert.ok(used <= 480, `${used} > 480`);
// A small tile: a few lines at most.
assert.ok(summaryLines(300, 200, true, true, title) <= 5);

// Which layout a cell gets.
const side = (w, h, ratio) => layoutFor(w, h, true, ratio);
// A short landscape screen puts the picture at the left, whatever its shape.
for (const [w, h] of [[800, 480], [640, 384], [1024, 600]]) {
  for (const ratio of [9 / 16, 3 / 4, 1, 3 / 2, 16 / 9]) {
    assert.deepEqual(side(w, h, ratio), { wide: true, small: true }, `${w}x${h} ${ratio}`);
  }
}
// ... a big landscape frame keeps the poster unless the picture is tall,
assert.deepEqual(side(1920, 1080, 16 / 9), { wide: false, small: false });
assert.deepEqual(side(1600, 1200, 4 / 3), { wide: false, small: false });
assert.deepEqual(side(1600, 1200, 9 / 16), { wide: true, small: false });
// ... and a portrait or square cell, or a cell with no picture, is never side by side.
assert.deepEqual(side(480, 800, 9 / 16), { wide: false, small: false });
assert.deepEqual(side(480, 480, 1), { wide: false, small: false });
assert.deepEqual(layoutFor(800, 480, false, 9 / 16), { wide: false, small: false });
// The picture's box: nearly the full height, a small margin round it, and
// never more than 60% of the width.
for (const [w, h, ratio] of [[800, 480, 9 / 16], [800, 480, 1], [800, 480, 16 / 9], [640, 384, 3 / 4]]) {
  const box = smallArtBox(w, h, ratio);
  assert.ok(box.h >= 0.9 * h && box.y > 0 && box.y + box.h < h, `${w}x${h} height ${box.h}`);
  assert.ok(Math.abs(box.y - (h - box.y - box.h)) < 0.01, "same margin above and below");
  assert.equal(box.x, box.y, "same margin left as top");
  assert.ok(box.w <= 0.6 * w + 0.01, `${w}x${h} width ${box.w}`);
}
assert.ok(Math.abs(smallArtBox(800, 480, 9 / 16).w - 0.95 * 480 * (9 / 16)) < 0.01, "a tall picture keeps its own shape");
// The summary still fits beside the smaller picture, on a square one too.
assert.ok(summaryLines(800, 480, true, true, title, 1) >= 1);
console.log("news_illustrated clamp_check: ok");
