import argparse
import json
import os
import subprocess

# choose number of gpus
parser = argparse.ArgumentParser()
parser.add_argument('--num_gpus', type=int, default=-1, help='number of gpus to use. -1 means all available gpus')
parser.add_argument('--workers_per_gpu', type=int, default=1, help='number of workers per gpu')
parser.add_argument('--input_model_paths', type=str, required=True, help='Path to a json file containing a list of paths to .glb files.')
args = parser.parse_args()

if args.num_gpus == -1:
    # TODO: fix this hard coded bug!!!
    args.num_gpus = 4

print(args)

with open(args.input_model_paths, 'r') as f:
    model_paths = json.load(f)

num_workers = args.num_gpus * args.workers_per_gpu
num_models = len(model_paths)
models_per_worker = num_models // num_workers

print(f'num_workers: {num_workers}')
print(f'num_models: {num_models}')
print(f'models_per_worker: {models_per_worker}')

# create a list of lists of model paths
model_paths = [model_paths[i:i + models_per_worker] for i in range(0, num_models, models_per_worker)]

# create a tmp dir
os.makedirs('tmp', exist_ok=True)
for gpu_i in range(args.num_gpus):
    for worker_i in range(args.workers_per_gpu):
        worker_i = gpu_i * args.workers_per_gpu + worker_i
        worker_objects = model_paths[worker_i]
        worker_input_paths = f'tmp/input_model_paths_{worker_i}.json'
        with open(worker_input_paths, 'w') as f:
            json.dump(worker_objects, f, indent=2)
        command = (
            f"export DISPLAY=:0.{gpu_i} && "
            f"blender-3.2.2-linux-x64/blender -b -P blender_script.py -- "
            f"--input_model_paths {worker_input_paths}"
        )

        subprocess.Popen(command, shell=True)

