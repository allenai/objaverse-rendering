# objaverse-simple-rendering

To run the example, first install the dependencies:

```bash
source setup.sh
```

Then download the objects:

```bash
python3 download_objaverse.py
```

Then authorize Wandb and AWS S3.

Then run:

```bash
pip install -r requirements.txt
screen -S objaverse
python3 distributed.py \
  --num_gpus 8 \
  --workers_per_gpu 10 \
  --input_model_paths input_model_paths.json
```
