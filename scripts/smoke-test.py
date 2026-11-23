#!/usr/bin/env python3
"""Replay actual private-client CLI setup and meaningful refusal cases using fictional fixtures."""
from pathlib import Path
import os,subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
r=subprocess.run([sys.executable,'-m','unittest','discover','-s',str(ROOT/'tests'),'-p','test_*.py','-v'],cwd=ROOT,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
sys.exit(r.returncode)
