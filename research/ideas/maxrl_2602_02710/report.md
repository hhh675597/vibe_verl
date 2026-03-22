# Report: MaxRL Reproduction On Math GRPO Recipe

*Generated: 2026-03-22 13:24 | idea_id: `maxrl_2602_02710`*

## Status: Successful run, no baseline available for comparison

## Results

*No baseline is recorded yet in `research/ledger/best.json`, so this run is evaluated standalone.*

| Metric | Value |
|---|---|
| Validation metric | `val/aime24/test_score` |
| Step 25 validation | `0.13333333333333333` |
| Step 50 validation | `0.16666666666666666` |
| Final training reward mean | `0.48046875` |
| Best observed training reward mean | `0.509765625` at step `18` |
| Final step throughput | `1182.4000668374458` tokens/s |
| Avg throughput, last 10 train steps | `2989.4354236389318` tokens/s |
| Avg step time, last 10 train steps | `149.52079371450236`s |
| Avg response clip ratio, last 10 train steps | `0.458203125` |
| Full-run duration | `7242`s |

## Run History

| Run ID | Profile | Status | Best Metric | Steps | Duration |
|--------|---------|--------|-------------|-------|----------|
| 20260322_103207_math_grpo_small_smoke_ma... | smoke | failed | - | - | 11s |
| 20260322_103327_math_grpo_small_smoke_ma... | smoke | failed | - | - | 45s |
| 20260322_103649_math_grpo_small_smoke_ma... | smoke | failed | - | - | 215s |
| 20260322_104421_math_grpo_small_smoke_ma... | smoke | failed | - | - | 13s |
| 20260322_104520_math_grpo_small_smoke_ma... | smoke | failed | - | - | 84s |
| 20260322_104727_math_grpo_small_smoke_ma... | smoke | failed | - | - | 416s |
| 20260322_105451_math_grpo_small_smoke_ma... | smoke | success | - | 2 | 199s |
| 20260322_105922_math_grpo_small_full_max... | full | failed | - | - | 376s |
| 20260322_110756_math_grpo_small_full_max... | full | failed | - | - | 387s |
| 20260322_111435_math_grpo_small_full_max... | full | failed | - | - | 285s |
| 20260322_112008_math_grpo_small_full_max... | full | success | - | 50 | 7242s |

## Errors Encountered

### 20260322_103207_math_grpo_small_smoke_maxrl_2602_02710_s1
- **Status**: failed (exit code 1)
- **Traceback**:
```
Traceback (most recent call last):
  File "/data/home/zdhs0086/hhh/verl-agent/verl/trainer/main_ppo.py", line 31, in main
    run_ppo(config)
```

### 20260322_103327_math_grpo_small_smoke_maxrl_2602_02710_s1
- **Status**: failed (exit code 1)
- **Log tail** (last 5 lines):
```
/data/home/zdhs0086/.conda/envs/vibe-verl/lib/python3.10/site-packages/torch/cuda/__init__.py:61: FutureWarning: The pynvml package is deprecated. Please install nvidia-ml-py instead. If you did not install pynvml directly, please report this to the maintainers of the package that installed pynvml for you.
  import pynvml  # type: ignore[import]
ray init kwargs: {'num_cpus': 96, 'runtime_env': {'env_vars': {'TOKENIZERS_PARALLELISM': 'true', 'NCCL_DEBUG': 'WARN', 'VLLM_LOGGING_LEVEL': 'WARN', 'VLLM_ALLOW_RUNTIME_LORA_UPDATING': 'true', 'VLLM_ALLREDUCE_USE_SYMM_MEM': '0', 'CUDA_DEVICE_MAX_CONNECTIONS': '1', 'NCCL_CUMEM_ENABLE': '0'}, 'working_dir': None}}
2026-03-22 10:33:43,575	INFO worker.py:1879 -- Started a local Ray instance. View the dashboard at [1m[32m127.0.0.1:8265 [39m[22m
[2026-03-22 10:34:14,020 E 2768345 2768345] core_worker.cc:513: Failed to register worker to Raylet: IOError: [RayletClient] Unable to register worker with raylet. Failed to read data from the socket: End of file worker_id=01000000ffffffffffffffffffffffffffffffffffffffffffffffff
```

