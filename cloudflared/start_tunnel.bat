@echo off
cd /d C:\Users\Truvi\Downloads\proof_model\cloudflared
start cmd /k "cloudflared.exe --config config.yml tunnel run proof-alpha"
