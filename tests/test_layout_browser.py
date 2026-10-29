"""client.js's layout in a live Chromium, at real screen sizes: a short
landscape screen (7.5-inch 800x480, 640x384) gets the picture at the left,
filling almost the full height, with the text in the space beside it; big
landscape and portrait frames keep the poster. The page serves client.js and
a picture from memory; nothing leaves the machine."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from plugins.news_illustrated.tests.fakes import picture

PLUGIN_DIR = Path(__file__).resolve().parent.parent
ORIGIN = "http://layout.test"


def _chromium_available() -> bool:
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            return Path(p.chromium.executable_path).exists()
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _chromium_available(), reason="Playwright Chromium not installed"
)

TITLE = "City council approves long-delayed harbour redevelopment after months of debate"
SUMMARY = (
    "After months of argument the council voted seven to two to approve the harbour "
    "plan, which adds a ferry terminal, a promenade and about four hundred homes."
)

DRAW = """async ([w, h, art, title, summary]) => {
  const mod = await import('/client.js');
  const host = document.getElementById('h');
  host.style.cssText = `width:${w}px;height:${h}px;container-type:size;position:relative;overflow:hidden`;
  const shadow = host.attachShadow({mode: 'open'});
  mod.default(shadow, {cell: {w, h, size: 'lg', options: {}}, locale: 'en', data: {
    title, summary, source: 'World', date: '2026-10-27', index: 2, count: 5,
    image: `/art.jpg?w=${art[0]}&h=${art[1]}`, image_w: art[0], image_h: art[1], look: {}}});
  const img = shadow.querySelector('img');
  await img.decode().catch(() => {});
  const box = e => { const b = e.getBoundingClientRect(); return {x: b.x, y: b.y, w: b.width, h: b.height}; };
  const cap = shadow.querySelector('.cap'), sum = shadow.querySelector('.summary');
  return {cls: shadow.querySelector('.ain').className, art: box(shadow.querySelector('.art')),
          img: box(img), cap: box(cap), capClipped: cap.scrollHeight > cap.clientHeight + 1,
          summaryClipped: sum ? sum.scrollHeight > sum.clientHeight + 1 : false};
}"""


@pytest.fixture(scope="module")
def browser() -> Any:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        b = p.chromium.launch()
        yield b
        b.close()


def _draw(browser: Any, w: int, h: int, art: tuple[int, int]) -> dict[str, Any]:
    page = browser.new_page(viewport={"width": w, "height": h})

    def serve(route: Any) -> None:
        url = route.request.url
        if url.endswith("/client.js"):
            route.fulfill(
                body=(PLUGIN_DIR / "client.js").read_text(encoding="utf-8"),
                content_type="text/javascript",
            )
        elif "/art.jpg" in url:
            route.fulfill(body=picture(*art), content_type="image/jpeg")
        elif url.rstrip("/") == ORIGIN:
            route.fulfill(
                body="<!doctype html><body style='margin:0'><div id=h></div>",
                content_type="text/html",
            )
        else:  # the host's stylesheets: not needed to lay the widget out
            route.fulfill(body="", content_type="text/css")

    page.route(f"{ORIGIN}/**", serve)
    page.goto(ORIGIN + "/")
    try:
        got: dict[str, Any] = page.evaluate(DRAW, [w, h, list(art), TITLE, SUMMARY])
    finally:
        page.close()
    return got


@pytest.mark.parametrize("screen", [(800, 480), (640, 384), (1024, 600)])
@pytest.mark.parametrize(
    "art",
    [(288, 512), (480, 640), (512, 512), (768, 512), (896, 512)],
    ids=lambda a: f"{a[0]}x{a[1]}",
)
def test_a_short_landscape_screen_puts_the_picture_left_at_nearly_full_height(
    browser: Any, screen: tuple[int, int], art: tuple[int, int]
) -> None:
    w, h = screen
    got = _draw(browser, w, h, art)
    assert "is-wide" in got["cls"] and "is-small" in got["cls"]
    a, cap = got["art"], got["cap"]
    margin = 0.025 * h
    assert a["x"] == pytest.approx(margin, abs=1.5)
    assert a["y"] == pytest.approx(margin, abs=1.5)
    assert a["h"] >= 0.94 * h, "nearly the full height"
    assert h - (a["y"] + a["h"]) == pytest.approx(margin, abs=1.5), "the same margin below"
    assert a["w"] <= 0.6 * w + 1
    # The picture fills its box (it is not shrunk and centred inside it).
    assert got["img"]["h"] == pytest.approx(a["h"], abs=1.5)
    # The text takes the rest of the width, and fits.
    assert cap["x"] >= a["x"] + a["w"] - 1
    assert cap["x"] + cap["w"] == pytest.approx(w, abs=1.5)
    assert not got["capClipped"] and not got["summaryClipped"]


@pytest.mark.parametrize(
    ("screen", "art", "wide"),
    [
        ((1920, 1080), (1344, 768), False),
        ((1600, 1200), (1152, 864), False),
        ((1440, 2560), (288, 512), False),
        ((1200, 1600), (864, 1152), False),
        ((480, 800), (288, 512), False),
        ((1600, 1200), (288, 512), True),
    ],
)
def test_bigger_and_portrait_frames_keep_their_layout(
    browser: Any, screen: tuple[int, int], art: tuple[int, int], wide: bool
) -> None:
    got = _draw(browser, *screen, art)
    assert "is-small" not in got["cls"]
    assert ("is-wide" in got["cls"]) is wide
    if not wide:  # the poster: the picture over the whole cell, the caption on it
        assert got["art"] == {"x": 0, "y": 0, "w": screen[0], "h": screen[1]}
        assert got["cap"]["y"] + got["cap"]["h"] == pytest.approx(screen[1], abs=1.5)
