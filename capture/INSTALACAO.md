# Lance On — Instalacao no PC da quadra

## O que instala onde

| Onde | O que | Como o cliente usa |
|------|--------|-------------------|
| **Nuvem (AWS)** | API + admin | Abrir o **link no navegador** (Chrome). Nada para instalar no PC da quadra. |
| **PC da quadra (Ubuntu ou Windows)** | Agente de captura | Setup App; depois inicia sozinho com o sistema. |

---

## Windows (novo)

### Requisitos

1. **Windows 10/11**
2. **Python 3.12+** — https://www.python.org/downloads/  
   Marque **Add python.exe to PATH** na instalacao.
3. **FFmpeg** — o Setup tenta instalar com `winget`. Se falhar, instale manualmente e reinicie o PC.

### Instalacao

1. Copie a pasta `capture` para o PC (USB).
2. Clique com o botao direito em **`LanceOn-Setup.bat`** → **Executar como administrador** (ou clique duplo e aceite o UAC).
3. Preencha a chave do dispositivo, IPs das cameras, usuario/senha e (opcional) a marca d'agua.
4. Clique **Instalar e iniciar**.

### Onde fica no Windows

| Item | Caminho |
|------|---------|
| Software | `C:\ProgramData\LanceOn\capture` |
| Config | `C:\ProgramData\LanceOn\config.yaml` |
| Videos / fila | `C:\ProgramData\LanceOn\data` |
| Logs | `C:\ProgramData\LanceOn\logs\capture.log` |

### Botoes no Windows

Windows **nao** usa GPIO do Raspberry Pi. Use:

| Camera | Tecla padrao |
|--------|----------------|
| Camera 1 | **F1** |
| Camera 2 | **F2** |
| Camera 3 | **F3** |

Botoes USB tipo arcade/HID que enviam F1/F2 funcionam.  
App **PRONTO** / admin **Gravar** tambem funcionam (internet).

### Comandos uteis (Windows)

```bat
schtasks /Run /TN LanceOnCapture
schtasks /End /TN LanceOnCapture
type C:\ProgramData\LanceOn\logs\capture.log
```

Ou use:

- `C:\ProgramData\LanceOn\start-capture.bat`
- `C:\ProgramData\LanceOn\stop-capture.bat`
- `C:\ProgramData\LanceOn\status-capture.bat`

O gravador inicia no **login do usuario** (para os botoes de teclado funcionarem). Em quadra, configure login automatico no Windows.

---

## Ubuntu / Mini PC (Raspberry Pi)

### Instalacao simples (recomendado)

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

### Depois da instalacao (Ubuntu)

- **Arranque automatico:** servico `lanceon-capture` (systemd).
- **Botoes fisicos:** um por camera (sinal no GPIO + GND). Padrao:
  - Camera 1: GPIO17 (pino **11**) + pino **9** (GND)
  - Camera 2: GPIO22 (pino **15**) + pino **13** (software drives GPIO27 LOW as GND)
- **Admin Gravar / app PRONTO:** gravam as cameras.

```bash
sudo systemctl status lanceon-capture
sudo journalctl -u lanceon-capture -f
sudo systemctl restart lanceon-capture
```

Configuracao: `/etc/lance-on/config.yaml`

---

## Sem internet

O botao grava o clip no PC mesmo sem internet. Os arquivos ficam na fila de upload e sao enviados quando a API voltar; so sao apagados depois do upload. Clips com mais de 48 h (ou se o disco passar de 4 GB) sao descartados. O app so mostra o video depois que ele chegar na nuvem.

## Painel admin

O cliente **nao** instala o admin no PC da quadra. Use `https://lanceonpara.com.br` (admin) e `https://api.lanceonpara.com.br` (API).
