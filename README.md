# objaverse-simple-rendering

To run the example, first install the dependencies:

```bash
sudo source setup.sh
```

Then download the objects:

```bash
python3 download_objaverse.py
```

Then run:

```bash
blender-3.2.2-linux-x64/blender -b -P blender_script.py -- --input_model_paths input_model_paths.json
```
