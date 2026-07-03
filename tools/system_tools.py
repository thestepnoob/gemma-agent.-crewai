import os
import subprocess
import time
from typing import Optional
from crewai.tools import BaseTool

class ExecuteTerminalCommandTool(BaseTool):
    name: str = "Terminal Befehl ausfuehren"
    description: str = (
        "Führt einen Terminal-Befehl (Windows CMD oder PowerShell) auf dem PC aus "
        "und gibt die Standard- und Fehlerausgabe zurück. Der Befehl wird standardmäßig "
        "im Projektverzeichnis ausgeführt."
    )

    def _run(self, command: str) -> str:
        cwd = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=90
            )
            
            def decode_output(b: bytes) -> str:
                if not b: return ""
                for encoding in ["utf-8", "cp850", "cp1252", "latin-1"]:
                    try: return b.decode(encoding)
                    except UnicodeDecodeError: continue
                return b.decode("utf-8", errors="replace")
            
            stdout_str = decode_output(result.stdout)
            stderr_str = decode_output(result.stderr)
            
            output_parts = []
            if stdout_str: output_parts.append(f"Standardausgabe (stdout):\n{stdout_str}")
            if stderr_str: output_parts.append(f"Fehlerausgabe (stderr):\n{stderr_str}")
            if not stdout_str and not stderr_str:
                output_parts.append("Befehl wurde ausgeführt, hat aber keine Ausgabe erzeugt.")
            
            output_parts.append(f"Exit-Code: {result.returncode}")
            return "\n\n".join(output_parts)
            
        except subprocess.TimeoutExpired:
            return "Fehler: Die Ausführung des Befehls hat das Zeitlimit von 90 Sekunden überschritten."
        except Exception as e:
            return f"Fehler bei der Ausführung des Befehls: {str(e)}"

class SystemMonitorTool(BaseTool):
    name: str = "System und Hardware Status"
    description: str = "Gibt den aktuellen Systemstatus aus (CPU-Auslastung, RAM-Verbrauch, Festplattenspeicher)."

    def _run(self) -> str:
        try:
            import psutil
            import platform
            import datetime
            
            cpu_percent = psutil.cpu_percent(interval=0.5)
            ram = psutil.virtual_memory()
            disk = psutil.disk_usage("C:\\")
            boot_time = datetime.datetime.fromtimestamp(psutil.boot_time()).strftime("%d.%m.%Y %H:%M:%S")
            
            info = [
                "=== System- & Hardware-Status ===",
                f"Betriebssystem: {platform.system()} {platform.release()} (Arch: {platform.machine()})",
                f"CPU-Auslastung: {cpu_percent}%",
                f"RAM-Auslastung: {ram.percent}% (Frei: {ram.available // (1024**2)} MB / Gesamt: {ram.total // (1024**2)} MB)",
                f"Speicherplatz (C:): {disk.percent}% belegt (Frei: {disk.free // (1024**3)} GB / Gesamt: {disk.total // (1024**3)} GB)",
                f"System-Startzeit: {boot_time}"
            ]
            return "\n".join(info)
        except Exception as e:
            return f"Fehler beim Abrufen des Systemstatus: {str(e)}"

