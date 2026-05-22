# -*- coding: cp1252 -*-
import platform
import psutil
import sys
import os
import subprocess
import shutil
import ctypes
import socket  # Fiabilise la détection des adresses IP (IPv4 / IPv6)
from io import StringIO
from datetime import datetime

def is_admin():
    """Vérifie si le script est exécuté avec les droits Administrateur"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False

def require_admin():
    """Force la relance du script en mode Administrateur si nécessaire"""
    if platform.system() != "Windows":
        return True
        
    if not is_admin():
        print("[Info] Droits administrateur requis. Tentative de relance...")
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit()
    return True

def get_size(bytes, suffix="o"):
    """Convertit les octets en format lisible (Ko, Mo, Go, etc.)"""
    factor = 1024
    for unit in ["", "K", "M", "G", "T", "P"]:
        if bytes < factor:
            return f"{bytes:.2f} {unit}{suffix}"
        bytes /= factor

def get_os_info():
    out = StringIO()
    print("--- SYSTÈME D'EXPLOITATION ---", file=out)
    print(f"Système   : {platform.system()}", file=out)
    print(f"Version   : {platform.version()}", file=out)
    print(f"Édition   : {platform.release()}", file=out)
    print(f"Machine   : {platform.machine()}", file=out)
    print(f"Nom du PC : {platform.node()}", file=out)
    return out.getvalue()

def get_cpu_info():
    out = StringIO()
    print("--- PROCESSEUR (CPU) ---", file=out)
    print(f"Modèle         : {platform.processor()}", file=out)
    print(f"Cœurs Physiques: {psutil.cpu_count(logical=False)}", file=out)
    print(f"Cœurs Logiques : {psutil.cpu_count(logical=True)}", file=out)
    
    try:
        cpufreq = psutil.cpu_freq()
        if cpufreq:
            print(f"Fréquence Max  : {cpufreq.max:.2f} Mhz", file=out)
            print(f"Fréquence Min  : {cpufreq.min:.2f} Mhz", file=out)
            print(f"Fréquence Act. : {cpufreq.current:.2f} Mhz", file=out)
    except Exception:
        pass
    print(f"Utilisation    : {psutil.cpu_percent(interval=0.1)}%", file=out)
    return out.getvalue()

def get_gpu_info():
    out = StringIO()
    print("--- CARTE GRAPHIQUE (GPU) ---", file=out)
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
                    print(f"  Pilote   : {parts[1]}", file=out)
            if gpu_count == 0:
                print("Aucun GPU détecté.", file=out)
        except Exception:
            print("Impossible de récupérer les détails du GPU via WMIC.", file=out)
    elif sys_type == "Linux":
        try:
            output = subprocess.check_output("lspci | grep -i vga", shell=True).decode('utf-8')
            print(f"Matériel : {output.strip()}", file=out)
        except Exception:
            print("L'outil lspci n'est pas disponible.", file=out)
    elif sys_type == "Darwin":
        try:
            cmd = "system_profiler SPDisplaysDataType | grep 'Chipset Model'"
            output = subprocess.check_output(cmd, shell=True).decode('utf-8')
            print(f"{output.strip()}", file=out)
        except Exception:
            print("Impossible de récupérer les détails du GPU sur macOS.", file=out)
    return out.getvalue()

def get_ram_info():
    out = StringIO()
    print("--- MÉMOIRE (RAM) ---", file=out)
    svmem = psutil.virtual_memory()
    print(f"Totale      : {get_size(svmem.total)}", file=out)
    print(f"Disponible  : {get_size(svmem.available)}", file=out)
    print(f"Utilisée    : {get_size(svmem.used)}", file=out)
    print(f"Pourcentage : {svmem.percent}%", file=out)
    return out.getvalue()

def get_disk_info():
    out = StringIO()
    print("--- DISQUES ---", file=out)
    try:
        partitions = psutil.disk_partitions()
        for partition in partitions:
            print(f"\nLecteur : {partition.device}", file=out)
            print(f"  Point de montage : {partition.mountpoint}", file=out)
            print(f"  Système de fich. : {partition.fstype}", file=out)
            try:
                partition_usage = psutil.disk_usage(partition.mountpoint)
                print(f"  Espace Total     : {get_size(partition_usage.total)}", file=out)
                print(f"  Espace Utilisé   : {get_size(partition_usage.used)}", file=out)
                print(f"  Espace Libre     : {get_size(partition_usage.free)}", file=out)
                print(f"  Pourcentage      : {partition_usage.percent}%", file=out)
            except PermissionError:
                print("  Accès refusé pour ce lecteur.", file=out)
    except Exception as e:
        print(f"Erreur lors de la lecture des partitions : {e}", file=out)
    return out.getvalue()

def get_net_info():
    out = StringIO()
    print("--- RÉSEAU ---", file=out)
    try:
        if_addrs = psutil.net_if_addrs()
        for interface_name, interface_addresses in if_addrs.items():
            print(f"\nInterface : {interface_name}", file=out)
            for address in interface_addresses:
                # Utilisation de socket.AF_INET pour l'IPv4 de manière universelle
                if address.family == socket.AF_INET:
                    print(f"  [IPv4] Adresse IP : {address.address}", file=out)
                    print(f"         Masque     : {address.netmask}", file=out)
                    if address.broadcast:
                        print(f"         Broadcast  : {address.broadcast}", file=out)
                # Optionnel : détection IPv6
                elif address.family == getattr(socket, 'AF_INET6', None):
                    print(f"  [IPv6] Adresse IP : {address.address}", file=out)
    except Exception as e:
        print(f"Impossible de récupérer les informations réseau : {e}", file=out)
    return out.getvalue()

def inspect_drive(drive_letter):
    print(f"\n--- INSPECTION DU LECTEUR {drive_letter.upper()} ---")
    drive_letter = drive_letter.upper().rstrip('\\')
    if not drive_letter.endswith(':'):
        drive_letter += ':'
    try:
        usage = psutil.disk_usage(drive_letter + '\\')
        print(f"Statut             : Accessible")
        print(f"Espace Total       : {get_size(usage.total)}")
        print(f"Espace Utilisé     : {get_size(usage.used)} ({usage.percent}%)")
        print(f"Espace Libre       : {get_size(usage.free)}")
        if platform.system() == "Windows":
            clean_letter = drive_letter.replace(':', '')
            cmd = f'powershell "Get-PhysicalDisk | Where-Object {{$_.DeviceID -eq (Get-Partition -DriveLetter {clean_letter}).DiskNumber}} | Select-Object -ExpandProperty MediaType"'
            media_type = subprocess.check_output(cmd, shell=True).decode('utf-8').strip()
            if media_type:
                print(f"Type de stockage   : {media_type}")
    except Exception as e:
        print(f"Erreur d'inspection : {e}")

def inspect_process(target):
    print(f"\n--- RECHERCHE DU PROCESSUS : {target} ---")
    if target.isdigit():
        try:
            p = psutil.Process(int(target))
            print(f"Nom : {p.name()} | PID : {p.pid} | Statut : {p.status()}")
            print(f"RAM : {get_size(p.memory_info().rss)} | CPU : {p.cpu_percent(interval=0.1)}%")
            return
        except psutil.NoSuchProcess:
            print("PID introuvable.")
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
        print("Aucun processus trouvé.")
        return
    print(f"Instances : {len(matching_processes)} | RAM totale : {get_size(total_memory)}")

def clean_system():
    if platform.system() != "Windows":
        print("La fonction de nettoyage est optimisée uniquement pour Windows.")
        return

    print("\n--- DOSSIERS TEMPORAIRES (NETTOYAGE) ---")
    confirm = input("Voulez-vous lancer le nettoyage des fichiers temporaires ? (o/n) : ").strip().lower()
    if confirm != 'o':
        print("Nettoyage annulé.")
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
        print(f"\nNettoyage de : {path}")
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

    print(f"\n[Succès] Nettoyage terminé.")
    print(f"-> Éléments supprimés : {files_deleted}")
    print(f"-> Espace disque récupéré : {get_size(bytes_saved)}")

def optimize_system():
    if platform.system() != "Windows":
        print("L'optimisation des processus est conçue pour Windows.")
        return

    print("\n--- OPTIMISATION DES PROCESSUS ---")
    print("Cette commande va fermer les services de télémétrie, de rapports d'erreurs et de tracking superflus.")
    confirm = input("Voulez-vous continuer ? (o/n) : ").strip().lower()
    if confirm != 'o':
        print("Optimisation annulée.")
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
                print(f"  [X] Tuable identifié et fermé : {p_name} (PID: {proc.info['pid']})")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    if killed_count == 0:
        print("\nAucun processus superflu détecté ou actif en ce moment. Votre système est déjà propre !")
    else:
        print(f"\n[Succès] Optimisation terminée.")
        print(f"-> Processus arrêtés : {killed_count}")
        print(f"-> Mémoire vive immédiatement libérée : {get_size(ram_freed)}")

def export_report():
    folder_name = "Rapports"
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
        
    now = datetime.now()
    date_texte = now.strftime("%d/%m/%Y à %H:%M:%S")
    filename = now.strftime("%d-%m-%Y_%HHh%Mm%SSs.txt")
    filepath = os.path.join(folder_name, filename)
    
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("=========================================\n")
            f.write("      RAPPORT MATÉRIEL ET SYSTÈME        \n")
            f.write(f"      Généré le : {date_texte}       \n")
            f.write("=========================================\n\n")
            # Injection de TOUS les modules sans aucune omission
            f.write(get_os_info() + "\n")
            f.write(get_cpu_info() + "\n")
            f.write(get_gpu_info() + "\n")
            f.write(get_ram_info() + "\n")
            f.write(get_disk_info() + "\n")
            f.write(get_net_info() + "\n")
        print(f"\n[Succès] Rapport complet sauvegardé dans : {os.path.abspath(filepath)}")
    except Exception as e:
        print(f"\n[Erreur] Échec de l'export : {e}")

def show_help():
    print("\nCommandes disponibles :")
    print("  os      : Informations du système d'exploitation")
    print("  cpu     : Détails complets du processeur (Fréquences & cœurs)")
    print("  gpu     : Modèles de puces graphiques et versions de pilotes")
    print("  ram     : État, tailles et occupation de la mémoire vive")
    print("  disk    : Liste exhaustive des partitions (Points de montage & types)")
    print("  inspect : Inspecte un lecteur cible en profondeur (ex: C:)")
    print("  proc    : Analyse un processus/logiciel par NOM ou PID")
    print("  clean   : [ADMIN] Nettoie les fichiers et caches temporaires")
    print("  optimize: [ADMIN] Ferme les processus d'arrière-plan superflus")
    print("  net     : Cartes réseaux, masques de sous-réseau et IPs actives")
    print("  all     : Affiche l'ensemble complet des modules à l'écran")
    print("  export  : Crée un rapport global daté dans le dossier 'Rapports'")
    print("  clear   : Nettoie l'écran de la console")
    print("  help    : Affiche ce menu d'aide")
    print("  exit    : Ferme le programme\n")

def main():
    status = " (Mode Administrateur)" if is_admin() else ""
    print(f"Moniteur & Inspecteur Système v4.3{status}")
    print("Entrez 'help' pour démarrer.")
    
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
                cible = input("Lettre du lecteur à inspecter (ex: C) : ").strip()
                if cible:
                    inspect_drive(cible)
            elif choix == 'proc':
                cible = input("Nom du programme ou PID à analyser : ").strip().lower()
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
                print("Fermeture de l'application.")
                break
            elif choix == "":
                continue
            else:
                print("Commande inconnue. Utilisez 'help'.")
                
        except KeyboardInterrupt:
            print("\nSortie du programme.")
            break

if __name__ == "__main__":
    main()
