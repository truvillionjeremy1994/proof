@echo off
cd /d C:\Users\Truvi\Downloads\proof_model

call venv\Scripts\activate.bat

start /min python app.py
start /min cloudflared tunnel run proof-alpha