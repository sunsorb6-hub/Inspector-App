# -*- coding: cp1252 -*-
import platform
import psutil
import sys
import os
import subprocess
import shutil
import ctypes
import socket
from io import StringIO
from datetime import datetime

def is_admin():
    """Check if the script is running with Administrator rights"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False

def require_admin():
    """Force the script to restart in Administrator mode if necessary"""
    if platform.system() != "Windows":
        return True
        
    if not is_admin():
        print("[Info] Administrator rights required. Attempting to restart...")
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit()
    return True

def get_size(bytes, suffix="B"):
    """Convert bytes to readable format (KB, MB, GB, etc.)"""
    factor = 1024
    for unit in ["", "K", "M", "G", "T", "P"]:
        if bytes < factor:
            return f"{bytes:.2f} {unit}{suffix}"
        bytes /= factor

def get_os_info():
    out = StringIO()
    print("--- OPERATING SYSTEM ---", file=out)
    print(f"System    : {platform.system()}", file=out)
    print(f"Version   : {platform.version()}", file=out)
    print(f"Release   : {platform.release()}", file=out)
    print(f"Machine   : {platform.machine()}", file=out)
    print(f"PC Name   : {platform.node()}", file=out)
    return out.getvalue()

def get_cpu_info():
    out = StringIO()
    print("--- PROCESSOR (CPU) ---", file=out)
    print(f"Model          : {platform.processor()}", file=out)
    print(f"Physical Cores : {psutil.cpu_count(logical=False)}", file=out)
    print(f"Logical Cores  : {psutil.cpu_count(logical=True)}", file=out)
    
    try:
        cpufreq = psutil.cpu_freq()
        if cpufreq:
            print(f"Max Frequency  : {cpufreq.max:.2f} Mhz", file=out)
            print(f"Min Frequency  : {cpufreq.min:.2f} Mhz", file=out)
            print(f"Current Freq.  : {cpufreq.current:.2f} Mhz", file=out)
    except Exception:
        pass
    print(f"Utilization    : {psutil.cpu_percent(interval=0.1)}%", file=out)
    return out.getvalue()

def get_gpu_info():
    out = StringIO()
    print("--- GRAPHICS CARD (GPU) ---", file=out)
    sys_type = platform.system()
    
    if sys_type == "Windows":
        try:
            cmd = "wmic path win32_VideoController get Name, DriverVersion /format:csv"
            output = subprocess.check_output(cmd, shell=True).decode('utf-8', errors='ignore')
            lines = [line.strip() for line in output.split('\n') if line.strip()]
            gpu_count = 0
            for line in lines:
                if line.startswith("Node") or "DriverVersion" in line:
                    continue
                parts = line.split(',')
                if len(parts) >= 3:
                    gpu_count += 1
                    print(f"GPU #{gpu_count} : {parts[2]}", file=out)
                    print(f"  Driver   : {parts[1]}", file=out)
            if gpu_count == 0:
                print("No GPU detected.", file=out)
        except Exception:
            print("Unable to retrieve GPU details via WMIC.", file=out)
    elif sys_type == "Linux":
        try:
            output = subprocess.check_output("lspci | grep -i vga", shell=True).decode('utf-8')
            print(f"Hardware: {output.strip()}", file=out)
        except Exception:
            print("The lspci tool is not available.", file=out)
    elif sys_type == "Darwin":
        try:
            cmd = "system_profiler SPDisplaysDataType | grep 'Chipset Model'"
            output = subprocess.check_output(cmd, shell=True).decode('utf-8')
            print(f"{output.strip()}", file=out)
        except Exception:
            print("Unable to retrieve GPU details on macOS.", file=out)
    return out.getvalue()

def get_ram_info():
    out = StringIO()
    print("--- MEMORY (RAM) ---", file=out)
    svmem = psutil.virtual_memory()
    print(f"Total       : {get_size(svmem.total)}", file=out)
    print(f"Available   : {get_size(svmem.available)}", file=out)
    print(f"Used        : {get_size(svmem.used)}", file=out)
    print(f"Percentage  : {svmem.percent}%", file=out)
    return out.getvalue()

def get_disk_info():
    out = StringIO()
    print("--- DISKS ---", file=out)
    try:
        partitions = psutil.disk_partitions()
        for partition in partitions:
            print(f"\nDrive: {partition.device}", file=out)
            print(f"  Mount point  : {partition.mountpoint}", file=out)
            print(f"  File system  : {partition.fstype}", file=out)
            try:
                partition_usage = psutil.disk_usage(partition.mountpoint)
                print(f"  Total Space  : {get_size(partition_usage.total)}", file=out)
                print(f"  Used Space   : {get_size(partition_usage.used)}", file=out)
                print(f"  Free Space   : {get_size(partition_usage.free)}", file=out)
                print(f"  Percentage   : {partition_usage.percent}%", file=out)
            except PermissionError:
                print("  Access denied for this drive.", file=out)
    except Exception as e:
        print(f"Error reading partitions: {e}", file=out)
    return out.getvalue()

def get_net_info():
    out = StringIO()
    print("--- NETWORK ---", file=out)
    try:
        if_addrs = psutil.net_if_addrs()
        for interface_name, interface_addresses in if_addrs.items():
            print(f"\nInterface: {interface_name}", file=out)
            for address in interface_addresses:
                if address.family == socket.AF_INET:
                    print(f"  [IPv4] IP Address : {address.address}", file=out)
                    print(f"         Netmask    : {address.netmask}", file=out)
                    if address.broadcast:
                        print(f"         Broadcast  : {address.broadcast}", file=out)
                elif address.family == getattr(socket, 'AF_INET6', None):
                    print(f"  [IPv6] IP Address : {address.address}", file=out)
    except Exception as e:
        print(f"Unable to retrieve network information: {e}", file=out)
    return out.getvalue()

def inspect_drive(drive_letter):
    print(f"\n--- DRIVE INSPECTION {drive_letter.upper()} ---")
    drive_letter = drive_letter.upper().rstrip('\\')
    if not drive_letter.endswith(':'):
        drive_letter += ':'
    try:
        usage = psutil.disk_usage(drive_letter + '\\')
        print(f"Status          : Accessible")
        print(f"Total Space     : {get_size(usage.total)}")
        print(f"Used Space      : {get_size(usage.used)} ({usage.percent}%)")
        print(f"Free Space      : {get_size(usage.free)}")
        if platform.system() == "Windows":
            clean_letter = drive_letter.replace(':', '')
            cmd = f'powershell "Get-PhysicalDisk | Where-Object {{$_.DeviceID -eq (Get-Partition -DriveLetter {clean_letter}).DiskNumber}} | Select-Object -ExpandProperty MediaType"'
            media_type = subprocess.check_output(cmd, shell=True).decode('utf-8').strip()
            if media_type:
                print(f"Storage type    : {media_type}")
    except Exception as e:
        print(f"Inspection error: {e}")

def inspect_process(target):
    print(f"\n--- PROCESS SEARCH: {target} ---")
    if target.isdigit():
        try:
            p = psutil.Process(int(target))
            print(f"Name: {p.name()} | PID: {p.pid} | Status: {p.status()}")
            print(f"RAM: {get_size(p.memory_info().rss)} | CPU: {p.cpu_percent(interval=0.1)}%")
            return
        except psutil.NoSuchProcess:
            print("PID not found.")
            return

    matching_processes = []
    total_memory = 0
    for proc in psutil.process_iter(['pid', 'name', 'memory_info']):
        try:
            if target in proc.info['name'].lower():
                matching_processes.append(proc)
                if proc.info['memory_info']:
                    total_memory += proc.info['memory_info'].rss
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    if not matching_processes:
        print("No process found.")
        return
    print(f"Instances: {len(matching_processes)} | Total RAM: {get_size(total_memory)}")

def clean_system():
    if platform.system() != "Windows":
        print("Cleanup function is optimized only for Windows.")
        return

    print("\n--- TEMPORARY FOLDERS (CLEANUP) ---")
    confirm = input("Do you want to start cleaning temporary files? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Cleanup cancelled.")
        return

    require_admin()

    paths_to_clean = [
        os.environ.get('TEMP'),
        os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'Temp')
    ]

    bytes_saved = 0
    files_deleted = 0

    for path in paths_to_clean:
        if not path or not os.path.exists(path):
            continue
        print(f"\nCleaning: {path}")
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            try:
                if os.path.isfile(item_path) or os.path.islink(item_path):
                    bytes_saved += os.path.getsize(item_path)
                    os.unlink(item_path)
                    files_deleted += 1
                elif os.path.isdir(item_path):
                    for root, dirs, files in os.walk(item_path):
                        for f in files:
                            fp = os.path.join(root, f)
                            if os.path.exists(fp):
                                bytes_saved += os.path.getsize(fp)
                    shutil.rmtree(item_path)
                    files_deleted += 1
            except Exception:
                continue

    print(f"\n[Success] Cleanup finished.")
    print(f"-> Items deleted: {files_deleted}")
    print(f"-> Disk space recovered: {get_size(bytes_saved)}")

def optimize_system():
    if platform.system() != "Windows":
        print("Process optimization is designed for Windows.")
        return

    print("\n--- PROCESS OPTIMIZATION ---")
    print("This command will close unnecessary telemetry, error reporting, and tracking services.")
    confirm = input("Do you want to continue? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Optimization cancelled.")
        return

    require_admin()

    target_bloatware = [
        "compattelrunner.exe", "wermgr.exe", "werfault.exe", 
        "gamebarftserver.exe", "onedrive.exe", "mobsync.exe", "smartscreen.exe"
    ]

    killed_count = 0
    ram_freed = 0

    for proc in psutil.process_iter(['pid', 'name', 'memory_info']):
        try:
            p_name = proc.info['name'].lower()
            if p_name in target_bloatware:
                ram_freed += proc.info['memory_info'].rss if proc.info['memory_info'] else 0
                proc.kill()
                killed_count += 1
                print(f"  [X] Target identified and closed: {p_name} (PID: {proc.info['pid']})")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    if killed_count == 0:
        print("\nNo unnecessary processes detected or active right now. Your system is already clean!")
    else:
        print(f"\n[Success] Optimization finished.")
        print(f"-> Processes stopped: {killed_count}")
        print(f"-> RAM immediately freed: {get_size(ram_freed)}")

def export_report():
    folder_name = "Reports"
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
        
    now = datetime.now()
    date_texte = now.strftime("%Y-%m-%d at %H:%M:%S")
    filename = now.strftime("%Y-%m-%d_%Hh%Mm%Ss.txt")
    filepath = os.path.join(folder_name, filename)
    
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("=========================================\n")
            f.write("      HARDWARE AND SYSTEM REPORT         \n")
            f.write(f"      Generated on: {date_texte}     \n")
            f.write("=========================================\n\n")
            f.write(get_os_info() + "\n")
            f.write(get_cpu_info() + "\n")
            f.write(get_gpu_info() + "\n")
            f.write(get_ram_info() + "\n")
            f.write(get_disk_info() + "\n")
            f.write(get_net_info() + "\n")
        print(f"\n[Success] Complete report saved in: {os.path.abspath(filepath)}")
    except Exception as e:
        print(f"\n[Error] Export failed: {e}")

def show_help():
    print("\nAvailable commands:")
    print("  os      : Operating system information")
    print("  cpu     : Complete processor details (Frequencies & cores)")
    print("  gpu     : Graphics card models and driver versions")
    print("  ram     : Memory status, sizes, and usage")
    print("  disk    : Comprehensive list of partitions (Mount points & types)")
    print("  inspect : Deep inspect a target drive (e.g., C:)")
    print("  proc    : Analyze a process/software by NAME or PID")
    print("  clean   : [ADMIN] Clean temporary files and caches")
    print("  optimize: [ADMIN] Close unnecessary background processes")
    print("  net     : Network adapters, subnet masks, and active IPs")
    print("  all     : Display all modules on screen")
    print("  export  : Create a dated global report in the 'Reports' folder")
    print("  clear   : Clear the console screen")
    print("  help    : Display this help menu")
    print("  exit    : Close the program\n")

def main():
    status = " (Administrator Mode)" if is_admin() else ""
    print(f"System Monitor & Inspector v4.3{status}")
    print("Enter 'help' to start.")
    
    while True:
        try:
            choix = input("\nSysInfo> ").strip().lower()
            
            if choix == 'help':
                show_help()
            elif choix == 'os':
                print("\n" + get_os_info().strip())
            elif choix == 'cpu':
                print("\n" + get_cpu_info().strip())
            elif choix == 'gpu':
                print("\n" + get_gpu_info().strip())
            elif choix == 'ram':
                print("\n" + get_ram_info().strip())
            elif choix == 'disk':
                print("\n" + get_disk_info().strip())
            elif choix == 'clean':
                clean_system()
            elif choix == 'optimize':
                optimize_system()
            elif choix == 'inspect':
                cible = input("Letter of the drive to inspect (e.g., C): ").strip()
                if cible:
                    inspect_drive(cible)
            elif choix == 'proc':
                cible = input("Name of the program or PID to analyze: ").strip().lower()
                if cible:
                    inspect_process(cible)
            elif choix == 'net':
                print("\n" + get_net_info().strip())
            elif choix == 'all':
                print("\n" + get_os_info() + get_cpu_info() + get_gpu_info() + get_ram_info() + get_disk_info() + get_net_info())
            elif choix == 'export':
                export_report()
            elif choix == 'clear':
                os.system('cls' if os.name == 'nt' else 'clear')
            elif choix in ['exit', 'quit']:
                print("Closing application.")
                break
            elif choix == "":
                continue
            else:
                print("Unknown command. Use 'help'.")
                
        except KeyboardInterrupt:
            print("\nExiting program.")
            break

if __name__ == "__main__":
    main()
