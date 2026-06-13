# Project Rationale

This document explains the design direction of the project: what kind of retro box
this repo is trying to build, why it makes certain tradeoffs, and how emulator
choices should be evaluated.

## 🎯 Primary Design Goal

The target experience is:

- appliance-like for the player
- flexible enough to mix emulator backends per system
- biased toward real-world playability over conceptual purity

This is not meant to be the most elegant emulator stack possible.
It is meant to be a practical stack that feels good to use on this hardware.

The intended result is a system that behaves like a full-fledged multi-platform
game console at the GUI level. A kid should be able to pick it up, browse games,
launch them, and have a great time without needing to understand what is behind
the curtain.

At the same time, the owner should be able to reach through that console-like
surface and manage the full system when needed. That includes the freedom to tune,
maintain, swap, and expand the emulator stack over remote access, including deeper
administration through tools such as `ssh` and `adb`.

> 🕰️ Once, a kid imagined his room lined wall to wall with consoles from distant places.
> Years passed, the dream grew smaller, stranger, and somehow brighter:
> a thousand little worlds gathered quietly into the palm of a hand. 📺🕹️

## 🧭 Core Strategy

The project follows one main rule:

- use `RetroArch` when it is good enough
- use standalone emulators when they are clearly better

`RetroArch` is valuable because it gives older systems a consistent launch path
and a compact mental model. But forcing every system through RetroArch is not a
design virtue by itself. When a standalone Android emulator performs better,
behaves better, or exposes better device-specific support, that path should win.

## 🎛️ Appliance for the Player, Workshop for the Owner

This project is intentionally two things at once.

For the player, it should feel appliance-like:

- browseable from the couch
- controller-friendly
- clear enough for a child to use comfortably
- shaped like a real console experience rather than a general-purpose computer

For the owner, it is intentionally more open-ended:

- more customizable than a sealed retro appliance
- maintainable at the system level
- expandable when you want to try different emulators or frontend behavior
- friendly to a more hands-on, geek-oriented style of ownership

That is an important distinction. The project is not trying to be the easiest
plug-and-play service to build or maintain. It is trying to be a polished console
for the person holding the controller, while remaining a rich tinkering surface
for the person who owns it.

## 🎮 Emulator Selection Philosophy

The emulator stack should be chosen by class of problem, not by ideology.

### Older Systems

Older systems are good candidates for `RetroArch` when:

- the libretro core is mature
- the overall path is stable and low-friction once established
- performance is already solid
- the frontend consistency is worth more than emulator-specific features

This generally applies to systems such as:

- NES
- SNES
- Genesis

For these, consistency is a feature.

### Heavier Systems

Heavier systems are where this project becomes intentionally less uniform.

Standalone emulators are preferred when they offer a clearer practical advantage for:

- Nintendo 64
- GameCube
- Wii
- PlayStation 1 when DuckStation is preferable to the RetroArch path
- PlayStation 2
- Nintendo 3DS
- Switch

The reason is not just raw frame rate. It is the whole package: graphics backend
quality, driver behavior, compatibility, emulator-specific tuning, and how well
the app fits Android on RK3588-class hardware.

## 🕹️ N64 as the Original Example

Nintendo 64 was one of the clearest reasons this project took shape in the first place.

The N64 case represents the broader pattern:

- a theoretically unified stack is not always the best playing stack
- frontend simplicity should not override emulator quality
- hardware-specific advantages are worth using when they materially improve the result

N64 is therefore less important as a single platform than as the example that defines the project's overall mindset.

## 🧩 Role of the Frontend

`ES-DE` is the user-facing launcher, not the source of truth for emulator quality.

Its job is to provide:

- a clean library view
- controller-friendly navigation
- a unified place to launch games
- enough routing flexibility to point different systems at different emulator backends

The frontend should make backend diversity manageable. It should not force false uniformity.

## ⚖️ What This Project Values

The design priorities are:

- smooth play over strict uniformity
- appliance-like day-to-day use over visible system complexity
- sensible defaults over exhaustive abstraction
- system-by-system pragmatism over one-backend purity
- a console-like user experience over endless tweakability in the main path

This means some inconsistency is acceptable if it buys a meaningfully better result on the device.

## 🔀 Acceptable Tradeoffs

The project accepts that a better stack may also be:

- messier than Batocera
- less standardized across systems
- more dependent on specific Android apps
- more opinionated about which emulator is "best enough"
- more demanding for the maintainer who wants to keep extending the stack

Those are acceptable costs as long as the system is better to actually play on.
