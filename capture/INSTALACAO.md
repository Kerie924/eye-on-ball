# Lance On — Instalacao no Mini PC (quadra)

## O que instala onde

| Onde | O que | Como o cliente usa |
|------|--------|-------------------|
| **Nuvem (AWS)** | API + admin | Abrir o **link no navegador** (Chrome). Nada para instalar no PC da quadra. |
| **Mini PC (Pi)** | Agente de captura | **Um comando** na instalacao; depois liga sozinho com o sistema. |

Nao usamos `.bat` ou `.exe` no Mini PC porque ele roda **Linux (Ubuntu)**, nao Windows.

## Instalacao simples (recomendado)

1. Copie a pasta `capture` para o Mini PC (USB, git ou scp).
2. Abra o terminal na pasta `capture`.
3. Execute:

```bash
chmod +x setup.sh
./setup.sh
```

4. Responda as perguntas (URL da API, chave do admin, IP da camera, senha).
5. Pronto. Reinicie o Mini PC se quiser testar o arranque automatico.

## Depois da instalacao

- **Arranque automatico:** servico `lanceon-capture` (systemd).
- **Botao fisico:** GPIO17 (pino 11) + GND.
- **Admin Gravar / app PRONTO:** mesma funcao que o botao.

Comandos uteis:

```bash
sudo systemctl status lanceon-capture
sudo journalctl -u lanceon-capture -f
sudo systemctl restart lanceon-capture
```

Configuracao: `/etc/lance-on/config.yaml`

## Sem internet

Hoje: a gravacao precisa de internet para **enviar** o video para a nuvem. O buffer local (ultimos 30 s) funciona offline; o envio falha se a API estiver fora.

**Proxima melhoria:** fila local — guardar clips no disco e enviar quando a conexao voltar.

## Painel admin

O cliente **nao** instala o admin no Mini PC. Use o endereco que voce configurou, por exemplo:

`http://13.210.97.155:8000` (API) + painel React hospedado ou `npm run dev` no seu PC de desenvolvimento apontando para essa API.

Para producao, o ideal e um dominio HTTPS (ex.: `https://admin.lanceon.com.br`).
