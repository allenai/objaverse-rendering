wget https://download.blender.org/release/Blender3.2/blender-3.2.2-linux-x64.tar.xz
tar -xf blender-3.2.2-linux-x64.tar.xz
rm blender-3.2.2-linux-x64.tar.xz

# this is needed to download urls in blender
sudo update-ca-certificates --fresh
export SSL_CERT_DIR=/etc/ssl/certs

sudo python3 ai2thor-xorg.py start || true
export DISPLAY=:0.0