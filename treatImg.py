import os
import re
from PIL import Image

x = 0

def calc_new_height(width, hegth, new_width):
    return round(new_width * hegth / width)


def is_image(extension):
    extension_lowercase = extension.lower()
    return bool(re.search(r'^\.(jpe?g|png|webp)$', extension_lowercase))

while x < 4:
    x = int(input('Selecione uma das opções abaixo:\n'
                  '1 - Redimencionar Imagens\n'
                  '2 - Comprimir Imagens\n'
                  '3 - Converter Imagens\n'
                  '4 - Sair\n'))
    if x == 1:
        def main(root_folder, new_width):
            for root, dirs, files in os.walk(root_folder):
                for file in files:
                    filename, extension = os.path.splitext(file)
                    if not is_image(extension):
                        return

                    new_imgName = filename + extension

                    original_img_path = os.path.join(root, file)
                    new_img_path = os.path.join(root, new_imgName)

                    pillow_img = Image.open(original_img_path)
                    width, height = pillow_img.size

                    new_height = calc_new_height(width, height, new_width)

                    new_img = pillow_img.resize((new_width, new_height))
                    new_img.save(new_img_path, optmize=True, quality=100)

                    print(f'A imagem {new_imgName} foi redimencionada com sucesso!')


        if __name__ == '__main__':
            root_folder = input('Digite o caminho onde estão as imagens: ')
            new_width = int(input('Digite o valor da largura desejada: '))
            main(root_folder, new_width)

    elif x == 2:
        def main(root_folder, value_quality):
            for root, dirs, files in os.walk(root_folder):
                for file in files:
                    filename, extension = os.path.splitext(file)
                    if is_image(extension):
                        new_imgName = filename + extension
                        original_img_path = os.path.join(root, file)
                        new_img_path = os.path.join(root, new_imgName)

                    pillow_img = Image.open(original_img_path)

                    new_img = pillow_img
                    new_img.save(new_img_path, optmize=True, quality=value_quality)

                    print(f'A imagem {new_imgName} foi comprimida com sucesso!')


        if __name__ == "__main__":
            root_folder = input('Digite o caminho onde estão as imagens: ')
            value_quality = int(input('Digite o valor entre 0 a 100 da porcentagem de perca de qualidade desejada: '))
            main(root_folder, value_quality)

    elif x == 3:
        def main(root_folder, type_image):
            for root, dirs, files in os.walk(root_folder):
                for file in files:
                    filename, extension = os.path.splitext(file)
                    if is_image(extension):
                        new_imgName = filename + "." + type_image
                        original_img_path = os.path.join(root, file)
                        new_img_path = os.path.join(root, new_imgName)
                    pillow_img = Image.open(original_img_path)

                    new_img = pillow_img
                    new_img.save(new_img_path, optmize=True, quality=60)
                    new_img.save(new_img_path, format=type_image)

                    print(f'A imagem {new_imgName} foi convertida com sucesso!')


        if __name__ == "__main__":
            root_folder = input('Digite o caminho onde estão as imagens: ')
            type_image = input('Tipos de Imagens: JPG, JPEG, PNG, WEBP\n'
                                'Digite um dos tipos citados acima para converter as imagens: ').lower()
            main(root_folder, type_image)