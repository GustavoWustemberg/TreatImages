import os
from PIL import Image
import logging
from Class.tools import functionalities


def converter(root_folder, type_image):
    for root, dirs, files in os.walk(root_folder):
        for file in files:
            filename, extension = os.path.splitext(file)
            if functionalities.is_image(extension):
                new_imgName = filename + "." + type_image
                original_img_path = os.path.join(root, file)
                new_img_path = os.path.join(root, new_imgName)
                try:
                    pillow_img = Image.open(original_img_path)
                    new_img = pillow_img
                    if pillow_img.mode == "RGBA" and type_image == "jpg":
                        new_img = pillow_img.convert("RGB")
                    new_img.save(new_img_path, optmize=True, quality=60)
                    new_img.save(new_img_path, format=type_image)
                    type_image_completed = "." + type_image
                    if extension != type_image_completed:
                        os.remove(original_img_path)
                except Exception as e:
                    logging.error(f'Erro ao converter {original_img_path}: {e}')
