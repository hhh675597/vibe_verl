# Copyright 2026 Bytedance Ltd. and/or its affiliates
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest

import numpy as np
import torch

from verl.trainer.ppo import core_algos


class TestMaxRLOutcomeAdvantage(unittest.TestCase):
    def test_group_mean_normalization(self):
        token_level_rewards = torch.tensor(
            [
                [0.0, 1.0],
                [0.0, 0.0],
                [1.0, 0.0],
                [1.0, 0.0],
            ],
            dtype=torch.float32,
        )
        response_mask = torch.ones_like(token_level_rewards)
        index = np.array(["a", "a", "b", "b"], dtype=object)
        traj_index = np.array([0, 1, 2, 3], dtype=object)

        advantages, returns = core_algos.compute_maxrl_outcome_advantage(
            token_level_rewards=token_level_rewards,
            response_mask=response_mask,
            index=index,
            traj_index=traj_index,
        )

        expected = torch.tensor(
            [
                [1.0, 1.0],
                [-1.0, -1.0],
                [0.0, 0.0],
                [0.0, 0.0],
            ],
            dtype=torch.float32,
        )

        torch.testing.assert_close(advantages, expected)
        torch.testing.assert_close(returns, expected)

    def test_zero_mean_groups_stay_finite(self):
        token_level_rewards = torch.zeros((3, 2), dtype=torch.float32)
        response_mask = torch.tensor(
            [
                [1.0, 1.0],
                [1.0, 0.0],
                [1.0, 1.0],
            ],
            dtype=torch.float32,
        )
        index = np.array(["z", "z", "z"], dtype=object)
        traj_index = np.array([0, 1, 2], dtype=object)

        advantages, returns = core_algos.compute_maxrl_outcome_advantage(
            token_level_rewards=token_level_rewards,
            response_mask=response_mask,
            index=index,
            traj_index=traj_index,
        )

        expected = torch.zeros_like(response_mask)

        self.assertTrue(torch.isfinite(advantages).all())
        torch.testing.assert_close(advantages, expected)
        torch.testing.assert_close(returns, expected)


if __name__ == "__main__":
    unittest.main()
