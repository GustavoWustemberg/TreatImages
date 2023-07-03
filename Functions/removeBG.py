from rembg import remove
import os
from PIL import Image
import logging
from Class.tools import functionalities

def removeBG(root_folder):
    for root, dirs, files in os.walk(root_folder):
        for file in files:
            filename, extension = os.path.splitext(file)
            if functionalities.is_image(extension):
                new_imgName = filename + extension
                original_img_path = os.path.join(root, file)
                new_img_path = os.path.join(root, new_imgName)
                try:
                    pillow_img = Image.open(original_img_path)
                    new_img = remove(pillow_img)
                    new_img.save(new_img_path, format='png')
                except Exception as e:
                    logging.error(f'Erro ao converter {original_img_path}: {e}')