from PIL import Image, ImageDraw, ImageFilter
import customtkinter as ctk

class AssetFactory:
    """Generates Premium UI Assets programmatically (Cyberpunk/Luxury Style)"""
    
    @staticmethod
    def create_gradient_header(width, height, color1, color2):
        base = Image.new('RGB', (width, height), color1)
        top = Image.new('RGB', (width, height), color2)
        mask = Image.new('L', (width, height))
        mask_data = []
        for y in range(height):
            mask_data.extend([int(255 * (y / height))] * width)
        mask.putdata(mask_data)
        base.paste(top, (0, 0), mask)
        return ctk.CTkImage(light_image=base, dark_image=base, size=(width, height))

    @staticmethod
    def get_icon_aim(size=(24, 24)):
        img = Image.new("RGBA", size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        # Crosshair with gap
        w, h = size
        cx, cy = w/2, h/2
        color = "#00ff88"
        
        # Outer Ring
        draw.ellipse((2, 2, w-3, h-3), outline="#ff3333", width=2)
        # Center Dot
        draw.ellipse((cx-2, cy-2, cx+2, cy+2), fill="#ff3333")
        # Hairs
        draw.line((cx-8, cy, cx-4, cy), fill="#ff3333", width=2)
        draw.line((cx+4, cy, cx+8, cy), fill="#ff3333", width=2)
        draw.line((cx, cy-8, cx, cy-4), fill="#ff3333", width=2)
        draw.line((cx, cy+4, cx, cy+8), fill="#ff3333", width=2)
        
        return ctk.CTkImage(light_image=img, dark_image=img, size=size)

    @staticmethod
    def get_icon_recoil(size=(24, 24)):
        img = Image.new("RGBA", size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        # Lightning Bolt
        points = [
            (14, 2), (6, 12), (11, 12),
            (9, 22), (18, 10), (13, 10)
        ]
        draw.polygon(points, fill="#ff3333")
        return ctk.CTkImage(light_image=img, dark_image=img, size=size)

    @staticmethod
    def get_icon_settings(size=(24, 24)):
        img = Image.new("RGBA", size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        # Gear
        w, h = size
        draw.ellipse((4, 4, w-5, h-5), outline="#888888", width=3)
        draw.ellipse((9, 9, w-10, h-10), outline="#888888", width=1)
        # Teeth (Simplified)
        for i in range(0, 360, 45):
            draw.line((w/2, h/2, w/2 + 10, h/2), fill="#888888", width=4)
        
        return ctk.CTkImage(light_image=img, dark_image=img, size=size)
        
    @staticmethod
    def get_logo(size=(40, 40)):
        img = Image.new("RGBA", size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        # Hexagon
        points = [
            (10, 0), (30, 0), (40, 20),
            (30, 40), (10, 40), (0, 20)
        ]
        draw.polygon(points, fill="#111111", outline="#ff3333", width=2)
        # Inner 'L'
        draw.text((12, 8), "L", fill="#ffffff", font_size=24) # Fallback if font fails
        return ctk.CTkImage(light_image=img, dark_image=img, size=size)
