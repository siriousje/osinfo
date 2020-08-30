#!/usr/bin/python3
# -*- coding: utf-8 -*-

import influx
import datetime
import psutil
import socket
import json
import collections

hostname = socket.gethostname()
timestamp = str(datetime.datetime.now(datetime.timezone.utc).isoformat())

Times = collections.namedtuple('Times', 'system user nice idle')

def send_data_to_influx(payload):
    influx.write_to_influxdb(payload)

def create_cpu_payload(cpu, times):
    global hostname, timestamp
    
    return {
        'measurement': 'cpu_info',
        'time': timestamp,
        'tags': {
            'host': hostname,
            'cpu': cpu
        },
        'fields': {
            'cpu': round(100.0 - times.idle, 1),
            'system': times.system,
            'user': times.user,
            'idle': times.idle,
            'nice': times.nice
        }
    }

def dumps(s):
    print(json.dumps(s, indent=4))

def cpu_info():
    payload = []
    
    times = psutil.cpu_times_percent(percpu=True, interval=1)
    system, user, nice, idle = 0.0, 0.0, 0.0, 0.0
    
    for i, cpu in enumerate(times):
        system += cpu.system
        user += cpu.user
        nice += cpu.nice
        idle += cpu.idle
        payload.append(create_cpu_payload(f"core{i}", cpu))

    num_cpu = float(len(times))
    averages = Times(round(system/num_cpu, 1), round(user/num_cpu, 1), round(nice/num_cpu, 1), round(idle/num_cpu, 1))
    payload.append(create_cpu_payload('cpu', averages))    

    send_data_to_influx(payload)

def memory_info():
    global hostname, timestamp
    memory = psutil.virtual_memory()
    payload = [{
        'measurement': 'memory_info',
        'time': timestamp,
        'tags': {
            'host': hostname
        },
        'fields': {
            'total': memory.total,
            'available': memory.available,
            'percent': memory.percent,
            'used': memory.used,
            'free': memory.free,
            'active': memory.active,
            'inactive': memory.inactive
        }
    }]
    send_data_to_influx(payload)

def swap_info():
    global hostname, timestamp
    memory = psutil.swap_memory()
    payload = [{
        'measurement': 'swap_info',
        'time': timestamp,
        'tags': {
            'host': hostname
        },
        'fields': {
            'total': memory.total,
            'percent': memory.percent,
            'used': memory.used,
            'free': memory.free
        }
    }]
    send_data_to_influx(payload)

def disk_info():
    global hostname, timestamp
    payload = []
    disks = psutil.disk_partitions(all=False)
    for disk in disks:
        usage = psutil.disk_usage(disk.mountpoint)
        payload.append({
            'measurement': 'disk_info',
            'time': timestamp, 
            'tags': {
                'host': hostname,
                'disk': disk.device
            },
            'fields': {
                'device': disk.device,
                'mountpoint': disk.mountpoint,
                'fstype': disk.fstype,
                'total': usage.total,
                'used': usage.used,
                'free': usage.free,
                'percent': usage.percent
            }
        })
        send_data_to_influx(payload)

def network_info():
    payload = []
    network = psutil.net_io_counters(pernic=True,nowrap=False)
    for iface, nic in network.items():
        payload.append({
            'measurement': 'network_info',
            'time': timestamp, 
            'tags': {
                'host': hostname,
                'interface': iface
            },
            'fields': {
                'bytes_sent': nic.bytes_sent,
                'bytes_recv': nic.bytes_recv,
                'packets_sent': nic.packets_sent,
                'packets_recv': nic.packets_recv,
                'errin': nic.errin,
                'errout': nic.errout,
                'dropin': nic.dropin,
                'dropout': nic.dropout
            }
        })
    send_data_to_influx(payload)


def main():
    cpu_info()
    memory_info()
    swap_info()
    disk_info()
    network_info()

if __name__ == '__main__':
    main()