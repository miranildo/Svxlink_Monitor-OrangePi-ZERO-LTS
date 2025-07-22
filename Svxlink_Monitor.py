#!/usr/bin/env python3
import time
import psutil
import subprocess
from PIL import Image, ImageDraw, ImageFont
import os
import socket
from luma.core.interface.serial import i2c
from luma.oled.device import ssd1306

# Configurações do display
WIDTH = 128
HEIGHT = 64
I2C_PORT = 0  # Porta I2C 0 para OrangePi Zero
I2C_ADDRESS = 0x3C

# Caminhos das fontes (ajuste conforme necessário)
FONT_AWESOME_PATH = "/root/fa-solid-900.ttf"
PIXEL_OPERATOR_PATH = "/root/PixelOperator.ttf"

# Inicialização do display
try:
    serial = i2c(port=I2C_PORT, address=I2C_ADDRESS)
    oled = ssd1306(serial, width=WIDTH, height=HEIGHT)
except Exception as e:
    print(f"Erro ao inicializar display: {e}")
    exit(1)

# Carregamento das fontes
try:
    icon_font = ImageFont.truetype(FONT_AWESOME_PATH, 12)
    font = ImageFont.truetype(PIXEL_OPERATOR_PATH, 16)
except Exception as e:
    print(f"Erro ao carregar fontes: {e}")
    print("Usando fontes padrão como fallback")
    icon_font = ImageFont.load_default()
    font = ImageFont.load_default()

# Códigos Unicode dos ícones FontAwesome
unicode_icons = {
    "processor": "\uf2db",  # CPU
    "thermometer": "\uf2c8",  # Temperatura
    "wifi": "\uf1eb",  # Wi-Fi/IP
    "tx": "\uf7c0",  # Transmitir
    "rx": "\uf519",  # Receber
    "microphone": "\uf130",  # Microfone
    "antenna": "\uf0c1"  # Antena
}

# [Mantenha todas as outras funções exatamente como estão no script original:
# get_ip_address(), get_cpu_temperature(), update_oled(), monitor_svxlink_log(), main()]

def get_ip_address():
    """Obtém o endereço IP local"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        try:
            return subprocess.check_output(['hostname', '-I']).decode().split()[0]
        except:
            return "Sem IP"

def get_cpu_temperature():
    """Obtém a temperatura da CPU"""
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            temp = int(f.read()) / 1000.0
            return f"{temp:.1f}°C"
    except Exception:
        return "N/D"

def update_oled(info_lines, tx_active, rx_active):
    """Atualiza o display OLED com as informações"""
    image = Image.new("1", (oled.width, oled.height))
    draw = ImageDraw.Draw(image)
    
    # Cabeçalho
    draw.rectangle((0, 0, oled.width, 15), fill=1)
    draw.text((oled.width // 2 - 30, 0), "PR7MLS-L", font=font, fill=0)
    
    # Informações do sistema
    draw.text((5, 20), unicode_icons["wifi"], font=icon_font, fill=255)
    draw.text((25, 20), info_lines['ip'], font=font, fill=255)
    
    draw.text((5, 35), unicode_icons["processor"], font=icon_font, fill=255)
    draw.text((25, 35), f"{info_lines['cpu']}%", font=font, fill=255)
    
    draw.text((70, 35), unicode_icons["thermometer"], font=icon_font, fill=255)
    draw.text((90, 35), info_lines['temp'], font=font, fill=255)

    # Status TX/RX
    tx_box = (5, 50, 60, 64)
    rx_box = (65, 50, 125, 64)
    
    draw.rectangle(tx_box, outline=1, fill=1 if tx_active else 0)
    draw.text((15, 52), unicode_icons["tx"], font=icon_font, fill=0 if tx_active else 255)
    draw.text((30, 50), "TX", font=font, fill=0 if tx_active else 255)

    draw.rectangle(rx_box, outline=1, fill=1 if rx_active else 0)
    draw.text((75, 50), unicode_icons["rx"], font=icon_font, fill=0 if rx_active else 255)
    draw.text((92, 50), "RX", font=font, fill=0 if rx_active else 255)

    oled.display(image)

def monitor_svxlink_log():
    """Monitora o log do SVXLink para obter status"""
    log_files = [
        "/var/log/svxlink.log",
        "/var/log/svxlink/svxlink.log"
    ]
    
    log_file = None
    for lf in log_files:
        if os.path.exists(lf):
            log_file = lf
            break
    
    if not log_file:
        return "EM ESPERA...", "LIVRE", "Livre para Recepcao"
    
    conference = "EM ESPERA..."
    speaker = "LIVRE"
    current_status = "Livre para Recepcao"
    
    try:
        with subprocess.Popen(['tail', '-n', '20', log_file], 
                            stdout=subprocess.PIPE, 
                            stderr=subprocess.PIPE, 
                            text=True, 
                            errors='ignore') as log:
            for line in log.stdout:
                if "EchoLink chat message received from" in line:
                    try:
                        conference = line.split("from")[1].split("---")[0].strip()
                    except:
                        conference = "Conferencia"
                
                if "->" in line:
                    speaker = line.split("->")[1].strip()

                if "Turning the transmitter ON" in line:
                    current_status = "Transmissao ativa"
                elif "Turning the transmitter OFF" in line:
                    current_status = "Livre para Recepcao"
                    
    except Exception as e:
        conference = f"Erro: {str(e)}"
        speaker = "Erro Log"
    
    return conference, speaker, current_status

def main():
    screen_toggle = False
    try:
        while True:
            # Coleta informações do sistema
            info = {
                'ip': get_ip_address(),
                'cpu': psutil.cpu_percent(),
                'temp': get_cpu_temperature()
            }
            
            # Monitora status do SVXLink
            conference, speaker, rx_tx_status = monitor_svxlink_log()
            tx_active = rx_tx_status == "Transmissao ativa"
            rx_active = rx_tx_status == "Livre para Recepcao"
            
            if screen_toggle:
                # Tela 1: Informações do sistema
                update_oled(info, tx_active, rx_active)
            else:
                # Tela 2: Informações do SVXLink
                image = Image.new("1", (oled.width, oled.height))
                draw = ImageDraw.Draw(image)
                
                draw.rectangle((0, 0, oled.width, 15), fill=1)
                draw.text((oled.width // 2 - 30, 0), "PR7MLS-L", font=font, fill=0)
                
                draw.text((5, 20), unicode_icons["antenna"], font=icon_font, fill=255)
                draw.text((25, 20), conference, font=font, fill=255)
                
                draw.text((5, 35), unicode_icons["microphone"], font=icon_font, fill=255)
                draw.text((19, 35), speaker, font=font, fill=255)
                
                # Status TX/RX
                tx_box = (5, 50, 60, 64)
                rx_box = (65, 50, 125, 64)
                
                draw.rectangle(tx_box, outline=1, fill=1 if tx_active else 0)
                draw.text((15, 52), unicode_icons["tx"], font=icon_font, fill=0 if tx_active else 255)
                draw.text((30, 50), "TX", font=font, fill=0 if tx_active else 255)

                draw.rectangle(rx_box, outline=1, fill=1 if rx_active else 0)
                draw.text((75, 50), unicode_icons["rx"], font=icon_font, fill=0 if rx_active else 255)
                draw.text((92, 50), "RX", font=font, fill=0 if rx_active else 255)

                oled.display(image)

            screen_toggle = not screen_toggle
            time.sleep(5)

    except KeyboardInterrupt:
        oled.clear()
        oled.display()
        print("\nDisplay limpo e programa encerrado.")

if __name__ == "__main__":
    main()