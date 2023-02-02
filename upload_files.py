import argparse
import glob
import shutil
import time

import boto3
from tqdm import tqdm

# total number of files uploaded
parser = argparse.ArgumentParser()
parser.add_argument("--num_files", type=int, required=True, help="total number of files uploaded")
args = parser.parse_args()

uploaded_files = set()
s3 = boto3.client("s3")
while len(uploaded_files) < args.num_files:
    print(len(uploaded_files), args.num_files)
    time.sleep(5)
    # upload the files
    png_files = set(glob.glob("views/**/*.png"))
    unuploaded_files = png_files - uploaded_files
    time.sleep(5)

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