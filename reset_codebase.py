import os
import shutil

src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../snake-game'))
dst_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), './codebase'))

# Remove all contents from codebase
for item in os.listdir(dst_dir):
    item_path = os.path.join(dst_dir, item)
    if os.path.isdir(item_path):
        shutil.rmtree(item_path)
    else:
        os.remove(item_path)

# Copy from snake-game to codebase, excluding .git and .gitignore
for item in os.listdir(src_dir):
    if item in ['.git', '.gitignore']:
        continue
    src_item = os.path.join(src_dir, item)
    dst_item = os.path.join(dst_dir, item)
    if os.path.isdir(src_item):
        shutil.copytree(src_item, dst_item)
    else:
        shutil.copy2(src_item, dst_item)