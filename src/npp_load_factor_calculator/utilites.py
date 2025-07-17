import os


def get_full_filename(folder, startswith):
    for file in os.listdir(folder):
        if file.startswith(startswith):
            return file
    return None


def get_number(number):
    if number < 10:
        return f"0{number}"
    else:
        return str(number)
    
    
def get_next_number_file_name(folder):
    files = os.listdir(folder)
    files = [file for file in files if file.endswith(".oemof")]
    if not files:
        return 0
    number_files = [int(file.split("_")[0]) for file in files]
    res = max(number_files) + 1
    return res


