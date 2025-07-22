#!/usr/bin/env python3
import time
import psutil
import subprocess
from PIL import Image, ImageDraw, ImageFont
import os
import socket
from luma.core.interface.serial import i2c
from luma.oled.device import ssd1306

# Configuração do display OLED
WIDTH = 128
HEIGHT = 64

# Inicialização do display com luma.oled (I2C porta 0)
try:
    serial = i2c(port=0, address=0x3C)
    oled = ssd1306(serial, width=WIDTH, height=HEIGHT)
except Exception as e:
    print(f"Erro ao inicializar display OLED: {e}")
    exit(1)

# Criação de uma imagem para desenhar no display
image = Image.new("1", (oled.width, oled.height))
draw = ImageDraw.Draw(image)

# Carregar as fontes originais (ajuste os caminhos se necessário)
try:
    icon_font = ImageFont.truetype("/opt/svxlink_display/fa-solid-900.ttf", 12)
    font = ImageFont.truetype("/opt/svxlink_display/PixelOperator.ttf", 16)
except Exception as e:
    print(f"Erro ao carregar fontes: {e}")
    # Fallback para fontes padrão se necessário
    icon_font = ImageFont.load_default()
    font = ImageFont.load_default()

# Códigos Unicode dos ícones FontAwesome (mantido original)
unicode_icons = {
    "processor": "\uf2db",  # CPU
    "thermometer": "\uf2c8",  # Temperatura
    "wifi": "\uf1eb",  # Wi-Fi/IP
    "tx": "\uf7c0",  # Transmitir
    "rx": "\uf519",  # Receber
    "microphone": "\uf130",  # Microfone
    "antenna": "\uf0c1"  # Antena
}

def get_ip_address():
    """Obtém o endereço IP local (mantido original)"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
    except Exception as e:
        ip = f"Erro IP: {e}"
    return ip

def get_cpu_temperature():
    """Obtém a temperatura da CPU (mantido original)"""
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            temp = int(f.read()) / 1000.0
        return f"{temp:.1f}°C"
    except FileNotFoundError:
        return "N/D"

def update_oled(info_lines, tx_active, rx_active):
    """Atualiza o display OLED (adaptado para luma.oled)"""
    # Cria nova imagem a cada atualização
    image = Image.new("1", (oled.width, oled.height))
    draw = ImageDraw.Draw(image)
    
    # Cabeçalho (mantido original)
    draw.rectangle((0, 0, oled.width, 15), fill=1)
    draw.text((oled.width // 2 - 30, 0), "PR7MLS-L", font=font, fill=0)
    
    # Informações do sistema (mantido original)
    draw.text((5, 20), unicode_icons["wifi"], font=icon_font, fill=255)
    draw.text((25, 20), info_lines['ip'], font=font, fill=255)
    
    draw.text((5, 35), unicode_icons["processor"], font=icon_font, fill=255)
    draw.text((25, 35), f"{info_lines['cpu']}%", font=font, fill=255)
    
    draw.text((70, 35), unicode_icons["thermometer"], font=icon_font, fill=255)
    draw.text((90, 35), info_lines['temp'], font=font, fill=255)

    # Status TX/RX (mantido original)
    tx_box = (5, 50, 60, 64)
    rx_box = (65, 50, 125, 64)
    
    draw.rectangle(tx_box, outline=1, fill=1 if tx_active else 0)
    draw.text((15, 52), unicode_icons["tx"], font=icon_font, fill=0 if tx_active else 255)
    draw.text((30, 50), "TX", font=font, fill=0 if tx_active else 255)

    draw.rectangle(rx_box, outline=1, fill=1 if rx_active else 0)
    draw.text((75, 50), unicode_icons["rx"], font=icon_font, fill=0 if rx_active else 255)
    draw.text((92, 50), "RX", font=font, fill=0 if rx_active else 255)

    # Atualiza o display (usando luma.oled)
    oled.display(image)

def monitor_svxlink_log():
    """Monitora o log do SVXLink (mantido original)"""
    log_file = "/var/log/svxlink.log"
    if not os.path.exists(log_file):
        print("Log não encontrado")
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
                    except IndexError:
                        conference = "Erro na captura"
                
                if "->" in line:
                    speaker = line.split("->")[1].strip()

                if "Turning the transmitter ON" in line:
                    current_status = "Transmissao ativa"
                elif "Turning the transmitter OFF" in line:
                    current_status = "Livre para Recepcao"
                    
    except Exception as e:
        conference = "Erro Log"
        speaker = f"Erro Log: {e}"
    
    return conference, speaker, current_status

def main():
    """Função principal (adaptada para limpar display ao sair)"""
    screen_toggle = False
    try:
        while True:
            # Informações do sistema
            info = {
                'ip': get_ip_address(),
                'cpu': psutil.cpu_percent(),
                'temp': get_cpu_temperature()
            }
            
            # Monitoramento do SVXLink
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
                
                # Cabeçalho
                draw.rectangle((0, 0, oled.width, 15), fill=1)
                draw.text((oled.width // 2 - 30, 0), "PR7MLS-L", font=font, fill=0)

                # Ícones e textos
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
        # Limpa o display ao sair
        oled.clear()
        oled.display()
        print("\nDisplay limpo e programa encerrado.")

if __name__ == "__main__":
    main()
