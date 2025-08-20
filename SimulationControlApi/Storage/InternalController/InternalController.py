# /workspace/project/controllers/trainer_controller/trainer_controller.py

import os, sys, json, traceback, importlib
from pathlib import Path

# Opcional: añade /workspace al sys.path para "user_code.*"
WS = Path("/workspace")
sys.path.insert(0, str(WS))

# Lee controllerArgs (si las pasaste). En Python de Webots podés
# leer args desde el propio env; si no, usa ruta fija por convención:
CONFIG_PATH = os.environ.get("CONFIG_PATH", "/workspace/config/train_config.json")

# Logging básico a archivo
LOG_DIR = WS / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
log_file = open(LOG_DIR / "train.log", "a", buffering=1)

def log(*args):
    print(*args, file=log_file, flush=True)
    print(*args, flush=True)

def load_cfg():
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)

def make_env(cfg):
    module_name = cfg["env_module"]      # "user_code.env"
    class_name  = cfg["env_class"]       # "HROSbotEnvironment"
    mod = importlib.import_module(module_name)
    EnvClass = getattr(mod, class_name)
    return EnvClass()

def make_model(cfg, env):
    from stable_baselines3 import PPO, DQN, A2C, SAC, TD3
    model_map = {
        "PPO": PPO, "DQN": DQN, "A2C": A2C, "SAC": SAC, "TD3": TD3
    }
    Model = model_map[cfg["algo"]]
    policy = cfg.get("policy", "MlpPolicy")
    params = cfg.get("algo_params", {})
    return Model(policy, env, verbose=1, **params)

def main():
    try:
        cfg = load_cfg()
        log("[trainer] cfg:", cfg)

        # Semillas, si querés reproducibilidad:
        """
        seed = cfg.get("seed")
        if seed is not None:
            import numpy as np, random, torch
            random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)
        """

        # Instancia env del usuario
        env = make_env(cfg)

        # Wrapper de seguridad opcional (timeouts, stuck, etc.)
        # from timeout_wrapper import TimeoutWrapper
        # env = TimeoutWrapper(env, timeout_seconds=15)

        # Crea modelo y entrena
        model = make_model(cfg, env)
        timesteps = int(cfg["timesteps"])
        model.learn(total_timesteps=timesteps)

        # Guarda modelo entrenado
        ART = WS / "trained_model"
        ART.mkdir(parents=True, exist_ok=True)
        model_path = ART / "model.zip"
        model.save(str(model_path))
        log(f"[trainer] modelo guardado en {model_path}")

    except Exception as e:
        log("[trainer][ERROR]", e)
        log(traceback.format_exc())
        env.close()
        sys.exit(1)
    finally:
        try:
            log_file.close()
            env.close()
            sys.exit(1)
        except:
            env.close()
            sys.exit(1)

if __name__ == "__main__":
    main()
