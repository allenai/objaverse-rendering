# Objaverse Rendering

To run the example, first install the dependencies:

```bash
source setup.sh
```

Then download the objects:

```bash
python3 download_objaverse.py
```

### System requirements

We have only tested the rendering scripts on Ubuntu machines that have NVIDIA GPUs.

Then run:

```bash
pip install -r requirements.txt
screen -S objaverse
python3 distributed.py \
  --num_gpus 8 \
  --workers_per_gpu 10 \
  --input_model_paths input_model_paths.json
```

### (Optional) Logging and Uploading

In the `scripts/distributed.py` script, we use [Wandb](https://wandb.ai/site) to log the rendering results. You can create a free account and then set the `WANDB_API_KEY` environment variable to your API key.

We also use [AWS S3](https://aws.amazon.com/s3/) to upload the rendered images. You can create a free account and then set the `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` environment variables to your credentials.

### 👋 Our Team

Objaverse is an open-source project built by the [PRIOR team](//prior.allenai.org) at the [Allen Institute for AI](//allenai.org) (AI2).
AI2 is a non-profit institute with the mission to contribute to humanity through high-impact AI research and engineering.

<br />

<a href="//prior.allenai.org">
<p align="center"><img width="100%" src="https://raw.githubusercontent.com/allenai/ai2thor/main/doc/static/ai2-prior.svg" /></p>
</a>
