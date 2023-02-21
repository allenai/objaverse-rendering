import glob
import multiprocessing
import shutil
import subprocess
import time
from dataclasses import dataclass
from typing import Optional

import boto3
import tyro

import wandb

queue_url = "https://sqs.us-west-2.amazonaws.com/667572507351/objaverse-rendering"


def get_num_messages(sqs) -> int:
    response = sqs.get_queue_attributes(
        QueueUrl=queue_url,
        AttributeNames=['ApproximateNumberOfMessages']
    )
    num_messages = int(response['Attributes']['ApproximateNumberOfMessages'])
    return num_messages


@dataclass
class Args:
    workers_per_gpu: int
    """number of workers per gpu"""

    upload_to_s3: bool = False
    """Whether to upload the rendered images to S3"""

    log_to_wandb: bool = False
    """Whether to log the progress to wandb"""

    num_gpus: int = -1
    """number of gpus to use. -1 means all available gpus"""


def worker(
    count: multiprocessing.Value,
    gpu: int,
    sqs: boto3.client,
    s3: Optional[boto3.client],
) -> None:
    while True:
        try:
            item = sqs.receive_message(
                QueueUrl=queue_url,
                MaxNumberOfMessages=1,
                WaitTimeSeconds=20,
                VisibilityTimeout=120,
            )
        except Exception as e:
            print(e)
            break

        if "Messages" not in item:
            break

        message = item["Messages"][0]
        object_path = message["Body"]

        # Perform some operation on the item
        print(object_path, gpu)
        command = (
            f"export DISPLAY=:0.{gpu} &&"
            f" blender-3.2.2-linux-x64/blender -b -P scripts/blender_script.py --"
            f" --object_path {object_path}"
        )
        subprocess.run(command, shell=True)

        if args.upload_to_s3:
            if object_path.startswith("http"):
                uid = object_path.split("/")[-1].split(".")[0]
                for f in glob.glob(f"views/{uid}/*"):
                    s3.upload_file(
                        f, "objaverse-im", f"{uid}/{f.split('/')[-1]}"
                    )
            # remove the views/uid directory
            shutil.rmtree(f"views/{uid}")
        
        # delete the message
        sqs.delete_message(
            QueueUrl=queue_url,
            ReceiptHandle=message["ReceiptHandle"]
        )

        with count.get_lock():
            count.value += 1


if __name__ == "__main__":
    args = tyro.cli(Args)

    s3 = boto3.client("s3") if args.upload_to_s3 else None
    sqs = boto3.client("sqs")
    count = multiprocessing.Value("i", 0)

    if args.log_to_wandb:
        wandb.init(project="objaverse-rendering", entity="prior-ai2")

    # Start worker processes on each of the GPUs
    for gpu_i in range(args.num_gpus):
        for worker_i in range(args.workers_per_gpu):
            worker_i = gpu_i * args.workers_per_gpu + worker_i
            process = multiprocessing.Process(
                target=worker, args=(count, gpu_i, sqs, s3)
            )
            process.daemon = True
            process.start()

    # update the wandb count
    if args.log_to_wandb:
        while True:
            time.sleep(5)
            num_messages_left = get_num_messages(sqs)
            wandb.log(
                {
                    "count": count.value,
                    "num_messages_left": num_messages_left,
                }
            )
            if num_messages_left == 0:
                break
