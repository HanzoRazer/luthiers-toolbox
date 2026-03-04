@echo off
REM Set your API key before running, or set it in environment variables
REM set ANTHROPIC_API_KEY=your-api-key-here
python agent.py --spec specs/production_shop.json --out ./output/production_shop
