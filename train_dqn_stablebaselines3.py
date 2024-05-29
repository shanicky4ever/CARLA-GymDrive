from env.environment import CarlaEnv
from stable_baselines3 import DQN
import gymnasium as gym

from agent.stablebaselines3_architectures import CustomExtractor_DQN

from stable_baselines3.common.callbacks import CheckpointCallback, EvalCallback, CallbackList, StopTrainingOnMaxEpisodes

class CustomEvalCallback(EvalCallback):
    def __init__(self, env, eval_freq, log_path, n_eval_episodes=5, deterministic=True, render=False):
        super().__init__(env, best_model_save_path=log_path, log_path=log_path, eval_freq=eval_freq, 
                         n_eval_episodes=n_eval_episodes, deterministic=deterministic, render=render)
        self.eval_results = []
        self.episode_numbers = []

    def _on_step(self) -> bool:
        result = super()._on_step()
        if self.n_calls % self.eval_freq == 0:
            self.eval_results.append(self.last_mean_reward)
            self.episode_numbers.append(self.n_calls // self.eval_freq)
        return result

    def save_results(self, path):
        with open(path, "w") as f:
            for episode, result in zip(self.episode_numbers, self.eval_results):
                f.write(f"Episode {episode*100}: Mean Reward = {result}\n")

def main():
    env = gym.make('carla-rl-gym-v0', time_limit=55, initialize_server=True, random_weather=True, synchronous_mode=True, continuous=False, show_sensor_data=False, has_traffic=False)
    
    checkpoint_callback = CheckpointCallback(
        save_freq=1000 * env.spec.max_episode_steps,
        save_path="./checkpoints/",
        name_prefix="dqn_av_checkpoint",
        save_replay_buffer=True,
        save_vecnormalize=True,
    )
    
    eval_callback = CustomEvalCallback(env, eval_freq=100 * env.spec.max_episode_steps, log_path="./logs/")
    
    callback_max_episodes = StopTrainingOnMaxEpisodes(max_episodes=5000, verbose=1)
    
    callback = CallbackList([checkpoint_callback, eval_callback, callback_max_episodes])
    
    policy_kwargs = dict(
        features_extractor_class=CustomExtractor_DQN,
    )
    
    model = DQN(
        policy="MultiInputPolicy",
        policy_kwargs=policy_kwargs,
        env=env,
        buffer_size=5000,
        learning_starts=1000,
        batch_size=32,
        gamma=0.99,
        train_freq=(4, 'step'),
        gradient_steps=1,
        target_update_interval=1000,
        exploration_fraction=0.1,
        exploration_final_eps=0.02,
        tensorboard_log="./dqn_av_tensorboard/",
        verbose=1,
    )
    
    model.learn(total_timesteps=5000 * env.spec.max_episode_steps, callback=callback)
    
    model.save("checkpoints/sb3_ad_dqn_final")
    env.close()
    
    eval_callback.save_results("logs/dqn_modular_5000_last_execution.txt")

if __name__ == '__main__':
    main()
