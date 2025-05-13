import string
import random

def generate_unique_id(self):
        characters = string.ascii_letters + string.digits
        return ''.join(random.choices(characters, k=8))
