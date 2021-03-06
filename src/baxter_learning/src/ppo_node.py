#!/usr/bin/python

import spinup2
from baxter_hw_env.envs.baxter_hw_env import BaxterHwEnv

import rospy
import sys
import numpy as np
import gym
from std_msgs.msg import Empty

def run():
    env = lambda : gym.make("BaxterHwEnv-v0")
    # Put ABSOLUTE path to logging directory here, then remove the NotImplementedError.
    # e.g.: "/home/cc/ee106b/sp20/staff/ee106b-taa/Desktop/data/ppo_log"
    OUTPUT_DIR = None
    raise NotImplementedError

    spinup2.ppo(
        env,
        ac_kwargs={"hidden_sizes":(128,2)},
        seed = np.random.randint(100),
        steps_per_epoch=1250,
        pi_lr=3e-4,
        epochs=2500,
        logger_kwargs = {"output_dir" : OUTPUT_DIR}
    )
    #polynomials
#     spinup2.vpgpolynomial(
#         env,
#         ac_kwargs={"order":2},
#         seed = np.random.randint(100),
#         steps_per_epoch=1250,
#         max_ep_len=25,
#         epochs=2500,
# #        pi_lr=2e-5,
#         pi_lr=1e-3,
#         l1_scaling=0.01,
#         logger_kwargs = {"output_dir" : "logs/polyrandomtest"}
#     )


if __name__ == "__main__":
    rospy.init_node("ppo")

    run()

    rospy.spin()
