from os import path

def file_to_string(filename):
	base_path = path.dirname(__file__)
	file_path = path.join(base_path, filename)
	with open(file_path, 'r') as file:
		return file.read()
