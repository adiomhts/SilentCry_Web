from PIL import Image
import os

input_dir = 'gallery'
output_dir = 'gallery/thumbs'
os.makedirs(output_dir, exist_ok=True)

for filename in os.listdir(input_dir):
    if filename.lower().endswith('.webp'):
        input_path = os.path.join(input_dir, filename)
        output_path = os.path.join(output_dir, filename)

        with Image.open(input_path) as img:
            img = img.convert('RGB')
            img.thumbnail((800, 800), Image.LANCZOS)  # просто вписываем по большей стороне
            img.save(output_path, 'WEBP')
            print(f"Saved: {output_path}")
