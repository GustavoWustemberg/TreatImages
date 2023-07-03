from Functions.converter import converter
from Functions.resize import resize
from Functions.compact import compact
from Functions.removeBG import removeBG

class initializer:
    def __init__(self, root_folder, new_width, value_quality, type_image):
        self.root_folder = root_folder
        self.new_width = new_width
        self.value_quality = value_quality
        self.type_image = type_image

    def options(self, x):
        if x == 1:
            self.new_width = int(input('Digite o valor da largura desejada: '))
            resize(self.root_folder, self.new_width)
        elif x == 2:
            self.value_quality = int(input('Digite o valor entre 0 a 100 da porcentagem de perca de qualidade desejada: '))
            compact(self.root_folder, self.value_quality)
        elif x == 3:
            self.type_image = input('Tipos de Imagens: JPG, JPEG, PNG, WEBP\n'
                       'Digite um dos tipos citados acima para converter as imagens: ').lower()
            converter(self.root_folder, self.type_image)
        elif x == 4:
            removeBG(self.root_folder)
