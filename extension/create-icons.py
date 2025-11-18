#!/usr/bin/env python3
"""
Simple script to create placeholder icons for the Chrome extension.
Run: python create-icons.py
"""
from PIL import Image, ImageDraw, ImageFont
import os

def create_icon(size, filename):
    """Create a simple icon with gradient background and text"""
    # Create image with gradient purple background
    img = Image.new('RGB', (size, size), color='#7c3aed')
    draw = ImageDraw.Draw(img)
    
    # Add gradient effect (simple version)
    for y in range(size):
        brightness = int(124 + (y / size) * 40)  # 124 to 164
        color = (brightness, 58, 237)
        draw.line([(0, y), (size, y)], fill=color)
    
    # Add white circle in center
    circle_radius = int(size * 0.35)
    center = size // 2
    draw.ellipse(
        [(center - circle_radius, center - circle_radius),
         (center + circle_radius, center + circle_radius)],
        fill='white'
    )
    
    # Add "AI" text in center
    try:
        # Try to use a nice font
        font_size = int(size * 0.4)
        font = ImageFont.truetype("arial.ttf", font_size)
    except:
        # Fallback to default font
        font = ImageFont.load_default()
    
    text = "AI"
    # Get text bounding box
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    # Center text
    text_x = (size - text_width) // 2
    text_y = (size - text_height) // 2 - int(size * 0.05)  # Slight adjustment
    
    draw.text((text_x, text_y), text, fill='#7c3aed', font=font)
    
    # Save
    img.save(filename, 'PNG')
    print(f"Created {filename}")

def main():
    """Create all required icon sizes"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    sizes = [16, 48, 128]
    for size in sizes:
        filename = os.path.join(script_dir, f'icon{size}.png')
        create_icon(size, filename)
    
    print("\n✅ All icons created successfully!")
    print("You can now load the extension in Chrome.")

if __name__ == '__main__':
    try:
        main()
    except ImportError:
        print("❌ Error: PIL (Pillow) is required to create icons.")
        print("Install it with: pip install Pillow")
        print("\nOr create icons manually and save as:")
        print("  - icon16.png (16x16)")
        print("  - icon48.png (48x48)")
        print("  - icon128.png (128x128)")


