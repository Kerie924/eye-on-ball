# Lance On — Instalacao no Mini PC (quadra)

## O que instala onde

| Onde | O que | Como o cliente usa |
|------|--------|-------------------|
| **Nuvem (AWS)** | API + admin | Abrir o **link no navegador** (Chrome). Nada para instalar no PC da quadra. |
| **Mini PC (Ubuntu)** | Agente de captura | **Um clique** no Setup App; depois liga sozinho com o sistema. |

## Instalacao simples (recomendado)

1. Copie a pasta `capture` para o Mini PC (USB).
2. Clique duas vezes em **`LanceOn-Setup.sh`** (ou no atalho `LanceOn-Setup.desktop`).
   - Se o Ubuntu pedir, escolha **Permitir iniciar** / **Allow Launching**.
3. Preencha a chave do dispositivo, IPs das cameras, usuario/senha e (opcional) a marca d'agua.
4. Clique **Instalar e iniciar** e informe a senha de administrador quando o Ubuntu pedir.
5. O Setup instala sozinho FFmpeg, Python, GPIO e o servico `lanceon-capture`.

Se o clique duplo nao abrir, no terminal:

```bash
cd capture
chmod +x LanceOn-Setup.sh
./LanceOn-Setup.sh
```

## Depois da instalacao

- **Arranque automatico:** servico `lanceon-capture` (systemd).
- **Botoes fisicos:** um por camera (sinal no GPIO + GND). Padrao:
  - Camera 1: GPIO17 (pino **11**) + GND (ex.: pino **9**)
  - Camera 2: GPIO27 (pino **13**) + GND (ex.: pino **14**)
  - Camera 3: GPIO22 (pino 15) + GND
  - Camera 4: GPIO23 (pino 16) + GND
  - Camera 5: GPIO24 (pino 18) + GND
  - Camera 6: GPIO25 (pino 22) + GND
- **Admin Gravar / app PRONTO:** gravam todas as cameras (como antes).

Comandos uteis:

```bash
sudo systemctl status lanceon-capture
sudo journalctl -u lanceon-capture -f
sudo systemctl restart lanceon-capture
```

Configuracao: `/etc/lance-on/config.yaml`

## Sem internet

Hoje: a gravacao precisa de internet para **enviar** o video para a nuvem. O buffer local (ultimos 30 s) funciona offline; o envio falha se a API estiver fora.

## Painel admin

O cliente **nao** instala o admin no Mini PC. Use `https://lanceonpara.com.br` (admin) e `https://api.lanceonpara.com.br` (API).
