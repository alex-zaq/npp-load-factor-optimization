from pathlib import Path

from openpyxl import Workbook
from openpyxl.drawing.image import Image
from openpyxl.utils import get_column_letter

output_file = Path("./experimental_models/image_to_excel/11.xlsx")
image_path = Path("./experimental_models/image_to_excel/11.jpg")

def insert_image_to_excel(image_path, output_file):
    """
    Создает новый файл Excel и вставляет изображение, привязанное к ячейке A1.
    """
    # 1. Создание рабочей книги и листа
    wb = Workbook()
    ws = wb.active
    ws.title = "Отчет с логотипом"

    # Добавляем какой-то контент для наглядности

    # 2. Загрузка изображения

    
    
    try:
        img = Image(image_path)
    except FileNotFoundError:
        print(f"Ошибка: Файл изображения не найден по пути {image_path}")
        return

    # 3. Привязка и добавление
    # 'A2' - это ячейка, к которой будет привязан верхний левый угол изображения (якорь)
    img.anchor = 'A2' 
    
    # Опционально: можно изменить размер изображения
    # img.width = 150
    # img.height = 75

    ws.add_image(img)

    # 4. Сохранение файла
    try:
        wb.save(output_file)
        print(f"✅ Файл успешно создан: {output_file}")
    except Exception as e:
        print(f"❌ Ошибка при сохранении файла: {e}")


insert_image_to_excel(image_path, output_file)