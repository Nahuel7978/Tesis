#!/usr/bin/env python3
"""
Monitor de recursos para simulación Webots + Deepbots + Stable Baselines3
Monitorea CPU, RAM, GPU y procesos relacionados durante el entrenamiento
"""

import psutil
import time
import datetime
import threading
import os
import sys
from collections import defaultdict
import json

class ResourceMonitor:
    def __init__(self, output_file="resource_monitor.txt", monitoring_interval=1.0):
        self.output_file = output_file
        self.monitoring_interval = monitoring_interval
        self.monitoring = False
        self.monitor_thread = None
        self.data_log = []
        
        # Palabras clave para identificar procesos relacionados con la simulación
        self.simulation_keywords = [
            # Webots específicos
            'webots', 'webots-bin', 'webots-bin.real', 'webots++', 'webots-b:gdrv0', 'elisa3',
            
            # Python y entrenamiento
            'python', 'python3', 'python3.10', 'python3.11', 'python3.12',
            'deepbots', 'pytorch', 'tensorflow', 'stable-baselines3',
            
            # Bibliotecas numéricas y BLAS
            'blas', 'openblas', 'mkl', 'mkl-service', 'numexpr', 'numpy',
            'libtorch', 'torch', 'libblas', 'libopenblas', 'libmkl',
            
            # GPU y CUDA
            'cuda', 'nvidia', 'gpu', 'nvidia-smi', 'nvidia-ml-py',
            'cudnn', 'cublas', 'curand', 'cusparse',
            
            # Renderizado y gráficos (pueden ser intensivos en Webots)
            'qt', 'qt5', 'qt6', 'qtwebengine', 'qtquick', 'qml',
            'opengl', 'mesa', 'glx', 'dri', 'gallium',
            'x11', 'xorg', 'wayland',
            
            # Multiprocessing y paralelización
            'multiprocessing', 'joblib', 'threadpoolctl',
            
            # Términos del proyecto
            'simulation', 'robot', 'tesis', 'autonomous', 'dqn', 'gym', 'gymnasium'
        ]
        
        # Inicializar archivo de salida
        self.init_output_file()
    
    def init_output_file(self):
        """Inicializa el archivo de salida con headers"""
        with open(self.output_file, 'w') as f:
            f.write("="*80 + "\n")
            f.write("MONITOR DE RECURSOS - WEBOTS + DEEPBOTS + STABLE BASELINES3\n")
            f.write(f"Inicio del monitoreo: {datetime.datetime.now()}\n")
            f.write("="*80 + "\n\n")
    
    def get_system_info(self):
        """Obtiene información general del sistema"""
        info = {
            'cpu_count': psutil.cpu_count(logical=False),
            'cpu_count_logical': psutil.cpu_count(logical=True),
            'memory_total_gb': round(psutil.virtual_memory().total / (1024**3), 2),
            'disk_usage': psutil.disk_usage('/').percent if os.name != 'nt' else psutil.disk_usage('C:\\').percent
        }
        
        # Información de GPU si está disponible
        try:
            import GPUtil
            gpus = GPUtil.getGPUs()
            if gpus:
                info['gpu_count'] = len(gpus)
                info['gpu_names'] = [gpu.name for gpu in gpus]
        except ImportError:
            info['gpu_info'] = "GPUtil no disponible - instalar con: pip install GPUtil"
        
        return info
    
    def get_simulation_processes(self):
        """Identifica todos los procesos relacionados con la simulación"""
        simulation_processes = []
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'memory_percent', 'memory_info', 'exe', 'cwd']):
            try:
                proc_info = proc.info
                proc_name = proc_info['name'].lower()
                proc_cmdline = ' '.join(proc_info['cmdline'] or []).lower()
                proc_exe = (proc_info['exe'] or '').lower()
                proc_cwd = (proc_info['cwd'] or '').lower()
                
                # Verificar si el proceso está relacionado con la simulación
                is_simulation_process = False
                match_reason = ""
                
                # 1. Verificar por nombre del proceso
                for keyword in self.simulation_keywords:
                    if keyword in proc_name:
                        is_simulation_process = True
                        match_reason = f"name:{keyword}"
                        break
                
                # 2. Verificar por línea de comandos
                if not is_simulation_process:
                    for keyword in self.simulation_keywords:
                        if keyword in proc_cmdline:
                            is_simulation_process = True
                            match_reason = f"cmdline:{keyword}"
                            break
                
                # 3. Verificar por ejecutable
                if not is_simulation_process and proc_exe:
                    for keyword in self.simulation_keywords:
                        if keyword in proc_exe:
                            is_simulation_process = True
                            match_reason = f"exe:{keyword}"
                            break
                
                # 4. Verificar procesos específicos de Webots (más riguroso)
                if not is_simulation_process:
                    webots_indicators = ['webots', '/opt/webots', 'wbt', 'proto']
                    if any(indicator in proc_cmdline or indicator in proc_exe or indicator in proc_cwd 
                        for indicator in webots_indicators):
                        is_simulation_process = True
                        match_reason = "webots_specific"
                
                # 5. Verificar procesos Python con argumentos relacionados al proyecto
                if not is_simulation_process and 'python' in proc_name:
                    project_terms = ['deepbots', 'stable', 'gym', 'robot', 'elisa3', 'tesis', 
                                'autonomous', 'simulation', 'train', 'dqn', 'rl']
                    if any(term in proc_cmdline or term in proc_cwd for term in project_terms):
                        is_simulation_process = True
                        match_reason = "python_project"
                
                # 6. Verificar procesos hijos de procesos ya identificados
                if not is_simulation_process:
                    try:
                        parent = proc.parent()
                        if parent and any(keyword in parent.name().lower() 
                                        for keyword in ['webots', 'python']):
                            # Verificar si el padre parece ser del proyecto
                            parent_cmdline = ' '.join(parent.cmdline() or []).lower()
                            if any(term in parent_cmdline for term in ['webots', 'deepbots', 'simulation']):
                                is_simulation_process = True
                                match_reason = f"child_of:{parent.name()}"
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                
                # 7. Verificar bibliotecas numéricas intensivas (solo si consumen mucho CPU)
                if not is_simulation_process:
                    try:
                        logical_cores = psutil.cpu_count()
                        cpu_percent = proc.cpu_percent(interval=0.1)/logical_cores
                        if cpu_percent > 5.0:  # Solo considerar si usa >5% CPU
                            intensive_libs = ['blas', 'mkl', 'openblas', 'numexpr', 'torch']
                            if any(lib in proc_name or lib in proc_exe for lib in intensive_libs):
                                is_simulation_process = True
                                match_reason = f"intensive_lib:cpu_{cpu_percent:.1f}%"
                    except:
                        pass
                
                if is_simulation_process:
                    # Obtener información detallada del proceso
                    try:
                        memory_info = proc.memory_info()
                        
                        # Calcular CPU correctamente
                        logical_cores = psutil.cpu_count()
                        cpu_percent = proc.cpu_percent(interval=0.1)/ logical_cores
                        
                        simulation_processes.append({
                            'pid': proc_info['pid'],
                            'name': proc_info['name'],
                            'cmdline': ' '.join(proc_info['cmdline'] or [])[:100] + '...' if len(' '.join(proc_info['cmdline'] or [])) > 100 else ' '.join(proc_info['cmdline'] or []),
                            'cpu_percent': round(cpu_percent, 2),
                            'memory_percent': proc.memory_percent(),
                            'memory_mb': round(memory_info.rss / (1024*1024), 2),
                            'status': proc.status(),
                            'match_reason': match_reason,  # Para debugging
                            'exe': proc_exe[:50] + '...' if len(proc_exe) > 50 else proc_exe,
                            'cwd': proc_cwd[:50] + '...' if len(proc_cwd) > 50 else proc_cwd
                        })
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                            
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        
        return simulation_processes
    
    def get_gpu_info(self):
        """Obtiene información de GPU si está disponible"""
        gpu_info = {}
        try:
            import GPUtil
            gpus = GPUtil.getGPUs()
            for i, gpu in enumerate(gpus):
                gpu_info[f'gpu_{i}'] = {
                    'name': gpu.name,
                    'load_percent': round(gpu.load * 100, 2),
                    'memory_used_mb': round(gpu.memoryUsed, 2),
                    'memory_total_mb': round(gpu.memoryTotal, 2),
                    'memory_percent': round((gpu.memoryUsed / gpu.memoryTotal) * 100, 2),
                    'temperature': gpu.temperature
                }
        except ImportError:
            gpu_info['error'] = "GPUtil no instalado"
        except Exception as e:
            gpu_info['error'] = f"Error obteniendo info GPU: {str(e)}"
        
        return gpu_info
    
    def monitor_resources(self):
        """Función principal de monitoreo que se ejecuta en un hilo separado"""
        start_time = time.time()
        
        while self.monitoring:
            try:
                timestamp = datetime.datetime.now()
                elapsed_time = time.time() - start_time
                
                # Obtener información del sistema
                cpu_percent = psutil.cpu_percent(interval=0.1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/') if os.name != 'nt' else psutil.disk_usage('C:\\')
                
                # Obtener procesos de simulación
                sim_processes = self.get_simulation_processes()
                
                # Obtener información de GPU
                gpu_info = self.get_gpu_info()
                
                # Calcular totales de procesos de simulación
                total_sim_cpu = sum(proc['cpu_percent'] for proc in sim_processes)
                total_sim_memory_mb = sum(proc['memory_mb'] for proc in sim_processes)
                total_sim_memory_percent = sum(proc['memory_percent'] for proc in sim_processes)
                
                # Crear registro de datos
                data_point = {
                    'timestamp': timestamp.isoformat(),
                    'elapsed_seconds': round(elapsed_time, 2),
                    'system': {
                        'cpu_percent': cpu_percent,
                        'memory_percent': memory.percent,
                        'memory_used_gb': round(memory.used / (1024**3), 2),
                        'memory_available_gb': round(memory.available / (1024**3), 2),
                        'disk_percent': disk.percent
                    },
                    'simulation': {
                        'process_count': len(sim_processes),
                        'total_cpu_percent': round(total_sim_cpu, 2),
                        'total_memory_mb': round(total_sim_memory_mb, 2),
                        'total_memory_percent': round(total_sim_memory_percent, 2)
                    },
                    'processes': sim_processes,
                    'gpu': gpu_info
                }
                
                # Guardar datos
                self.data_log.append(data_point)
                
                # Escribir al archivo
                self.write_data_point(data_point)
                
                time.sleep(self.monitoring_interval)
                
            except Exception as e:
                print(f"Error en monitoreo: {e}")
                time.sleep(self.monitoring_interval)
    
    def write_data_point(self, data_point):
        """Escribe un punto de datos al archivo"""
        with open(self.output_file, 'a') as f:
            f.write(f"\n[{data_point['timestamp']}] Tiempo transcurrido: {data_point['elapsed_seconds']}s\n")
            f.write("-" * 60 + "\n")
            
            # Sistema general
            sys_data = data_point['system']
            f.write(f"SISTEMA GENERAL:\n")
            f.write(f"  CPU: {sys_data['cpu_percent']:.2f}%\n")
            f.write(f"  RAM: {sys_data['memory_percent']:.2f}% ({sys_data['memory_used_gb']:.2f}GB usados)\n")
            f.write(f"  Disco: {sys_data['disk_percent']:.2f}%\n\n")
            
            # Procesos de simulación
            sim_data = data_point['simulation']
            f.write(f"PROCESOS DE SIMULACIÓN ({sim_data['process_count']} procesos):\n")
            f.write(f"  CPU Total: {sim_data['total_cpu_percent']:.2f}%\n")
            f.write(f"  RAM Total: {sim_data['total_memory_percent']:.2f}% ({sim_data['total_memory_mb']:.2f}MB)\n\n")
            
            # Detalle de procesos
            if data_point['processes']:
                f.write("DETALLE DE PROCESOS:\n")
                # Ordenar por CPU descendente para mostrar los más activos primero
                processes_sorted = sorted(data_point['processes'], key=lambda x: x['cpu_percent'], reverse=True)
                
                for proc in processes_sorted[:10]:  # Mostrar solo top 10
                    f.write(f"  PID {proc['pid']}: {proc['name']} (Status: {proc['status']}) [{proc['match_reason']}]\n")
                    f.write(f"    CPU: {proc['cpu_percent']:.2f}%, RAM: {proc['memory_percent']:.2f}% ({proc['memory_mb']:.2f}MB)\n")
                    f.write(f"    EXE: {proc['exe']}\n")
                    f.write(f"    CMD: {proc['cmdline']}\n")
                    if proc['cwd']:
                        f.write(f"    CWD: {proc['cwd']}\n")
                
                # Mostrar top 5 por categoría
                if len(processes_sorted) > 5:
                    f.write(f"\n  TOP 5 POR CPU:\n")
                    for i, proc in enumerate(processes_sorted[:5], 1):
                        f.write(f"    {i}. {proc['name']} (PID {proc['pid']}): {proc['cpu_percent']:.2f}% CPU [{proc['match_reason']}]\n")
                        
                f.write("\n")
                # GPU si está disponible
                if data_point['gpu'] and 'error' not in data_point['gpu']:
                    f.write("GPU:\n")
                    for gpu_id, gpu_data in data_point['gpu'].items():
                        f.write(f"  {gpu_data['name']}:\n")
                        f.write(f"    Uso: {gpu_data['load_percent']:.2f}%\n")
                        f.write(f"    VRAM: {gpu_data['memory_percent']:.2f}% ({gpu_data['memory_used_mb']:.2f}MB)\n")
                        f.write(f"    Temperatura: {gpu_data['temperature']}°C\n")
                    f.write("\n")
                
                f.write("=" * 60 + "\n")
    
    def start_monitoring(self):
        """Inicia el monitoreo en un hilo separado"""
        if not self.monitoring:
            self.monitoring = True
            
            # Escribir información del sistema
            system_info = self.get_system_info()
            with open(self.output_file, 'a') as f:
                f.write("INFORMACIÓN DEL SISTEMA:\n")
                f.write(f"  CPUs físicos: {system_info['cpu_count']}\n")
                f.write(f"  CPUs lógicos: {system_info['cpu_count_logical']}\n")
                f.write(f"  RAM Total: {system_info['memory_total_gb']} GB\n")
                if 'gpu_names' in system_info:
                    f.write(f"  GPUs: {', '.join(system_info['gpu_names'])}\n")
                f.write("\n" + "="*80 + "\n")
            
            self.monitor_thread = threading.Thread(target=self.monitor_resources)
            self.monitor_thread.daemon = True
            self.monitor_thread.start()
            print(f"Monitoreo iniciado. Guardando en: {self.output_file}")
    
    def stop_monitoring(self):
        """Detiene el monitoreo"""
        if self.monitoring:
            self.monitoring = False
            if self.monitor_thread:
                self.monitor_thread.join()
            
            # Escribir resumen final
            self.write_summary()
            print("Monitoreo detenido.")
    
    def write_summary(self):
        """Escribe un resumen al final del archivo"""
        if not self.data_log:
            return
        
        with open(self.output_file, 'a') as f:
            f.write("\n" + "="*80 + "\n")
            f.write("RESUMEN FINAL DEL MONITOREO\n")
            f.write(f"Fin del monitoreo: {datetime.datetime.now()}\n")
            f.write("="*80 + "\n")
            
            # Calcular estadísticas
            cpu_values = [dp['system']['cpu_percent'] for dp in self.data_log]
            memory_values = [dp['system']['memory_percent'] for dp in self.data_log]
            sim_cpu_values = [dp['simulation']['total_cpu_percent'] for dp in self.data_log]
            sim_memory_values = [dp['simulation']['total_memory_percent'] for dp in self.data_log]
            
            f.write(f"Duración total: {self.data_log[-1]['elapsed_seconds']:.2f} segundos\n")
            f.write(f"Puntos de datos recolectados: {len(self.data_log)}\n\n")
            
            f.write("ESTADÍSTICAS DEL SISTEMA:\n")
            f.write(f"  CPU - Promedio: {sum(cpu_values)/len(cpu_values):.2f}%, Máximo: {max(cpu_values):.2f}%\n")
            f.write(f"  RAM - Promedio: {sum(memory_values)/len(memory_values):.2f}%, Máximo: {max(memory_values):.2f}%\n\n")
            
            f.write("ESTADÍSTICAS DE SIMULACIÓN:\n")
            f.write(f"  CPU - Promedio: {sum(sim_cpu_values)/len(sim_cpu_values):.2f}%, Máximo: {max(sim_cpu_values):.2f}%\n")
            f.write(f"  RAM - Promedio: {sum(sim_memory_values)/len(sim_memory_values):.2f}%, Máximo: {max(sim_memory_values):.2f}%\n")


def main():
    """Función principal para usar el monitor de forma independiente"""
    print("Monitor de Recursos - Webots + Deepbots + Stable Baselines3")
    print("Presiona Ctrl+C para detener el monitoreo")
    
    monitor = ResourceMonitor()
    
    try:
        monitor.start_monitoring()
        
        # Mantener el programa corriendo
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nDeteniendo monitoreo...")
        monitor.stop_monitoring()


if __name__ == "__main__":
    main()