### 20260322_103649_math_grpo_small_smoke_maxrl_2602_02710_s1
- **Status**: failed (exit code 1)
- **Traceback**:
```
[36m(TaskRunner pid=2774860)[0m Traceback (most recent call last):
[36m(TaskRunner pid=2774860)[0m   File "/data/home/zdhs0086/hhh/verl-agent/verl/utils/tracking.py", line 133, in __del__
[36m(TaskRunner pid=2774860)[0m     if "wandb" in self.logger:
[36m(TaskRunner pid=2774860)[0m AttributeError: 'Tracking' object has no attribute 'logger'
[36m(WorkerDict pid=2778543)[0m kwargs: {'n': 1, 'logprobs': 0, 'max_tokens': 8192, 'detokenize': False, 'temperature': 1.0, 'top_k': -1, 'top_p': 1, 'ignore_eos': False}
[36m(WorkerDict pid=2778543)[0m /data/home/zdhs0086/.conda/envs/vibe-verl/lib/python3.10/site-packages/torch/distributed/fsdp/fully_sharded_data_parallel.py:690: FutureWarning: FSDP.state_dict_type() and FSDP.set_state_dict_type() are being deprecated. Please use APIs, get_state_dict() and set_state_dict(), which can support different parallelisms, FSDP1, FSDP2, DDP. API doc: https://pytorch.org/docs/stable/distributed.checkpoint.html#torch.distributed.checkpoint.state_dict.get_state_dict .Tutorial: https://pytorch.org/tutorials/recipes/distributed_checkpoint_recipe.html .
[36m(WorkerDict pid=2778543)[0m   warnings.warn(
```

### 20260322_104421_math_grpo_small_smoke_maxrl_2602_02710_s1
- **Status**: failed (exit code 1)
- **Log tail** (last 9 lines):
```
/data/home/zdhs0086/.conda/envs/vibe-verl/lib/python3.10/site-packages/torch/cuda/__init__.py:61: FutureWarning: The pynvml package is deprecated. Please install nvidia-ml-py instead. If you did not install pynvml directly, please report this to the maintainers of the package that installed pynvml for you.
  import pynvml  # type: ignore[import]
Could not override 'env.name'.
To append to your config use +env.name=math
Key 'name' is not in struct
    full_key: env.name
    object_type=dict

Set the environment variable HYDRA_FULL_ERROR=1 for a complete stack trace.
```

### 20260322_104520_math_grpo_small_smoke_maxrl_2602_02710_s1
- **Status**: failed (exit code 1)
- **Traceback**:
```
Traceback (most recent call last):
  File "/data/home/zdhs0086/hhh/verl-agent/verl/trainer/main_ppo.py", line 31, in main
    run_ppo(config)
```

### 20260322_104727_math_grpo_small_smoke_maxrl_2602_02710_s1
- **Status**: failed (exit code 143)
- **Log tail** (last 100 lines):
```
[36m(TaskRunner pid=2787239)[0m test_gen_batch meta info: {'eos_token_id': 151643, 'pad_token_id': 151643, 'recompute_log_prob': False, 'do_sample': True, 'validate': True}
[36m(TaskRunner pid=2787239)[0m validation generation end
[36m(TaskRunner pid=2787239)[0m test_gen_batch meta info: {'eos_token_id': 151643, 'pad_token_id': 151643, 'recompute_log_prob': False, 'do_sample': True, 'validate': True}
[36m(TaskRunner pid=2787239)[0m validation generation end
[36m(TaskRunner pid=2787239)[0m test_gen_batch meta info: {'eos_token_id': 151643, 'pad_token_id': 151643, 'recompute_log_prob': False, 'do_sample': True, 'validate': True}
[36m(TaskRunner pid=2787239)[0m validation generation end
[36m(TaskRunner pid=2787239)[0m test_gen_batch meta info: {'eos_token_id': 151643, 'pad_token_id': 151643, 'recompute_log_prob': False, 'do_sample': True, 'validate': True}
*** SIGTERM received at time=1774148064 on cpu 48 ***
[failure_signal_handler.cc : 345] RAW: Signal 15 raised at PC=0x14786444c81c while already in AbslFailureSignalHandler()
*** SIGTERM received at time=1774148064 on cpu 48 ***
PC: @     0x14786444c81c  (unknown)  __read
    @     0x14786437a520       3552  (unknown)
    @     0x1477cba5d089        208  absl::lts_20230802::debugging_internal::ReadAddrMap()
    @     0x1477cba5d2f1         80  absl::lts_20230802::debugging_internal::(anonymous namespace)::Symbolizer::FindObjFile()
    @     0x1477cba5d33e       1296  absl::lts_20230802::debugging_internal::(anonymous namespace)::Symbolizer::GetUncachedSymbol()
```

