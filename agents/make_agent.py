from stable_baselines3.a2c import A2C
from stable_baselines3.ppo import PPO
from stable_baselines3.ddpg import DDPG
from stable_baselines3.td3 import TD3
from stable_baselines3.sac import SAC
from stable_baselines3.her import HER
from .sb3_on_policy_train import SB3OnPolicyTrainer,SB3OffPolicyTrainer,SB3HerPolicyTrainer
from .rainbow_trainer import RainbowTrainer
import gym
from .sb3_extended_algos import ExtA2C, ExtPPO, ExtSAC


SB3_ON_ALGOS = {
    "A2C": ExtA2C,
    "PPO": ExtPPO,
}
SB3_OFF_ALGOS = {
    "DDPG": DDPG,
    "TD3": TD3,
    "SAC": ExtSAC,
}

def make_agent(agent_name, env_name, device, hyperparams):
    if 'rainbow' == agent_name:
        return RainbowTrainer(env_name,device=device,**hyperparams)
    elif "SB3_OFF" == agent_name:
        env_fn = lambda: gym.make(env_name)
        env = env_fn()
        algo = SB3_OFF_ALGOS[hyperparams.pop('ALGO')]
        model = "MlpPolicy" if len(env.observation_space.shape) != 3 else "CnnPolicy"
        return SB3OffPolicyTrainer(env_fn,algo(model,env,device=device,**hyperparams))
    elif "SB3_ON" == agent_name:
        env_fn = lambda: gym.make(env_name)
        env = env_fn()
        algo = SB3_ON_ALGOS[hyperparams.pop('ALGO')]
        model = "MlpPolicy" if len(env.observation_space.shape) != 3 else "CnnPolicy"
        return SB3OnPolicyTrainer(env_fn,algo(model,env,device=device,**hyperparams))
    elif "SB3_HER" == agent_name:
        env_fn = lambda: gym.make(env_name)
        algo = SB3_OFF_ALGOS[hyperparams.pop('ALGO')]
        return SB3HerPolicyTrainer(env_fn,HER("MlpPolicy",env_fn(),model_class=algo,device=device,**hyperparams))
    else:
        raise ValueError("bad agent name, must be one of ['rainbow', 'SB3_OFF', 'SB3_ON', 'SB3_HER']")

if __name__ == "__main__":
    agent = make_agent("rainbow","space_invaders","cpu",{})
    agent = make_agent("SB3_OFF","Pendulum-v0","cpu",{'ALGO':'TD3'})
    agent = make_agent("SB3_ON","Pendulum-v0","cpu",{'ALGO':'PPO'})
    # agent = make_agent("SB3_HER","Pendulum-v0","cpu",{'ALGO':'TD3',"max_episode_length":100})
