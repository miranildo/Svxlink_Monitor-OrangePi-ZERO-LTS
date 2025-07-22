# Svxlink_Monitor-OrangePi-ZERO-LTS - João Pessoa 21 de Julho de 2025 23:32:27Hs
Instalação do display oled

Como usar:

Baixe o script install_svxlink_display.sh com o comando "wget https://github.com/miranildo/Svxlink_Monitor-OrangePi-ZERO-LTS/raw/refs/heads/main/install_svxlink_display.sh"

Dê permissão de execução:

chmod +x install_svxlink_display.sh

Execute como root:

sudo ./install_svxlink_display.sh

Script do Display (Svxlink_Monitor.py)

Certifique-se de que o script do display esteja disponível no URL especificado (linha 48 do script de instalação) ou modifique o script para usar uma versão local.

Pós-instalação:

Verifique o status do serviço:

systemctl status svxlink_monitor.service

Visualize os logs:

journalctl -u svxlink_monitor.service -f

Reinicie o serviço se necessário:

systemctl restart svxlink_monitor.service

Este script completo vai:

1 - Configurar automaticamente o I2C na porta 0

2 - Criar um ambiente virtual Python isolado

3 - Instalar todas as dependências necessárias

4 - Configurar as fontes no diretório /opt/svxlink_display/

5 - Criar e ativar o serviço systemd

6 - Iniciar automaticamente o display na inicialização do sistema

Créditos: https://github.com/LeoVichi/SVXLink_Monitor
          https://github.com/f5vmr/SVXLink-Dash-V2

