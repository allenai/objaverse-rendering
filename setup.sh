RUN wget https://download.blender.org/release/Blender3.2/blender-3.2.2-linux-x64.tar.xz
RUN tar -xf blender-3.2.2-linux-x64.tar.xz
RUN rm blender-3.2.2-linux-x64.tar.xz

sudo python3 ai2thor-xorg.py start
export DISPLAY=:0.0