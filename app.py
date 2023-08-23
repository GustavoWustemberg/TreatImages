import logging
from Class.initializer import initializer
import questionary

logging.basicConfig(filename='conversion_errors.log', level=logging.ERROR)

options = [
    'Redimensionar Imagens',
    'Comprimir Imagens',
    'Converter Imagens',
    'Remover Fundo das Imagens',
    'Sair'
]

while True:
    selected_option = questionary.select(
        'Selecione uma das opções abaixo:',
        choices=options
    ).ask()

    if selected_option == 'Sair':
        break

    if selected_option != 'Remover Fundo das Imagens':
        root_folder = input('Digite o caminho onde estão as imagens: ')
        init = initializer(root_folder, None, None, None)
        if selected_option == 'Redimensionar Imagens':
            init.options(1)
        elif selected_option == 'Comprimir Imagens':
            init.options(2)
        elif selected_option == 'Converter Imagens':
            init.options(3)
    else:
        init = initializer(None, None, None, None)
        init.options(4)
