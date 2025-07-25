Set WshShell = CreateObject("WScript.Shell")
WshShell.Run chr(34) & "C:\Users\Truvi\Downloads\proof_model\cloudflared\start_tunnel.bat" & Chr(34), 0
Set WshShell = Nothing
