#!/bin/bash
# Script de instalação para Svxlink Monitor Display na OrangePi Zero LTS com Debian 12 Armbian

echo "Bloqueando atualizações do PHP8.3, evitando problemas com o SVXLink-Dashboard quando instalado..."
sudo apt-mark hold libapache2-mod-php libapache2-mod-php8.3 php php-bcmath php-cli php-common php-curl php-gd php-gmp php-mbstring php-mysql php-pear php-xml php-zip php8.3 php8.3-bcmath php8.3-cli php8.3-common php8.3-curl php8.3-gd php8.3-gmp php8.3-mbstring php8.3-mysql php8.3-opcache php8.3-readline php8.3-xml php8.3-zip

# Verifica se é root
if [ "$(id -u)" -ne 0 ]; then
  echo "Este script deve ser executado como root" >&2
  exit 1
fi

echo "=== Instalando Svxlink Monitor Display ==="

# 1. Atualizar sistema e instalar dependências
echo "Instalando dependências..."
apt update
apt install -y python3-pip python3-dev python3-venv i2c-tools git

# 2. Habilitar I2C-0
echo "Configurando I2C..."
if ! grep -q "i2c0" /boot/armbianEnv.txt; then
  echo "overlays=i2c0" >> /boot/armbianEnv.txt
  echo "param_i2c0_enable=1" >> /boot/armbianEnv.txt
  echo "i2c0" >> /etc/modules
fi

# 3. Instalar pacotes Python no ambiente virtual
echo "Criando ambiente virtual..."
python3 -m venv /opt/svxlink_display
source /opt/svxlink_display/bin/activate

echo "Instalando pacotes Python..."
pip install --upgrade pip
pip install luma.oled psutil pillow

# 4. Baixar fontes (se não existirem)
echo "Configurando fontes..."
FONT_AWESOME="/root/fa-solid-900.ttf"
PIXEL_OPERATOR="/root/PixelOperator.ttf"
DEJAVUSANS="/root/DejaVuSans.ttf"

if [ ! -f "$FONT_AWESOME" ]; then
  echo "Baixando Font Awesome..."
  wget -O "$FONT_AWESOME" https://github.com/miranildo/Svxlink_Monitor-OrangePi-ZERO-LTS/raw/refs/heads/main/fa-solid-900.ttf
fi

if [ ! -f "$PIXEL_OPERATOR" ]; then
  echo "Baixando Pixel Operator..."
  wget -O "$PIXEL_OPERATOR" https://github.com/miranildo/Svxlink_Monitor-OrangePi-ZERO-LTS/raw/refs/heads/main/PixelOperator.ttf
fi

if [ ! -f "$DEJAVUSANS" ]; then
  echo "Baixando Fonte DejavuSans..."
  wget -O "$DEJAVUSANS" https://github.com/miranildo/Svxlink_Monitor-OrangePi-ZERO-LTS/raw/refs/heads/main/DejaVuSans.ttf
fi

# 5. Baixar o script do display
echo "Instalando script do display..."
SCRIPT_URL="https://github.com/miranildo/Svxlink_Monitor-OrangePi-ZERO-LTS/raw/refs/heads/main/Svxlink_Monitor.py"
SCRIPT_PATH="/opt/svxlink_display/Svxlink_Monitor.py"

wget -O "$SCRIPT_PATH" "$SCRIPT_URL"
chmod +x "$SCRIPT_PATH"

# 6. Criar serviço systemd
echo "Criando serviço systemd..."
SERVICE_FILE="/etc/systemd/system/svxlink_monitor.service"

cat > "$SERVICE_FILE" <<EOL
[Unit]
Description=Svxlink Monitor Display Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/svxlink_display
ExecStart=/opt/svxlink_display/bin/python /opt/svxlink_display/Svxlink_Monitor.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOL

# 7. Recarregar e ativar serviço
systemctl daemon-reload
systemctl enable svxlink_monitor.service
systemctl start svxlink_monitor.service

echo "Configurando permissões..."
chown -R root:root /opt/svxlink_display
chmod 644 /root/fa-solid-900.ttf /root/PixelOperator.ttf /root/DejaVuSans.ttf

# 8. Verificar instalação
echo "Verificando instalação..."
if systemctl is-active --quiet svxlink_monitor.service; then
  echo -e "\n\033[32mInstalação concluída com sucesso!\033[0m"
  echo "O serviço está rodando: systemctl status svxlink_monitor.service"
else
  echo -e "\n\033[31mErro: O serviço não está rodando\033[0m"
  echo "Verifique com: journalctl -u svxlink_monitor.service -b"
fi

echo "=== Instalação Finalizada ==="
