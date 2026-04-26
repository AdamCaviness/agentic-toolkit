# Changelog

## [0.8.0](https://github.com/AdamCaviness/agentic-toolkit/compare/v0.7.0...v0.8.0) (2026-04-26)


### Features

* **get-it-right:** footprint guard before auto-implementation ([#60](https://github.com/AdamCaviness/agentic-toolkit/issues/60)) ([cc495b8](https://github.com/AdamCaviness/agentic-toolkit/commit/cc495b8e920ead57fa2c7f9e9e3eadbd12d032b4))

## [0.7.0](https://github.com/AdamCaviness/agentic-toolkit/compare/v0.6.4...v0.7.0) (2026-04-26)


### Features

* **triage:** quality pass for shared template and skills ([#58](https://github.com/AdamCaviness/agentic-toolkit/issues/58)) ([113ba2c](https://github.com/AdamCaviness/agentic-toolkit/commit/113ba2c1d501f8233869fc536171b6aed68f45c8))

## [0.6.4](https://github.com/AdamCaviness/agentic-toolkit/compare/v0.6.3...v0.6.4) (2026-04-26)


### Refactoring

* **triage:** extract shared orchestration source ([#30](https://github.com/AdamCaviness/agentic-toolkit/issues/30)) ([#56](https://github.com/AdamCaviness/agentic-toolkit/issues/56)) ([b5b40cf](https://github.com/AdamCaviness/agentic-toolkit/commit/b5b40cfe5b76cd053d1d5116fd9295f277dc873d))

## [0.6.3](https://github.com/AdamCaviness/agentic-toolkit/compare/v0.6.2...v0.6.3) (2026-04-26)


### Refactoring

* **skills:** forbid concrete Claude-only leaks in public skills ([#53](https://github.com/AdamCaviness/agentic-toolkit/issues/53)) ([10d05c2](https://github.com/AdamCaviness/agentic-toolkit/commit/10d05c2ca146c0e078a746f29e97e7ce77aa2067)), closes [#35](https://github.com/AdamCaviness/agentic-toolkit/issues/35)

## [0.6.2](https://github.com/AdamCaviness/agentic-toolkit/compare/v0.6.1...v0.6.2) (2026-04-26)


### Bug Fixes

* **convert-worktree:** split preservation from history ([#33](https://github.com/AdamCaviness/agentic-toolkit/issues/33)) ([#51](https://github.com/AdamCaviness/agentic-toolkit/issues/51)) ([4f7a75c](https://github.com/AdamCaviness/agentic-toolkit/commit/4f7a75c7c24e9bf26d449c75ea811c8e6e3faf7f))

## [0.6.1](https://github.com/AdamCaviness/agentic-toolkit/compare/v0.6.0...v0.6.1) (2026-04-26)


### Bug Fixes

* **pr:** add publish state gate so user work cannot be skipped ([#49](https://github.com/AdamCaviness/agentic-toolkit/issues/49)) ([2bee0b0](https://github.com/AdamCaviness/agentic-toolkit/commit/2bee0b0afd72197f250653e80be77b8113d5b654)), closes [#36](https://github.com/AdamCaviness/agentic-toolkit/issues/36)

## [0.6.0](https://github.com/AdamCaviness/agentic-toolkit/compare/v0.5.2...v0.6.0) (2026-04-26)


### Features

* **skill:** mark pr and ship as mechanical to skip model invocation ([#47](https://github.com/AdamCaviness/agentic-toolkit/issues/47)) ([42e1ba0](https://github.com/AdamCaviness/agentic-toolkit/commit/42e1ba04b793017e7ffbd3df0162c86e33c28464)), closes [#29](https://github.com/AdamCaviness/agentic-toolkit/issues/29)

## [0.5.2](https://github.com/AdamCaviness/agentic-toolkit/compare/v0.5.1...v0.5.2) (2026-04-26)


### Refactoring

* **skills:** centralize branch lifecycle contract ([#27](https://github.com/AdamCaviness/agentic-toolkit/issues/27)) ([#45](https://github.com/AdamCaviness/agentic-toolkit/issues/45)) ([3c5e837](https://github.com/AdamCaviness/agentic-toolkit/commit/3c5e8371d3592f0376bbd0bd1c9273120f35d647))

## [0.5.1](https://github.com/AdamCaviness/agentic-toolkit/compare/v0.5.0...v0.5.1) (2026-04-26)


### Bug Fixes

* **code-review:** include untracked paths in review scope ([#43](https://github.com/AdamCaviness/agentic-toolkit/issues/43)) ([211e7b0](https://github.com/AdamCaviness/agentic-toolkit/commit/211e7b07f26e76fcc6753fa02538bf5e3c98c1fe)), closes [#37](https://github.com/AdamCaviness/agentic-toolkit/issues/37)

## [0.5.0](https://github.com/AdamCaviness/agentic-toolkit/compare/v0.4.3...v0.5.0) (2026-04-26)


### Features

* **skill:** add untrusted content boundary ([e4384a3](https://github.com/AdamCaviness/agentic-toolkit/commit/e4384a3f52350a028bff4d085d1a0ab196cba8f4)), closes [#28](https://github.com/AdamCaviness/agentic-toolkit/issues/28)

## [0.4.3](https://github.com/AdamCaviness/agentic-toolkit/compare/v0.4.2...v0.4.3) (2026-04-26)


### Bug Fixes

* **skill:** preserve directive obligations ([6340ee2](https://github.com/AdamCaviness/agentic-toolkit/commit/6340ee2ff463df4d1065630e77e2379eb087a13e)), closes [#38](https://github.com/AdamCaviness/agentic-toolkit/issues/38)

## [0.4.2](https://github.com/AdamCaviness/agentic-toolkit/compare/v0.4.1...v0.4.2) (2026-04-25)


### Bug Fixes

* **skill:** enforce next-ticket branch gate ([#25](https://github.com/AdamCaviness/agentic-toolkit/issues/25)) ([fdd6e2a](https://github.com/AdamCaviness/agentic-toolkit/commit/fdd6e2a68d7c709cb7e2cf1ac2e764af5a34e6a1))

## [0.4.1](https://github.com/AdamCaviness/agentic-toolkit/compare/v0.4.0...v0.4.1) (2026-04-24)


### Bug Fixes

* **ci:** retrigger release-please + refactor code-review skill ([#23](https://github.com/AdamCaviness/agentic-toolkit/issues/23)) ([7aa4b05](https://github.com/AdamCaviness/agentic-toolkit/commit/7aa4b058a6c1d64164b36014a25f017084ad32d3))

## [0.4.0](https://github.com/AdamCaviness/agentic-toolkit/compare/v0.3.1...v0.4.0) (2026-04-24)


### Features

* **next-ticket:** team-safe claiming + model-judgement detection ([#20](https://github.com/AdamCaviness/agentic-toolkit/issues/20)) ([ed70c3c](https://github.com/AdamCaviness/agentic-toolkit/commit/ed70c3c02cd99f2f1949f882e0caf78a331fb653))


### Bug Fixes

* **ci:** prevent docs-only commits from triggering releases ([#18](https://github.com/AdamCaviness/agentic-toolkit/issues/18)) ([b106c5b](https://github.com/AdamCaviness/agentic-toolkit/commit/b106c5b5552c72b028c6b90c47baa3716586575e))

## [0.3.1](https://github.com/AdamCaviness/agentic-toolkit/compare/v0.3.0...v0.3.1) (2026-04-23)


### Bug Fixes

* **ci:** prevent docs-only commits from triggering releases ([#18](https://github.com/AdamCaviness/agentic-toolkit/issues/18)) ([b106c5b](https://github.com/AdamCaviness/agentic-toolkit/commit/b106c5b5552c72b028c6b90c47baa3716586575e))

## [0.3.0](https://github.com/AdamCaviness/agentic-toolkit/compare/v0.2.1...v0.3.0) (2026-04-22)


### Features

* **skill:** add compress-markdown skill ([#13](https://github.com/AdamCaviness/agentic-toolkit/issues/13)) ([ba2fbe6](https://github.com/AdamCaviness/agentic-toolkit/commit/ba2fbe6b8548dda73aec17f51e62658737502b39))

## [0.2.1](https://github.com/AdamCaviness/agentic-toolkit/compare/v0.2.0...v0.2.1) (2026-04-19)


### Bug Fixes

* **skill:** fix bot PR detection in update-deps ([#10](https://github.com/AdamCaviness/agentic-toolkit/issues/10)) ([9ab5b79](https://github.com/AdamCaviness/agentic-toolkit/commit/9ab5b792863266b651867f8d1e75ac8c2bae1385))

## [0.2.0](https://github.com/AdamCaviness/agentic-toolkit/compare/v0.1.0...v0.2.0) (2026-04-19)


### Features

* **skill:** add update-deps skill ([#7](https://github.com/AdamCaviness/agentic-toolkit/issues/7)) ([041394d](https://github.com/AdamCaviness/agentic-toolkit/commit/041394d40197545589d8e216c5a42b2ee63664d8))
