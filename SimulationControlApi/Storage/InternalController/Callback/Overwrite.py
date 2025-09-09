from stable_baselines3.common.callbacks import CheckpointCallback, EvalCallback, BaseCallback
import os
from pathlib import Path


class OverwriteCheckpointCallback(CheckpointCallback):
    """
    CheckpointCallback personalizado que siempre guarda con el mismo nombre,
    sobrescribiendo el archivo anterior.
    """
    
    def __init__(self, save_freq, save_path, name_prefix="model_checkpoint"):
        super().__init__(
            save_freq=save_freq,
            save_path=save_path,
            name_prefix=name_prefix
        )
        
        self.fixed_filename = f"{name_prefix}_latest"
    
    def _on_step(self) -> bool:
        """
        Sobrescribe el método para usar nombre fijo
        """
        if self.n_calls % self.save_freq == 0:
            model_path = os.path.join(self.save_path, self.fixed_filename)
            
            self.model.save(model_path)
        
        
        return True