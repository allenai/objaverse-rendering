import argparse
import json
import random

import boto3
import objaverse
from tqdm import tqdm

parser = argparse.ArgumentParser()
parser.add_argument(
    "--start_i", type=int, required=True, help="total number of files uploaded"
)
parser.add_argument(
    "--end_i", type=int, required=True, help="total number of files uploaded"
)
args = parser.parse_args()


def get_completed_uids():
    # get all the files in the objaverse-images bucket
    s3 = boto3.resource("s3")
    bucket = s3.Bucket("objaverse-images")
    bucket_files = [obj.key for obj in tqdm(bucket.objects.all())]

    bucket_files[:10]
    dir_counts = {}
    for file in bucket_files:
        d = file.split("/")[0]
        dir_counts[d] = dir_counts.get(d, 0) + 1

    # get the directories with 12 files
    dirs = [d for d, c in dir_counts.items() if c == 12]
    return set(dirs)


# set the random seed to 42
random.seed(42)

uids = objaverse.load_uids()

random.shuffle(uids)

object_paths = objaverse._load_object_paths()
uids = uids[args.start_i : args.end_i]

# get the uids that have already been downloaded
completed_uids = get_completed_uids()
uids = [uid for uid in uids if uid not in completed_uids]

uid_object_paths = [
    f"https://huggingface.co/datasets/allenai/objaverse/resolve/main/{object_paths[uid]}"
    for uid in uids
]

with open("input_model_paths.json", "w") as f:
    json.dump(uid_object_paths, f, indent=2)
