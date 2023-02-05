import argparse
import json
import os
import shutil
import subprocess
import time
import subprocess

import wandb

# choose number of gpus
parser = argparse.ArgumentParser()
parser.add_argument('--num_gpus', type=int, default=-1, help='number of gpus to use. -1 means all available gpus')
parser.add_argument('--workers_per_gpu', type=int, default=1, help='number of workers per gpu')
parser.add_argument('--input_model_paths', type=str, required=True, help='Path to a json file containing a list of paths to .glb files.')
args = parser.parse_args()

def get_gpu_count():
    result = subprocess.run(
        ["nvidia-smi", "--query-gpu=index", "--format=csv,noheader"],
        stdout=subprocess.PIPE
    )
    return len(result.stdout.splitlines())


if args.num_gpus == -1:
    args.num_gpus = get_gpu_count()

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
# model_paths = [model_paths[i:i + models_per_worker] for i in range(0, num_models, models_per_worker)]
model_paths = [model_paths[i::num_workers] for i in range(num_workers)]
assert num_models == sum([len(x) for x in model_paths])

# delete the views dir
shutil.rmtree('views', ignore_errors=True)

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
            f"export DISPLAY=:0.{gpu_i} &&"
            f" blender-3.2.2-linux-x64/blender -b -P blender_script.py --"
            f" --input_model_paths {worker_input_paths}"
            f" --worker_i {worker_i}"
        )

        subprocess.Popen(command, shell=True)

# upload the files to s3
subprocess.Popen(f"python3 upload_files.py --num_files {num_models * 12}", shell=True)

# do monitoring on all of the progress
wandb.init(project="objaverse-rendering", entity="prior-ai2")
wandb.config.update(args)

while True:
    time.sleep(10)
    # check the progress/{worker_id}.csv files of each of the workers
    num_finished = 0
    for worker_i in range(num_workers):
        progress_file = f'progress/{worker_i}.csv'
        # read the last line of the progress file
        if os.path.exists(progress_file):
            with open(progress_file, 'r') as f:
                lines = f.readlines()
                if len(lines) > 1:
                    worker_progress = lines[-1].strip()
                    num_finished_, total_, object_path, total_time = worker_progress.split(',')
                    num_finished += int(num_finished_)
    percentage = num_finished / num_models
    wandb.log({'num_finished': num_finished, 'total': num_models, 'percentage': percentage})
    if num_finished == num_models:
        break
