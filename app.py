import logging
from Class.initializer import initializer

logging.basicConfig(filename='conversion_errors.log', level=logging.ERROR)
x = 0

while x < 5:
    x = int(input('Selecione uma das opções abaixo:\n'
                  '1 - Redimensionar Imagens\n'
                  '2 - Comprimir Imagens\n'
                  '3 - Converter Imagens\n'
                  '4 - Remover Fundo das Imagens\n'
                  '5 - Sair\n'))
    if not x > 4:
        root_folder = input('Digite o caminho onde estão as imagens: ')

        init = initializer(root_folder, None, None, None)
        init.options(x)