# Objaverse Rendering

Scripts to perform distributed rendering of Objaverse objects in Blender across many GPUs and processes.

### System requirements

We have only tested the rendering scripts on Ubuntu machines that have NVIDIA GPUs.

If you run into any issues, please open an issue! :)

### Installation

1. Install Blender

```bash
wget https://download.blender.org/release/Blender3.2/blender-3.2.2-linux-x64.tar.xz
tar -xf blender-3.2.2-linux-x64.tar.xz
rm blender-3.2.2-linux-x64.tar.xz
```

2. Update certificates for Blender to download URLs

```bash
# this is needed to download urls in blender
# https://github.com/python-poetry/poetry/issues/5117#issuecomment-1058747106
sudo update-ca-certificates --fresh
export SSL_CERT_DIR=/etc/ssl/certs
```

3. Install Python dependencies

```bash
pip install -r requirements.txt
```

4. (Optional) If you are running rendering on a headless machine, you will need to start an xserver. To do this, run:

```bash
sudo apt-get install xserver-xorg
sudo python3 scripts/start_xserver.py start
```

### Rendering

1. Download the objects:

```bash
python3 scripts/download_objaverse.py --start_i 0 --end_i 100
```

2. Start the distributed rendering script:

```bash
python3 scripts/distributed.py \
  --num_gpus <NUM_GPUs> \
  --workers_per_gpu <WORKERS_PER_GPU> \
  --input_models_path <INPUT_MODELS_PATH>
```

This will then render the images into the `views` directory.

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
