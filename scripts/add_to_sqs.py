import multiprocessing
from multiprocessing import Pool

import boto3
import objaverse
from tqdm import tqdm

uids = objaverse.load_uids()

object_paths = objaverse._load_object_paths()

# get the uids that have already been downloaded
uid_object_paths = [{
    "Id": uid,
    "MessageBody": f"https://huggingface.co/datasets/allenai/objaverse/resolve/main/{object_paths[uid]}"
}
    for uid in uids
]
batches = [uid_object_paths[i:i+10] for i in range(0, len(uid_object_paths), 10)]

# Create an SQS client
sqs = boto3.client("sqs")

# Get the URL for the queue you want to receive a message from
queue_url = "https://sqs.us-west-2.amazonaws.com/667572507351/objaverse-rendering"

def upload_batch(batch):
    sqs.send_message_batch(
        QueueUrl=queue_url,
        Entries=batch
    )

# use tqdm and multiprocessing to upload the batches
with Pool(multiprocessing.cpu_count()) as p:
    list(tqdm(p.imap(upload_batch, batches), total=len(batches)))
