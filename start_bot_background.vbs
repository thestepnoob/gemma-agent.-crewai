Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "C:\Users\iboer\gemma_agent"
WshShell.Run "C:\Windows\System32\cmd.exe /c ""C:\Users\iboer\gemma_agent\start_bot.bat"" --nopause", 0, False
