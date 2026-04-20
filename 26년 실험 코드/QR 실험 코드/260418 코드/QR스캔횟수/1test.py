import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import qrcode
from qrcode.image.pil import PilImage

class QRCodeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("QR Code Generator with Fruit Image")
        
        self.label = tk.Label(root, text="Select a fruit image to generate QR code")
        self.label.pack(pady=10)
        
        self.select_button = tk.Button(root, text="Select Image", command=self.select_image)
        self.select_button.pack(pady=10)
        
        self.qr_label = tk.Label(root)
        self.qr_label.pack(pady=10)
        
        self.save_button = tk.Button(root, text="Save QR Code", command=self.save_qr_code)
        self.save_button.pack(pady=10)
        self.save_button.config(state=tk.DISABLED)
        
        self.selected_image = None
        self.qr_image = None

    def select_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.bmp;*.gif")])
        if file_path:
            self.selected_image = Image.open(file_path)
            self.generate_qr_code()

    def generate_qr_code(self):
        if self.selected_image:
            qr = qrcode.QRCode(
                version=4,
                error_correction=qrcode.constants.ERROR_CORRECT_H,
                box_size=5,
                border=4,
            )
            qr.add_data('https://iampm.synology.me/')
            qr.make(fit=True)
            
            self.qr_image = qr.make_image(fill_color="black", back_color="white").convert('RGB')
            pos = (((self.qr_image.size[1] - self.selected_image.size[1]) // 2))
            self.qr_image.paste(self.selected_image, pos)
            
            self.qr_tk_image = ImageTk.PhotoImage(self.qr_image)
            self.qr_label.config(image=self.qr_tk_image)
            self.save_button.config(state=tk.NORMAL)

    def save_qr_code(self):
        if self.qr_image:
            save_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png")])
            if save_path:
                self.qr_image.save(save_path)

if __name__ == "__main__":
    root = tk.Tk()
    app = QRCodeApp(root)
    root.mainloop()
