#!/bin/bash
# Script de instalação completo para Svxlink Monitor Display na OrangePi Zero LTS Debian 12 Armbian

echo "Bloqueando atualizações do PHP8.3, evitando problemas com o SVXLink-Dashboard quando instalado..."
sudo apt-mark hold libapache2-mod-php libapache2-mod-php8.3 php php-bcmath php-cli php-common php-curl php-gd php-gmp php-mbstring php-mysql php-pear php-xml php-zip php8.3 php8.3-bcmath php8.3-cli php8.3-common php8.3-curl php8.3-gd php8.3-gmp php8.3-mbstring php8.3-mysql php8.3-opcache php8.3-readline php8.3-xml php8.3-zip

# Verifica se é root
if [ "$(id -u)" -ne 0 ]; then
  echo "Este script deve ser executado como root" >&2
  exit 1
fi

echo "=== Instalando Svxlink Monitor Display (versão completa) ==="

# 1. Atualizar sistema e instalar dependências COMPLETAS
echo "Instalando dependências do sistema..."
apt update
apt install -y \
    python3-pip python3-dev python3-venv \
    i2c-tools git \
    libjpeg-dev zlib1g-dev libfreetype6-dev \
    liblcms2-dev libopenjp2-7-dev libtiff5-dev \
    libwebp-dev libharfbuzz-dev libfribidi-dev \
    fonts-dejavu fonts-font-awesome

# 2. Habilitar I2C-0
echo "Configurando I2C..."
if ! grep -q "i2c0" /boot/armbianEnv.txt; then
  echo "overlays=i2c0" >> /boot/armbianEnv.txt
  echo "param_i2c0_enable=1" >> /boot/armbianEnv.txt
  echo "i2c0" >> /etc/modules
  echo "Necessária reinicialização para ativar I2C"
fi

# 3. Criar ambiente virtual
echo "Criando ambiente virtual em /opt/svxlink_display..."
python3 -m venv /opt/svxlink_display
source /opt/svxlink_display/bin/activate

# 4. Instalar pacotes Python com prioridade para wheels
echo "Instalando pacotes Python..."
export PACKAGES="luma.oled psutil pillow"

# Primeira tentativa com wheels pré-compilados
pip install --upgrade pip setuptools wheel
pip install --prefer-binary $PACKAGES

# Segunda tentativa (se falhar) com compilação local
if [ $? -ne 0 ]; then
  echo "Falha na instalação com wheels, tentando compilar localmente..."
  apt install -y build-essential python3-setuptools
  pip install --no-binary :all: $PACKAGES
fi

# 5. Configurar fontes
echo "Configurando fontes em /root..."
FONT_AWESOME="/root/fa-solid-900.ttf"
PIXEL_OPERATOR="/root/PixelOperator.ttf"
DEJAVUSANS="/root/DejaVuSans.ttf"

if [ ! -f "$FONT_AWESOME" ]; then
  echo "Baixando Font Awesome..."
  wget -q --show-progress -O "$FONT_AWESOME" \
    https://github.com/miranildo/Svxlink_Monitor-OrangePi-ZERO-LTS/raw/main/fa-solid-900.ttf || \
    echo "Erro ao baixar Font Awesome"
fi

if [ ! -f "$PIXEL_OPERATOR" ]; then
  echo "Baixando Pixel Operator..."
  wget -q --show-progress -O "$PIXEL_OPERATOR" \
    https://github.com/miranildo/Svxlink_Monitor-OrangePi-ZERO-LTS/raw/main/PixelOperator.ttf || \
    echo "Erro ao baixar Pixel Operator"
fi

if [ ! -f "$DEJAVUSANS" ]; then
  echo "Baixando Fonte DejavuSans..."
  wget -q --show-progress -O "$DEJAVUSANS" \
    https://github.com/miranildo/Svxlink_Monitor-OrangePi-ZERO-LTS/raw/main/DejaVuSans.ttf || \
    echo "Erro ao baixar DejaVuSans"
fi

# 6. Baixar o script do display
echo "Instalando script principal..."
SCRIPT_URL="https://github.com/miranildo/Svxlink_Monitor-OrangePi-ZERO-LTS/raw/main/Svxlink_Monitor.py"
SCRIPT_PATH="/opt/svxlink_display/Svxlink_Monitor.py"

wget -q --show-progress -O "$SCRIPT_PATH" "$SCRIPT_URL" || \
  echo "Erro ao baixar o script do display"

chmod +x "$SCRIPT_PATH"

# 7. Configurar serviço systemd
echo "Configurando serviço systemd..."
SERVICE_FILE="/etc/systemd/system/svxlink_monitor.service"

cat > "$SERVICE_FILE" <<EOL
[Unit]
Description=Svxlink Monitor Display Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/svxlink_display
Environment="PATH=/opt/svxlink_display/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
ExecStart=/opt/svxlink_display/bin/python /opt/svxlink_display/Svxlink_Monitor.py
Restart=always
RestartSec=5
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=svxlink_display

[Install]
WantedBy=multi-user.target
EOL

# 8. Ativar serviço
systemctl daemon-reload
systemctl enable svxlink_monitor.service
systemctl start svxlink_monitor.service

echo "Ajustando permissões..."
chown -R root:root /opt/svxlink_display
chmod 644 /root/*.ttf

# 9. Verificar instalação
echo -e "\nVerificação final:"
if systemctl is-active --quiet svxlink_monitor.service; then
  echo -e "\033[32mServiço instalado e rodando com sucesso!\033[0m"
  echo "Status do display:"
  journalctl -u svxlink_monitor.service -b --no-pager | tail -n 5
else
  echo -e "\033[31mErro: Serviço não está rodando\033[0m"
  journalctl -u svxlink_monitor.service -b --no-pager | tail -n 20
  echo -e "\nTente reiniciar o sistema após a instalação"
fi

echo -e "\n=== Instalação concluída ==="
echo "Reinicie o sistema para ativar as configurações de I2C: sudo reboot"
echo "Comandos úteis:"
echo "  systemctl status svxlink_monitor.service"
echo "  journalctl -u svxlink_monitor.service -f"
echo "  sudo reboot"
