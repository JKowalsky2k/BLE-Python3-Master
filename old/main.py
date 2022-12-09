from cryptography.fernet import Fernet

key = b"Jb67fINfZT3H9x_cE6SoNx-VxqDm3wix9EhPokCI1Uk="
print(f"{key = }")
data = "8450eca01665516d9aeb5317764902b78495502637c96192c81b1683d32d691a0965cf037feca8b9ed9ee6fc6ab8f27fce8f77c4fd9b4a442a00fc317b8237e6".encode()

f = Fernet(key)
en_data = f.encrypt(data)
print(f"{en_data.decode() = }")

de_data = f.decrypt(en_data)
print(f"{de_data.decode() = }")

# key = Fernet.generate_key()
# print(f'{key = }')
# with open("key.key", "wb") as key_file:
#     key_file.write(key)