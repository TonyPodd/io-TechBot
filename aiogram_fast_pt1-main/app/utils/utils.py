from PIL import Image
import io
import qrcode
import tempfile
import subprocess
import os
from pyzbar.pyzbar import decode

def image_to_blob(image_path):
    with open(image_path, "rb") as f:
        image_data = f.read()
    return image_data


def blob_to_image(image_blob):
    image_stream = io.BytesIO(image_blob)
    image = Image.open(image_stream)
    return image



def scan_qr_code(image_path):
    # Открываем изображение
    with Image.open(image_path) as img:
        # Декодируем QR-коды на изображении
        decoded_objects = decode(img)
        
        # Проверяем, найдены ли какие-либо объекты
        if decoded_objects:
            # Возвращаем первый найденный QR-код
            return decoded_objects[0].data.decode('utf-8')
        else:
            return None

def generate_qr_code(id: int, bonus_points: int, file_path: str):
    data = f"ID: {id}\nBonus points: {bonus_points}"
    qr = qrcode.make(data)
    qr.save(file_path)
    
# def scan_qr_code(img):
    

if __name__ == "__main__":
    # generate_qr_code(13456, 100, "qr_code.png")
    print(scan_qr_code('mat.jpg'))
