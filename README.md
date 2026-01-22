# Skillio

> AI Agent 的能力发现与装配中枢

[![PyPI version](https://badge.fury.io/py/skillio.svg)](https://badge.fury.io/py/skillio)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## What is Skillio?

Skillio is an **intent-to-capability matching engine** for AI Agents. Instead of knowing which tools exist, you simply describe what you want to do, and Skillio finds the right skill for you.

```bash
# Traditional way: You need to know the tool name
$ yt-dlp https://youtube.com/watch?v=xxx

# Skillio way: Just describe your intent
$ skillio search "download YouTube video"
→ Recommended: video-downloader (powered by yt-dlp)

$ skillio install video-downloader
→ Skill installed to ~/.cursor/skills/
```

## Core Philosophy

**Old approach (Supply-side)**: User needs to know "what tools exist"

**Skillio approach (Demand-side)**: User just describes "what they want to do"

## Installation

```bash
pip install skillio
```

## Quick Start

### Search for Skills

```bash
# Natural language search
skillio search "I want to convert video to GIF"
skillio search "下载 B 站视频"
skillio search "PDF to Word"

# Keyword search
skillio search --keyword "video download"
```

### Install Skills

```bash
# Install a skill
skillio install video-downloader

# Install to specific location
skillio install video-downloader --target ~/.cursor/skills/
```

### Manage Installed Skills

```bash
# List installed skills
skillio list

# Show skill details
skillio info video-downloader

# Update a skill
skillio update video-downloader

# Remove a skill
skillio remove video-downloader
```

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   User / AI Agent                    │
│              "I want to convert video to GIF"        │
└─────────────────────┬───────────────────────────────┘
                      ▼
┌─────────────────────────────────────────────────────┐
│              Layer 3: Intent Understanding           │
│   - Natural language parsing                         │
│   - Capability tag extraction                        │
└─────────────────────┬───────────────────────────────┘
                      ▼
┌─────────────────────────────────────────────────────┐
│              Layer 2: Capability Matching            │
│   - Reverse index: tags → skills                     │
│   - Ranking: quality, relevance, popularity          │
└─────────────────────┬───────────────────────────────┘
                      ▼
┌─────────────────────────────────────────────────────┐
│              Layer 1: Skill Repository               │
│   - Metadata storage                                 │
│   - Version management                               │
│   - Source tracking (GitHub/Docs/Manual)             │
└─────────────────────────────────────────────────────┘
```

## Skill Schema

Each skill is defined with structured metadata:

```yaml
name: video-downloader
version: 1.0.0
source:
  type: github
  repo: yt-dlp/yt-dlp
description: Download videos from YouTube, Bilibili, and 1000+ sites
capabilities:
  - video download
  - YouTube
  - Bilibili
  - batch download
scenarios:
  - download video
  - save video for offline
  - extract audio from video
dependencies:
  - python >= 3.8
  - ffmpeg
```

## Roadmap

- [x] **Phase 1**: MVP - Intent matching engine (CLI)
- [ ] **Phase 2**: Platform - Online registry (skillio.dev)
- [ ] **Phase 3**: Ecosystem - Cross-platform skill standard

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Links

- Website: [skillio.dev](https://skillio.dev)
- GitHub: [github.com/copyboy/skillio](https://github.com/copyboy/skillio)
- PyPI: [pypi.org/project/skillio](https://pypi.org/project/skillio)
