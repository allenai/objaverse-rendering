import argparse
import glob
import json
import os
import shutil
import subprocess
import time

import boto3
from tqdm import tqdm

import wandb

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
# model_paths = [model_paths[i:i + models_per_worker] for i in range(0, num_models, models_per_worker)]
model_paths = [model_paths[i::num_workers] for i in range(num_workers)]
assert num_models == sum([len(x) for x in model_paths])

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


# do monitoring on all of the progress
wandb.init(project="objaverse-rendering", entity="prior-ai2")
wandb.config.update(args)

i = 0
uploaded_files = set()
s3 = boto3.client('s3')

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
    i += 1

    if i % 10 == 0:
        # upload the files
        png_files = set(glob.glob("views/**/*.png"))
        unuploaded_files = png_files - uploaded_files

        for png_file in tqdm(unuploaded_files):
            # upload the file without the views/ prefix
            s3.upload_file(png_file, "objaverse-images", png_file[len("views/"):])
            uploaded_files.add(png_file)

        # check for all the views directories that have 12 files in them
        # if there are 12 files, delete the directory
        for views_dir in glob.glob("views/*"):
            # check if there are 12 files in the directory
            # and if all the files are uploaded
            files = glob.glob(f"{views_dir}/*.png")
            if len(files) == 12 and set(files).issubset(uploaded_files):
                shutil.rmtree(views_dir)
