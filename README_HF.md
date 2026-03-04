---
title: ROAR Item Generator
emoji: 🦁
colorFrom: blue
colorTo: purple
sdk: gradio
sdk_version: 5.11.0
app_file: app_gradio.py
pinned: false
license: mit
---

# ROAR Assessment Item Generator

Generate reading comprehension items with AI-powered difficulty estimation.

## Features
- AI-powered item generation using Claude
- Automatic difficulty estimation using ModernBERT
- Save and export items to CSV
- Interactive chat interface

## Model
Uses a custom-trained difficulty estimation model (ModernBERT + Ridge Regression)
