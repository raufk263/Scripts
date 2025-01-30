import platform
import psutil
import shutil
import datetime
def get_system_info():
    return {
        'System': platform.system(),           # Get system name
        'Node Name':platform.node(),          # Get the node name (hostname)
        'Version': platform.version(),         # Get OS version
        'Machine': platform.machine(),         # Get machine type
        'Processor': platform.processor(),     # Get processor info
    }
print("SYSTEM REPORT")
print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
print("------------------------------------------")
# Get the system info and print it
print("System Details---")
system_info = get_system_info()
for key, value in system_info.items():
    print(f"{key}: {value}")

#Get CPU usage of system
print("\nCPU utilization of System---")

def get_cpu_usage():
    cpu_usage = psutil.cpu_percent(interval=1)
    print(f"CPU Usage: {cpu_usage}%")

get_cpu_usage()

# Get Disk Usage of System
print("\nDisk usage of System---")
def get_disk_usage():
    disk = shutil.disk_usage('/')
    return {
        'Total Disk Space': f'{disk.total / (1024**3):.2f} GB',
        'Used Disk Space': f'{disk.used / (1024**3):.2f} GB',
        'Free Disk Space': f'{disk.free / (1024**3):.2f} GB',
        'Disk Usage': f'{(disk.used / disk.total) * 100:.2f}%',
    }

disk_info = get_disk_usage()
for key, value in disk_info.items():
    print(f"{key}: {value}")

# Get memory details of System
print("\nMemory Usage of System---")
def get_memory_usage():
    mem = psutil.virtual_memory()
    return {
        'Total Memory': f'{mem.total / (1024**3):.2f} GB',
        'Used Memory': f'{mem.used / (1024**3):.2f} GB',
        'Available Memory': f'{mem.available / (1024**3):.2f} GB',
        'Memory Usage': f'{mem.percent}%',
        'Free Memory' : f'{mem.free/ (1024**2):.2f} MB'
    }

mem_info = get_memory_usage()
for key, value in mem_info.items():
    print(f"{key}: {value}")
