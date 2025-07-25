#!/bin/bash
cd /Users/Truvi/Downloads/proof_model

source venv/Scripts/activate
nohup python app.py > flask.log 2>&1 &

cloudflared tunnel run proof-alpha > tunnel.log 2>&1 &