### 20260322_105922_math_grpo_small_full_maxrl_2602_02710_s1
- **Status**: failed (exit code 1)
- **Traceback**:
```
Traceback (most recent call last):
  File "/data/home/zdhs0086/hhh/verl-agent/verl/trainer/main_ppo.py", line 31, in main
    run_ppo(config)
```

### 20260322_110756_math_grpo_small_full_maxrl_2602_02710_s1
- **Status**: failed (exit code 143)
- **Log tail** (last 100 lines):
```
    @ ... and at least 1 more frames
[2026-03-22 11:14:25,804 E 2809790 2809790] logging.cc:496: *** SIGTERM received at time=1774149265 on cpu 145 ***
[2026-03-22 11:14:25,804 E 2809790 2809790] logging.cc:496: PC: @     0x154c6dd2888d  (unknown)  syscall
[2026-03-22 11:14:25,804 E 2809790 2809790] logging.cc:496:     @     0x154c6dc4c520       3488  (unknown)
[2026-03-22 11:14:25,804 E 2809790 2809790] logging.cc:496:     @     0x154bd69bca74        208  absl::lts_20230802::WriteSignalMessage()
[2026-03-22 11:14:25,804 E 2809790 2809790] logging.cc:496:     @     0x154bd69bcb4f         80  absl::lts_20230802::AbslFailureSignalHandler()
[2026-03-22 11:14:25,804 E 2809790 2809790] logging.cc:496:     @     0x154c6dc4c520  (unknown)  (unknown)
[2026-03-22 11:14:25,804 E 2809790 2809790] logging.cc:496:     @ ... and at least 1 more frames
PC: @     0x154c6dc9b117  (unknown)  (unknown)
    @     0x154c6dc4c520  (unknown)  (unknown)
    @ ... and at least 1 more frames
[2026-03-22 11:14:25,805 E 2809790 2809790] logging.cc:496: *** SIGTERM received at time=1774149265 on cpu 191 ***
[2026-03-22 11:14:25,805 E 2809790 2809790] logging.cc:496: PC: @     0x154c6dc9b117  (unknown)  (unknown)
[2026-03-22 11:14:25,805 E 2809790 2809790] logging.cc:496:     @     0x154c6dc4c520  (unknown)  (unknown)
[2026-03-22 11:14:25,805 E 2809790 2809790] logging.cc:496:     @ ... and at least 1 more frames
```

### 20260322_111435_math_grpo_small_full_maxrl_2602_02710_s1
- **Status**: failed (exit code 1)
- **Traceback**:
```
Traceback (most recent call last):
  File "/data/home/zdhs0086/hhh/verl-agent/verl/trainer/main_ppo.py", line 31, in main
    run_ppo(config)
```

## Conclusion

MaxRL now runs successfully in this VeRL checkout on the math environment after fixing a sequence of harness and recipe mismatches: the math env key, smoke grouping, `raw_prompt` propagation, the missing `file` logger, 8-GPU activation, Ray CPU budget, and actor/log-prob micro-batch sizing.

On the final successful run, the validation metric `val/aime24/test_score` improved from `0.13333333333333333` at step 25 to `0.16666666666666666` at step 50. Training looked stable rather than divergent: recent reward means stayed around `0.39-0.48`, KL remained small, and the run sustained roughly 3.0k tokens/s over the later non-validation steps on 8 H100s.

The main remaining efficiency limitation is long generation length. Response clip ratio stayed around `0.46` over the last 10 steps, which means a large fraction of samples still hit the 8192-token cap. The next obvious follow-up is not another algorithm change first, but tightening generation length or task formatting so rollout compute is spent on useful tokens rather than capped responses.
