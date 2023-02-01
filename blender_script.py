"""Blender script to render images of 3D models.

This script is used to render images of 3D models. It takes in a list of paths
to .glb files and renders images of each model. The images are from rotating the
object around the origin. The images are saved to the output directory.

Example usage:
    blender -b -P blender_script.py -- \
        --input_model_paths input_model_paths.json \
        --output_dir ./views \
        --engine CYCLES \
        --scale 0.8 \
        --num_images 12 \
        --camera_dist 1.2

Here, input_model_paths.json is a json file containing a list of paths to .glb.
"""

import argparse
import json
import math
import os
import random
import sys
import time
from typing import Tuple

import bpy

parser = argparse.ArgumentParser()
parser.add_argument(
    "--input_model_paths",
    type=str,
    required=True,
    help="Path to a json file containing a list of paths to .glb files.",
)
parser.add_argument("--output_dir", type=str, default="./views")
parser.add_argument(
    "--engine", type=str, default="BLENDER_EEVEE", choices=["CYCLES", "BLENDER_EEVEE"]
)
parser.add_argument("--scale", type=float, default=0.8)
parser.add_argument("--num_images", type=int, default=12)
parser.add_argument("--camera_dist", type=int, default=1.2)
parser.add_argument("--worker_i", type=int, default=0)

argv = sys.argv[sys.argv.index("--") + 1 :]
args = parser.parse_args(argv)

context = bpy.context
scene = context.scene
render = scene.render

render.engine = args.engine
render.image_settings.file_format = "PNG"
render.image_settings.color_mode = "RGBA"
render.resolution_x = 512
render.resolution_y = 512
render.resolution_percentage = 100

scene.cycles.device = "GPU"
scene.cycles.samples = 32
scene.cycles.diffuse_bounces = 1
scene.cycles.glossy_bounces = 1
scene.cycles.transparent_max_bounces = 3
scene.cycles.transmission_bounces = 3
scene.cycles.filter_width = 0.01
scene.cycles.use_denoising = True
scene.render.film_transparent = True

cam = scene.objects["Camera"]
cam.location = (0, 1.2, 0)
cam.data.lens = 35
cam.data.sensor_width = 32

cam_constraint = cam.constraints.new(type="TRACK_TO")
cam_constraint.track_axis = "TRACK_NEGATIVE_Z"
cam_constraint.up_axis = "UP_Y"

# setup lighting
bpy.ops.object.light_add(type="AREA")
light2 = bpy.data.lights["Area"]
light2.energy = 30000
bpy.data.objects["Area"].location[2] = 0.5
bpy.data.objects["Area"].scale[0] = 100
bpy.data.objects["Area"].scale[1] = 100
bpy.data.objects["Area"].scale[2] = 100


def sample_point_on_sphere(radius: float) -> Tuple[float, float, float]:
    theta = random.random() * 2 * math.pi
    phi = math.acos(2 * random.random() - 1)
    return (
        radius * math.sin(phi) * math.cos(theta),
        radius * math.sin(phi) * math.sin(theta),
        radius * math.cos(phi),
    )


def randomize_lighting() -> None:
    light2.energy = random.uniform(5000, 35000)
    bpy.data.objects["Area"].location[0] = 0
    bpy.data.objects["Area"].location[1] = 0
    bpy.data.objects["Area"].location[2] = random.uniform(0.5, 1.5)


def reset_lighting() -> None:
    light2.energy = 30_000
    bpy.data.objects["Area"].location[0] = 0
    bpy.data.objects["Area"].location[1] = 0
    bpy.data.objects["Area"].location[2] = 0.5


def join_meshes() -> bpy.types.Object:
    """Joins all the meshes in the scene into one mesh."""
    # get all the meshes in the scene
    meshes = [obj for obj in bpy.data.objects if obj.type == "MESH"]
    # join all of the meshes
    bpy.ops.object.select_all(action="DESELECT")
    for mesh in meshes:
        mesh.select_set(True)
        bpy.context.view_layer.objects.active = mesh
    # join the meshes
    bpy.ops.object.join()
    meshes = [obj for obj in bpy.data.objects if obj.type == "MESH"]
    assert len(meshes) == 1
    mesh = meshes[0]
    return mesh


