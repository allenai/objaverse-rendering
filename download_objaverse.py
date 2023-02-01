import json
import random

import objaverse

# set the random seed to 42
random.seed(42)

uids = objaverse.load_uids()

random.shuffle(uids)

object_paths = objaverse._load_object_paths()
uids = uids[:1000]
uid_object_paths = [f"https://huggingface.co/datasets/allenai/objaverse/resolve/main/{object_paths[uid]}" for uid in uids]

with open("input_model_paths.json", "w") as f:
    json.dump(uid_object_paths, f, indent=2)
