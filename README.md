# Svxlink_Monitor OrangePi ZERO LTS DEBIAN 12 ARMBIAN 2025
Instalação do display oled para monitoramento.

O SvxLink já deverá está instalado e funcionando, bem como o SVXLink-Dash-V2, o script instala todas as dependências para que funcione um Display OLED ligado na porta GPIO do OrangePi ZERO LTS e atualiza o SVXLink-Dash-V2 para a última versão, favor não atualizar o PHP.

Pinos GPIO:

3 TWI0_SDA / PA12 / GPIO12

4 5V

5 TWI0_SCK / PA11 / GPIO11

6 GND

Como usar:

Baixe o script install_svxlink_display.sh com o comando "wget https://github.com/miranildo/Svxlink_Monitor-OrangePi-ZERO-LTS/raw/refs/heads/main/install_svxlink_display.sh"

Dê permissão de execução:

chmod +x install_svxlink_display.sh

Execute como root:

sudo ./install_svxlink_display.sh

Pós-instalação:

Verifique o status do serviço:

systemctl status svxlink_monitor.service

Visualize os logs:

journalctl -u svxlink_monitor.service -f

Reinicie o serviço se necessário:

systemctl restart svxlink_monitor.service

Para que o display funcione é necessário um "reboot" ao final da instalação.

Este script completo vai:

1 - Configurar automaticamente o I2C na porta 0

2 - Criar um ambiente virtual Python isolado

3 - Instalar todas as dependências necessárias

4 - Configurar as fontes no diretório /opt/svxlink_display/

5 - Criar e ativar o serviço systemd

6 - Iniciar automaticamente o display na inicialização do sistema

Créditos: https://github.com/LeoVichi/SVXLink_Monitor
          e https://github.com/f5vmr/SVXLink-Dash-V2

