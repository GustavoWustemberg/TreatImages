from Functions.converter import converter
from Functions.resize import resize
from Functions.compact import compact
from Functions.removeBG import removeBG
import questionary

optionsConvertion = ['jpg', 'jpeg', 'png', 'webp']
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
            selected_option = questionary.select(
                'Selecione uma das opções abaixo:',
                choices=optionsConvertion
            ).ask()

            self.type_image = selected_option
            converter(self.root_folder, self.type_image)
        elif x == 4:
            removeBG(self.root_folder)
