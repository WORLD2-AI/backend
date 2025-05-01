from app import proecess_character_born

result = proecess_character_born.delay({"id":1})
print(result)