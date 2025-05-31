import os
from PIL import Image

# Path to the folder containing your images
input_folder = ''    # Folder with original images
output_folder = ''    # Folder where edited images will be saved

# Create output folder if it doesn't exist
os.makedirs(output_folder, exist_ok=True)

# Loop through each file in the input folder
for filename in os.listdir(input_folder):
    if filename.endswith(('.png', '.jpg', '.jpeg', '.webp')):  # Only image files
        img_path = os.path.join(input_folder, filename)
        img = Image.open(img_path)

        # Edit a pixel: set pixel at (5, 5) to dark red (200, 0, 0)
        img.putpixel((5, 5), (200, 0, 0))

        # # Optional: color a small 3x3 block
        # color = (255, 0, 0)  # Bright Red
        # for x in range(5, 8):
        #     for y in range(5, 8):
        #         img.putpixel((x, y), color)

        # Resize (shrink) the image to 1/3 of its original size
        new_size = (img.width // 3, img.height // 3)
        small_img = img.resize(new_size)

        # Save the edited and resized image
        output_path = os.path.join(output_folder, f'edited_{filename}')
        small_img.save(output_path)

        print(f"Processed {filename} → saved as {output_path}")

print("✅ All images processed successfully!")
