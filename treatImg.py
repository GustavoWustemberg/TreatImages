import os
import re
from PIL import Image
from tqdm import tqdm

x = 0
value = 0

def calc_new_height(width, hegth, new_width):
    return round(new_width * hegth / width)

def is_image(extension):
    extension_lowercase = extension.lower()
    return bool(re.search(r'^\.(jpe?g|png|webp)$', extension_lowercase))

def resize(root_folder, new_width):
    for root, dirs, files in os.walk(root_folder):
        for file in tqdm(files):
            filename, extension = os.path.splitext(file)
            if is_image(extension):
                new_imgName = filename + extension
                original_img_path = os.path.join(root, file)
                new_img_path = os.path.join(root, new_imgName)
                pillow_img = Image.open(original_img_path)
                width, height = pillow_img.size

                new_height = calc_new_height(width, height, new_width)

                new_img = pillow_img.resize((new_width, new_height))
                new_img.save(new_img_path, optmize=True, quality=100)

def compact(root_folder, value_quality):
    for root, dirs, files in os.walk(root_folder):
        for file in tqdm(files):
            filename, extension = os.path.splitext(file)
            if is_image(extension):
                new_imgName = filename + extension
                original_img_path = os.path.join(root, file)
                new_img_path = os.path.join(root, new_imgName)
                pillow_img = Image.open(original_img_path)

                new_img = pillow_img
                new_img.save(new_img_path, optmize=True, quality=value_quality)

def converter(root_folder, type_image):
    for root, dirs, files in os.walk(root_folder):
        for file in tqdm(files):
            filename, extension = os.path.splitext(file)
            if is_image(extension):
                new_imgName = filename + "." + type_image
                original_img_path = os.path.join(root, file)
                new_img_path = os.path.join(root, new_imgName)
                pillow_img = Image.open(original_img_path)

                new_img = pillow_img
                new_img.save(new_img_path, optmize=True, quality=60)
                new_img.save(new_img_path, format=type_image)

            if is_image(extension):
                if extension != type_image:
                    os.remove(original_img_path)

while x < 4:
    x = int(input('Selecione uma das opções abaixo:\n'
                  '1 - Redimencionar Imagens\n'
                  '2 - Comprimir Imagens\n'
                  '3 - Converter Imagens\n'
                  '4 - Sair\n'))


    def main(root_folder, new_width = 0, value_quality = 0, type_image = ''):
        if x == 1:
            resize(root_folder, new_width)
        elif x == 2:
            compact(root_folder, value_quality)
        elif x == 3:
            converter(root_folder, type_image)

    if x == 1 and __name__ == '__main__':
        root_folder = input('Digite o caminho onde estão as imagens: ')
        new_width = int(input('Digite o valor da largura desejada: '))
        main(root_folder = root_folder, new_width = new_width, value_quality = 0, type_image = '')

    if x == 2 and __name__ == "__main__":
        root_folder = input('Digite o caminho onde estão as imagens: ')
        value_quality = int(input('Digite o valor entre 0 a 100 da porcentagem de perca de qualidade desejada: '))
        main(root_folder = root_folder, new_width = 0, value_quality = value_quality, type_image = '')

    if x == 3 and __name__ == "__main__":
        root_folder = input('Digite o caminho onde estão as imagens: ')
        type_image = input('Tipos de Imagens: JPG, JPEG, PNG, WEBP\n'
                           'Digite um dos tipos citados acima para converter as imagens: ').lower()
        main(root_folder = root_folder, new_width = 0, value_quality = 0, type_image = type_image)
