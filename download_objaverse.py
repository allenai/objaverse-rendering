import json
import random

import objaverse

# set the random seed to 42
random.seed(42)

uids = objaverse.load_uids()

random.shuffle(uids)

uids = uids[:100]

paths = objaverse.load_objects(uids)

with open("input_model_paths.json", "w") as f:
    json.dump(list(paths.values()), f, indent=2)