class HardwarePerformanceDiagnosticTool(BaseTool):
    name: str = "Hardware und Leistung Diagnose"
    description: str = (
        "Führt eine umfassende System- und Leistungsanalyse durch. "
        "Liest Live-Sensoren aus HWiNFO aus und ermittelt die Top-5 CPU- und RAM-fressenden Prozesse."
    )

    def _run(self) -> str:
        import psutil
        import datetime
        import winreg
        import re
        
        report = []
        report.append("=== SYSTEM- UND LEISTUNGDIAGNOSE ===")
        report.append(f"Zeitpunkt: {datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n")
        
        report.append("--- HWiNFO64 Sensordaten (Echtzeit) ---")
        hwinfo_lines = []
        try:
            root_path = r"Software\HWiNFO64\VSB"
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, root_path) as key:
                num_values = winreg.QueryInfoKey(key)[1]
                temp_data = {}
                for i in range(num_values):
                    name, val, _ = winreg.EnumValue(key, i)
                    match = re.match(r"^(Sensor|Label|Value|ValueRaw|Color)(\d+)$", name)
                    if match:
                        prefix, idx = match.groups()
                        idx = int(idx)
                        if idx not in temp_data: temp_data[idx] = {}
                        temp_data[idx][prefix] = val
                
                for idx in sorted(temp_data.keys()):
                    item = temp_data[idx]
                    sensor = item.get("Sensor", "")
                    label = item.get("Label", "")
                    value = item.get("Value", "")
                    if sensor or label:
                        s_str = str(sensor).replace("\u00e4", "ae").replace("\u00f6", "oe").replace("\u00fc", "ue")
                        l_str = str(label).replace("\u00e4", "ae").replace("\u00f6", "oe").replace("\u00fc", "ue")
                        v_str = str(value).replace("\u00b0", " Grad").replace("\u00c2\u00b0", " Grad")
                        hwinfo_lines.append(f"- [{s_str}] {l_str}: {v_str}")
        except Exception:
            pass
            
        if hwinfo_lines:
            report.extend(hwinfo_lines)
        else:
            report.append("Keine HWiNFO-Registry-Daten gefunden.")
        report.append("")
        
        try:
            res = subprocess.run(
                "nvidia-smi --query-gpu=temperature.gpu,utilization.gpu,power.draw,clocks.throttle_reasons.active --format=csv,noheader",
                shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=5
            )
            if res.returncode == 0 and res.stdout.strip():
                gpu_info = res.stdout.strip().split(",")
                if len(gpu_info) >= 4:
                    report.append("--- NVIDIA GPU Status (nvidia-smi) ---")
                    report.append(f"- Temperatur: {gpu_info[0].strip()}°C")
                    report.append(f"- Kernlast: {gpu_info[1].strip()}")
                    report.append(f"- Stromverbrauch: {gpu_info[2].strip()}")
                    report.append(f"- Throttling aktiv: {gpu_info[3].strip()}\n")
        except Exception:
            pass
            
        report.append("--- Top-5 CPU-fressende Prozesse ---")
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name']):
                try: processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied): pass
            
            time.sleep(0.2)
            cpu_proc_list = []
            for p in processes:
                try:
                    p_obj = psutil.Process(p['pid'])
                    cpu = p_obj.cpu_percent()
                    mem = p_obj.memory_info().rss / (1024 * 1024)
                    cpu_proc_list.append({'pid': p['pid'], 'name': p['name'], 'cpu': cpu, 'mem': mem})
                except Exception:
                    pass
            
            top_cpu = sorted(cpu_proc_list, key=lambda x: x['cpu'], reverse=True)[:5]
            for p in top_cpu:
                report.append(f"- {p['name']} (PID: {p['pid']}): {p['cpu']:.1f}% CPU | {p['mem']:.1f} MB RAM")
                
            report.append("\n--- Top-5 RAM-fressende Prozesse ---")
            top_ram = sorted(cpu_proc_list, key=lambda x: x['mem'], reverse=True)[:5]
            for p in top_ram:
                report.append(f"- {p['name']} (PID: {p['pid']}): {p['mem']:.1f} MB RAM | {p['cpu']:.1f}% CPU")
        except Exception as proc_err:
            report.append(f"Fehler beim Erfassen der Prozesse: {str(proc_err)}")
            
        return "\n".join(report)

class DiskManagementTool(BaseTool):
    name: str = "Datentraeger Verwaltung und Diagnose"
    description: str = (
        "Diagnostiziert physische Festplatten und logische Volumes. "
        "Aktionen: 'list_physical', 'list_volumes', 'diagnose_volume' (benötigt 'drive_letter')."
    )

    def _run(self, action: str, drive_letter: Optional[str] = None) -> str:
        action = action.lower().strip()
        
        if action == "list_physical":
            cmd = "powershell -Command \"Get-PhysicalDisk | Select-Object DeviceId, Model, Size, MediaType, OperationalStatus, HealthStatus | Format-List\""
            try:
                result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=15)
                return result.stdout if result.stdout else "Keine physischen Datenträger gefunden."
            except Exception as e:
                return f"Fehler: {str(e)}"
                
        elif action == "list_volumes":
            cmd = "powershell -Command \"Get-Volume | Select-Object DriveLetter, FriendlyName, FileSystemType, Size, SizeRemaining, HealthStatus | Format-List\""
            try:
                result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=15)
                return result.stdout if result.stdout else "Keine Volumes gefunden."
            except Exception as e:
                return f"Fehler: {str(e)}"
                
        elif action == "diagnose_volume":
            if not drive_letter: return "Fehler: 'drive_letter' wird benötigt (z. B. 'D:')."
            
            drive_letter = drive_letter.upper().strip()
            import re
            if not re.match(r"^[A-Z]:?$", drive_letter):
                return f"Fehler: Ungültiger Laufwerksbuchstabe '{drive_letter}'."
            if not drive_letter.endswith(":"): drive_letter += ":"
                
            cmd_chk = f"chkdsk {drive_letter}"
            cmd_vol = f"powershell -Command \"Get-Volume -DriveLetter {drive_letter[0]} | Format-List\""
            
            report = [f"=== DIAGNOSE FÜR LAUFWERK {drive_letter} ==="]
            try:
                res_vol = subprocess.run(cmd_vol, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10)
                if res_vol.returncode == 0:
                    report.append("\n--- Volume-Details ---")
                    report.append(res_vol.stdout.strip())
                
                report.append("\n--- Dateisystem-Diagnose (chkdsk) ---")
                res_chk = subprocess.run(cmd_chk, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=60)
                report.append(res_chk.stdout.strip() if res_chk.stdout else "Keine Ausgabe.")
                return "\n".join(report)
            except Exception as e:
                return f"Fehler bei Diagnose: {str(e)}"
        
        else:
            return f"Unbekannte Aktion '{action}'."
