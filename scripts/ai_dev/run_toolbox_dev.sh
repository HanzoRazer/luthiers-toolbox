#!/usr/bin/env bash
set -e

cd packages/client
echo "Starting ToolBox dev server"
npm install
npm run dev
