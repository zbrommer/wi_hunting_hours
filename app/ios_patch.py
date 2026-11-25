#!/usr/bin/env python3
"""Customize the Capacitor-generated ios/ project (run in CI after `npx cap add ios`).
Sets the app icon, a plain dark launch screen, Info.plist keys and a silent alert sound."""
import json, plistlib, struct, sys, wave, zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "tools"))
from make_icons import png  # same artwork as the website icons

APP = HERE / "ios" / "App" / "App"
ASSETS = APP / "Assets.xcassets"

def solid_png(size, rgb):
    raw = zlib.compress((b"\x00" + bytes(rgb) * size) * size, 9)
    chunk = lambda t, d: struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0)) + chunk(b"IDAT", raw) + chunk(b"IEND", b"")

def one_image_set(folder, name, data, extra):
    for f in folder.glob("*.png"):
        f.unlink()
    (folder / name).write_bytes(data)
    (folder / "Contents.json").write_text(json.dumps(
        {"images": [{"filename": name, "idiom": "universal", **extra}], "info": {"author": "xcode", "version": 1}}, indent=2))

# App icon: one 1024px image, no transparency (App Store rule).
one_image_set(ASSETS / "AppIcon.appiconset", "AppIcon-1024.png", png(1024), {"platform": "ios", "size": "1024x1024"})
# Launch screen: the page's dark background instead of Capacitor's logo (the storyboard fills the screen with it).
one_image_set(ASSETS / "Splash.imageset", "splash.png", solid_png(16, (0x13, 0x20, 0x1B)), {})

plist = APP / "Info.plist"
info = plistlib.loads(plist.read_bytes())
info.update({
    "CFBundleDisplayName": "WI Hours",
    "NSLocationWhenInUseUsageDescription": "Your location picks your shooting-hours zone and area. It stays on your phone.",
    "ITSAppUsesNonExemptEncryption": False,
    "UISupportedInterfaceOrientations": ["UIInterfaceOrientationPortrait"],
    "UIStatusBarStyle": "UIStatusBarStyleLightContent",  # white status bar text over the dark countdown bar
    "UIViewControllerBasedStatusBarAppearance": False,
})
info.pop("UISupportedInterfaceOrientations~ipad", None)
plist.write_bytes(plistlib.dumps(info))

# Alerts vibrate but make no sound (like the website), so they don't spook game.
with wave.open(str(APP / "silence.wav"), "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(8000); w.writeframes(b"\x00\x00" * 4000)
print("ios project patched")