def center_mesh(mesh: bpy.types.Object) -> None:
    """Centers the mesh at the origin."""
    # select the mesh
    bpy.ops.object.select_all(action="DESELECT")
    mesh.select_set(True)
    # clear and keep the transformation of the parent
    bpy.ops.object.parent_clear(type="CLEAR_KEEP_TRANSFORM")
    # set the mesh position to the origin, use the bounding box center
    bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY", center="BOUNDS")
    bpy.context.object.location = (0, 0, 0)
    # 0 out the transform
    bpy.ops.object.transforms_to_deltas(mode="ALL")


def resize_object(mesh: bpy.types.Object, max_side_length_meters: float) -> None:
    """Resizes the object to have a max side length of max_side_length_meters meters."""
    # select the mesh
    bpy.ops.object.select_all(action="DESELECT")
    mesh.select_set(True)
    # get the bounding box
    x_size, y_size, z_size = mesh.dimensions
    # get the max side length
    curr_max_side_length = max([x_size, y_size, z_size])
    # get the scale factor
    scale_factor = max_side_length_meters / curr_max_side_length
    # scale the object
    bpy.ops.transform.resize(value=(scale_factor, scale_factor, scale_factor))
    # 0 out the transform
    bpy.ops.object.transforms_to_deltas(mode="ALL")


def reset_scene() -> None:
    """Resets the scene to a clean state."""
    # delete everything that isn't part of a camera or a light
    for obj in bpy.data.objects:
        if obj.type not in {"CAMERA", "LIGHT"}:
            bpy.data.objects.remove(obj, do_unlink=True)
    # delete all the materials
    for material in bpy.data.materials:
        bpy.data.materials.remove(material, do_unlink=True)
    # delete all the textures
    for texture in bpy.data.textures:
        bpy.data.textures.remove(texture, do_unlink=True)
    # delete all the images
    for image in bpy.data.images:
        bpy.data.images.remove(image, do_unlink=True)


# load the glb model
def load_object(object_path: str) -> None:
    """Loads a glb model into the scene."""
    if object_path.endswith(".glb"):
        bpy.ops.import_scene.gltf(filepath=object_path, merge_vertices=True)
    elif object_path.endswith(".fbx"):
        bpy.ops.import_scene.fbx(filepath=object_path)
    else:
        raise ValueError(f"Unsupported file type: {object_path}")


def save_images(object_file: str) -> None:
    """Saves rendered images of the object in the scene."""
    os.makedirs(args.output_dir, exist_ok=True)

    reset_scene()

    # load the object
    load_object(object_file)
    object_uid = os.path.basename(object_file).split(".")[0]
    mesh = join_meshes()
    center_mesh(mesh)
    resize_object(mesh, args.scale)

    for i in range(args.num_images):
        # set the camera position
        cam_constraint.target = mesh
        theta = (i / args.num_images) * math.pi * 2
        phi = math.radians(60)
        point = (
            args.camera_dist * math.sin(phi) * math.cos(theta),
            args.camera_dist * math.sin(phi) * math.sin(theta),
            args.camera_dist * math.cos(phi),
        )
        reset_lighting()
        cam.location = point

        # render the image
        render_path = os.path.join(args.output_dir, object_uid, f"{i:03d}.png")
        scene.render.filepath = render_path
        bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    with open(args.input_model_paths) as f:
        object_paths = json.load(f)

    os.makedirs("progress", exist_ok=True)
    start = time.time()
    with open(f"progress/{args.worker_i}.csv", "w") as f:
        f.write("num_finished,total,object_path,time\n")
    for curr_object_i, object_path in enumerate(object_paths):
        try:
            start_i = time.time()
            save_images(object_path)
            end_i = time.time()
            print("Finished", object_path, "in", end_i - start_i, "seconds")
            with open(f"progress/{args.worker_i}.csv", "a") as f:
                f.write(
                    f"{curr_object_i + 1},{len(object_paths)},{object_path},{end_i - start_i}\n"
                )
        except:
            print("Failed to render", object_path)
            time.sleep(2)
    end = time.time()
    print(
        "Finished all in",
        end - start,
        "seconds, average",
        (end - start) / len(object_paths),
        "seconds per object",
    )
