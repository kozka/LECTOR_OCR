import tkinter as tk
from PIL import ImageGrab, ImageTk
import pytesseract
import edge_tts
import pygame
import asyncio
import keyboard
import os
import sys
import configparser
import winsound
import threading
import ctypes

# --- 1. CONFIGURACIÓN DE RUTAS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PATH_TESSERACT = os.path.join(BASE_DIR, "Tesseract-OCR", "tesseract.exe")
PATH_CONFIG = os.path.join(BASE_DIR, 'config.txt')
OUTPUT_AUDIO = os.path.join(BASE_DIR, "temp_lectura.mp3")

if os.path.exists(PATH_TESSERACT):
    pytesseract.pytesseract.tesseract_cmd = PATH_TESSERACT

# --- 2. CONFIGURACIÓN ---
config = configparser.ConfigParser(interpolation=None)
if not os.path.exists(PATH_CONFIG):
    config['AUDIO'] = {'VOZ': 'es-ES-AlvaroNeural', 'VELOCIDAD': '+0%'}
    with open(PATH_CONFIG, 'w') as f: config.write(f)
else:
    config.read(PATH_CONFIG, encoding='utf-8')

VOICE = config.get('AUDIO', 'VOZ', fallback='es-ES-AlvaroNeural')
RATE = config.get('AUDIO', 'VELOCIDAD', fallback='+0%')

# --- 3. HERRAMIENTA DE RECORTE ---
class SnippingTool:
    def __init__(self, master_screenshot, game_hwnd):
        self.root = tk.Tk()
        self.root.attributes("-fullscreen", True)
        self.root.attributes("-topmost", True)
        self.root.configure(background='black')
        
        # Guardamos la ID de la ventana del juego para volver luego
        self.game_hwnd = game_hwnd
        
        self.screenshot = master_screenshot
        self.tk_image = ImageTk.PhotoImage(self.screenshot)
        
        self.canvas = tk.Canvas(self.root, cursor="cross", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.create_image(0, 0, image=self.tk_image, anchor="nw")
        
        # Efecto de oscurecimiento
        self.rect_dim = self.canvas.create_rectangle(0, 0, self.screenshot.width, self.screenshot.height, fill="black", stipple="gray50")

        self.start_x = 0
        self.start_y = 0
        self.current_rect = None
        
        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_move_press)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)
        self.root.bind("<Escape>", lambda e: self.root.destroy())
        
        self.cropped_image = None
        self.root.focus_force()

    def on_button_press(self, event):
        self.start_x = event.x
        self.start_y = event.y
        if self.current_rect:
            self.canvas.delete(self.current_rect)
        self.current_rect = self.canvas.create_rectangle(self.start_x, self.start_y, 1, 1, outline='red', width=3)

    def on_move_press(self, event):
        self.canvas.coords(self.current_rect, self.start_x, self.start_y, event.x, event.y)

    def on_button_release(self, event):
        x1, y1 = min(self.start_x, event.x), min(self.start_y, event.y)
        x2, y2 = max(self.start_x, event.x), max(self.start_y, event.y)
        
        self.root.destroy()
        self.root.update() # Asegurar que se cierra visualmente
        
        # --- EL TRUCO DEL BOOMERANG ---
        # Devolvemos el foco al juego inmediatamente
        try:
            ctypes.windll.user32.SetForegroundWindow(self.game_hwnd)
        except Exception as e:
            print(f"No pude volver al juego: {e}")

        if (x2 - x1) > 10 and (y2 - y1) > 10:
            self.cropped_image = self.screenshot.crop((x1, y1, x2, y2))

    def run(self):
        self.root.mainloop()
        return self.cropped_image

# --- 4. AUDIO Y LÓGICA ---
async def hablar_async(texto):
    print(f" > Narrando...")
    try:
        communicate = edge_tts.Communicate(texto, VOICE, rate=RATE)
        await communicate.save(OUTPUT_AUDIO)
        
        pygame.mixer.init()
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()
            pygame.mixer.music.unload()
            
        pygame.mixer.music.load(OUTPUT_AUDIO)
        pygame.mixer.music.play()
        
        while pygame.mixer.music.get_busy():
            await asyncio.sleep(0.1)
        pygame.mixer.quit()
        try: os.remove(OUTPUT_AUDIO)
        except: pass
    except Exception as e:
        print(f"[ERROR AUDIO] {e}")

def ejecutar_proceso():
    # 1. IDENTIFICAR JUEGO (Obtener ID de la ventana activa ACTUAL)
    hwnd_juego = ctypes.windll.user32.GetForegroundWindow()
    
    winsound.Beep(700, 100) 
    
    # 2. CAPTURA
    try:
        full_screenshot = ImageGrab.grab(all_screens=True)
    except Exception as e:
        print(f"Error captura: {e}")
        return

    # 3. SELECTOR (Le pasamos la ID del juego para que sepa dónde volver)
    tool = SnippingTool(full_screenshot, hwnd_juego)
    imagen_recortada = tool.run()
    
    if imagen_recortada:
        winsound.Beep(1000, 50)
        
        # 4. LEER
        try:
            custom_oem = r'--oem 3 --psm 6' 
            texto = pytesseract.image_to_string(imagen_recortada, lang='spa', config=custom_oem)
            texto = texto.replace("\n", " ").replace("|", "")
            
            if len(texto.strip()) > 1:
                # Usamos threading para no bloquear el teclado mientras habla
                # Esto es importante para seguir jugando
                threading.Thread(target=lambda: asyncio.run(hablar_async(texto))).start()
            else:
                winsound.Beep(200, 200)
        except Exception as e:
            print(f"[ERROR OCR] {e}")

def main():
    print("="*50)
    print(" SISTEMA EGG V4")
    print("="*50)
    print(f" [OK] Tesseract: Detectado")
    print(" [LISTO] Pulsa 'Control + Q' en el juego.")
    print("="*50)
    
    keyboard.add_hotkey('ctrl+q', ejecutar_proceso)
    keyboard.wait()

if __name__ == "__main__":
    main()