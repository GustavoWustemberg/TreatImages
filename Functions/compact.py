import os
from PIL import Image
import logging
from Class.tools import functionalities


def compact(root_folder, value_quality):
    for root, dirs, files in os.walk(root_folder):
        for file in files:
            filename, extension = os.path.splitext(file)
            if functionalities.is_image(extension):
                new_imgName = filename + extension
                original_img_path = os.path.join(root, file)
                new_img_path = os.path.join(root, new_imgName)
                try:
                    pillow_img = Image.open(original_img_path)
                    new_img = pillow_img
                    new_img.save(new_img_path, optmize=True, quality=value_quality)
                except Exception as e:
                    logging.error(f'Erro ao compactar {original_img_path}: {e}')