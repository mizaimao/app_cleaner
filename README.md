# App Cleaner

A small native macOS (SwiftUI) app that uninstalls apps *and* their leftovers.
Drag an app onto the window; it finds the files and folders that most likely
belong to it, shows their sizes, and moves the ones you pick to the Trash.

This is a personal tool — built to run unsigned on my own Macs, not for
distribution.

## What it does

- Reads the dropped app's bundle identifier and name from `Contents/Info.plist`.
- Scans the standard macOS leftover locations (user **and** `/Library`):
  `Application Support`, `Caches`, `Preferences`, `Containers`,
  `Group Containers`, `Saved Application State`, `Logs`, `HTTPStorages`,
  `WebKit`, `Cookies`, `Application Scripts`, `LaunchAgents`, `LaunchDaemons`,
  and `PrivilegedHelperTools`.
- Matches by bundle id (and dotted extensions of it) plus folders named exactly
  after the app. Short/ambiguous names are skipped to avoid false positives.
- Shows each match with its recursive size and a checkbox.
- **Double-click a row** (or right-click → Reveal in Finder) to inspect it first.
- Warns if the app is currently running, with a one-click **Quit App** button.
- Deletes by **moving to the Trash** — recoverable, never `rm`.

### How matching works (and its limits)

macOS keeps no retroactive "app X created file Y" log, so this is *heuristic*
matching — the same approach AppCleaner / PearCleaner use. It errs toward not
deleting unrelated data, so it can occasionally miss a leftover stored under an
unrelated name. Always glance at the list before trashing.

## Requirements

- macOS 13 or later.
- **Swift toolchain.** Full Xcode is *not* required — Xcode Command Line Tools
  are enough:
  ```sh
  xcode-select --install
  ```
  Check it worked: `swift --version` should print a version.

## Build

From the project root:

```sh
make build      # release build → build/AppCleaner.app
make run        # build (release) and launch
make debug      # faster debug build
make clean      # remove .build/ and build/
```

Under the hood `make build` runs [`scripts/build_app.sh`](scripts/build_app.sh),
which compiles with `swift build`, assembles `build/AppCleaner.app` around the
binary + [`Resources/Info.plist`](Resources/Info.plist), and ad-hoc code-signs
it so it launches locally without Gatekeeper complaints.

To keep it around, drag `build/AppCleaner.app` into `/Applications`.

## Full Disk Access (important)

Deleting things in `~/Library/Containers`, `Caches`, etc. requires **Full Disk
Access**. Without it those deletes fail and the app tells you so.

Grant it once: **System Settings → Privacy & Security → Full Disk Access → +**,
then add `AppCleaner.app` (wherever you keep it). If it was already running,
quit and relaunch it afterward.

## Project layout

| Path | Purpose |
| --- | --- |
| `Sources/AppCleaner/AppCleanerApp.swift` | App entry point (SwiftUI `App`) |
| `Sources/AppCleaner/ContentView.swift` | Drop zone, list, banners, buttons |
| `Sources/AppCleaner/CleanerModel.swift` | State, scan orchestration, running-app check |
| `Sources/AppCleaner/Scanner.swift` | Matching, size calculation, trashing |
| `Resources/Info.plist` | Bundle metadata used when assembling the `.app` |
| `scripts/build_app.sh` | Compiles and assembles the `.app` bundle |
