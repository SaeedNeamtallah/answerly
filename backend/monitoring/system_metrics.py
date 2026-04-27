"""
System Resource Monitoring
CPU - RAM - Disk usage metrics
"""

import psutil
from prometheus_client import Gauge

# ------------------------
# Metrics
# ------------------------

CPU_USAGE = Gauge(
    "system_cpu_usage_percent",
    "CPU usage percentage"
)

RAM_USAGE = Gauge(
    "system_ram_usage_percent",
    "RAM usage percentage"
)

DISK_USAGE = Gauge(
    "system_disk_usage_percent",
    "Disk usage percentage"
)


# ------------------------
# Update Function
# ------------------------

async def update_system_metrics():
    cpu_percent = psutil.cpu_percent(interval=0.5)
    CPU_USAGE.set(cpu_percent)

    ram = psutil.virtual_memory()
    RAM_USAGE.set(ram.percent)

    disk = psutil.disk_usage("C:\\")  # لو Linux خليه "/"
    DISK_USAGE.set(disk.percent)