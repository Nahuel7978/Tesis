import os

def createInternalController(
        path: str,
        model: str,
        verbose: int,
        learning_rate: float,
        buffer_size: int,
        learning_starts: int,
        batch_size: int,
        gamma: float,
        train_freq: int,
        target_update_interval: int,
        exploration_fraction: float,
        exploration_final_eps: float
    ) -> str:
        """
        Creates a folder 'internalTrainingController' and a Python file 'internalTrainingController.py'
        with a trainAgent method based on the specified model and parameters.
        
        :param path: Base path where the internalTrainingController folder will be created.
        :param model: The RL model to use (e.g., 'DQN').
        :param verbose: Verbosity level for the model.
        :param learning_rate: Learning rate for the model.
        :param buffer_size: Size of the replay buffer.
        :param learning_starts: Steps before learning starts.
        :param batch_size: Batch size for training.
        :param gamma: Discount factor.
        :param train_freq: Frequency of training.
        :param target_update_interval: Frequency of target network updates.
        :param exploration_fraction: Fraction of total timesteps for exploration.
        :param exploration_final_eps: Final epsilon for exploration.
        :return: Full path to the created Python file.
        """
        # Define the folder and file paths
        controller_dir = os.path.join(path, "internalTrainingController")
        controller_file = os.path.join(controller_dir, "internalTrainingController.py")
        
        # Create the folder if it doesn't exist
        os.makedirs(controller_dir, exist_ok=True)
        
        # Define the imports and base structure
        file_content = """import numpy as np
from stable_baselines3 import DQN
from webots_controller import WebotsController

class InternalTrainingController(WebotsController):
    def __init__(self):
        super().__init__()
        
    def trainAgent(self):
"""
        
        # Add model-specific code (e.g., for DQN)
        if model.upper() == "DQN":
            file_content += f"""        model = DQN(
            "MlpPolicy",
            self.env,
            verbose={verbose},
            learning_rate={learning_rate},
            buffer_size={buffer_size},
            learning_starts={learning_starts},
            batch_size={batch_size},
            gamma={gamma},
            train_freq={train_freq},
            target_update_interval={target_update_interval},
            exploration_fraction={exploration_fraction},
            exploration_final_eps={exploration_final_eps}
        )
        model.learn(total_timesteps=100000)
        model.save("dqn_webots_model")
"""
        else:
            # Fallback for unsupported models (extendable for other models like PPO)
            file_content += """        # Placeholder for other models
        pass
"""
        
        # Write the content to the Python file
        with open(controller_file, 'w') as f:
            f.write(file_content)
        
        return controller_file