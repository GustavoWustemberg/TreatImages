import os
from PIL import Image
import logging
from Class.tools import functionalities


def resize(root_folder, new_width):
    for root, dirs, files in os.walk(root_folder):
        for file in files:
            filename, extension = os.path.splitext(file)
            if functionalities.is_image(extension):
                new_imgName = filename + extension
                original_img_path = os.path.join(root, file)
                new_img_path = os.path.join(root, new_imgName)
                try:
                    pillow_img = Image.open(original_img_path)
                    width, height = pillow_img.size
                    new_height = functionalities.calc_new_height(width, height, new_width)
                    new_img = pillow_img.resize((new_width, new_height))
                    new_img.save(new_img_path, optmize=True, quality=100)
                except Exception as e:
                    logging.error(f'Erro ao redimensionar {original_img_path}: {e}')
                    return False

    return True