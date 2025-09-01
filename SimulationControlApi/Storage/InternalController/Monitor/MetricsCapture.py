from typing import Dict, Any, Optional
import re
from datetime import datetime
import json
from pathlib import Path

class MetricsCapture:
    """Captura y parsea las métricas de entrenamiento de SB3"""
    
    def __init__(self, jsonl_file_path: Path):
        self.__jsonl_file_path = jsonl_file_path
        self.__buffer = ""
        self.__in_metrics_block = False

    def process_output_line(self, line: str):
        """Procesa cada línea de salida buscando bloques de métricas"""
        # Detectar inicio de bloque de métricas
        if "rollout/" in line:
            self.__in_metrics_block = True
            self.__buffer = line + "\n"
        elif self.__in_metrics_block:
            self.__buffer += line + "\n"
            
            # Detectar fin de bloque (línea de guiones)
            if line.strip().startswith("--") and line.strip().endswith("--"):
                metrics = self.parse_metrics_block(self.__buffer)
                if metrics:
                    self.save_metrics_to_jsonl(metrics)
                
                # Resetear estado
                self.__in_metrics_block = False
                self.__buffer = ""        

    def parse_metrics_block(self, block_text: str) -> Optional[Dict[str, Any]]:
        """Parsea el bloque de métricas y extrae los valores"""
        try:
            metrics = {}
            timestamp = datetime.now().isoformat()
            
            # Patrones para extraer métricas
            patterns = {
                'ep_len_mean': r'ep_len_mean\s*\|\s*([\d.-]+)',
                'ep_rew_mean': r'ep_rew_mean\s*\|\s*([-\d.]+)',
                'exploration_rate': r'exploration_rate\s*\|\s*([\d.-]+)',
                'episodes': r'episodes\s*\|\s*(\d+)',
                'fps': r'fps\s*\|\s*([\d.-]+)',
                'time_elapsed': r'time_elapsed\s*\|\s*(\d+)',
                'total_timesteps': r'total_timesteps\s*\|\s*(\d+)'
            }
            
            for key, pattern in patterns.items():
                match = re.search(pattern, block_text)
                if match:
                    value = match.group(1)
                    # Convertir a número si es posible
                    try:
                        if '.' in value:
                            metrics[key] = float(value)
                        else:
                            metrics[key] = int(value)
                    except ValueError:
                        metrics[key] = value
            
            if metrics:
                metrics['timestamp'] = timestamp
                return metrics
                
        except Exception as e:
            print(f"Error al parsear métricas: {e}")
            
        return None
    
    def save_metrics_to_jsonl(self, metrics: Dict[str, Any]):
        """Guarda las métricas en formato JSONL"""
        try:
            with open(self.__jsonl_file_path, 'a', encoding='utf-8') as f:
                json.dump(metrics, f, separators=(',', ':'))
                f.write('\n')
                f.flush()  # Asegurar escritura inmediata
                
            print(f"Métricas guardadas: {metrics['timestamp']} - Episodio: {metrics.get('episodes', 'N/A')}")
            
        except Exception as e:
            print(f"Error al guardar métricas: {e}")
