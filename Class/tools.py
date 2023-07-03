import re

class functionalities:
    def calc_new_height(width, hegth, new_width):
        return round(new_width * hegth / width)

    def is_image(extension):
        extension_lowercase = extension.lower()
        return bool(re.search(r'^\.(jpe?g|png|webp)$', extension_lowercase))