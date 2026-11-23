# RAI · Rotildino Avelino Inteligência

> Assistente pessoal de IA por voz para Windows, com holograma animado.

A RAI funciona como a Alexa: você diz **"RAI, ..."**, ela entende o que você falou, pensa com uma inteligência artificial (Gemini, Ollama ou Claude), executa ações no computador e responde em voz alta. Se preferir, você também pode **escrever** para ela no chat do holograma.

```
 Você fala "RAI, ..."
        │
        ▼
 ┌──────────────┐   ┌────────────────────┐   ┌──────────────┐   ┌──────────────┐
 │  Microfone   │──▶│  Whisper (no PC)   │──▶│  IA + ações  │──▶│  Voz neural  │──▶ alto-falante
 └──────────────┘   │  fala → texto      │   │  Gemini /    │   │  texto → fala│
                    └────────────────────┘   │  Ollama /    │   └──────────────┘
 Você escreve no chat ─────────────────────▶ │  Claude      │
                                             └──────┬───────┘
                                                    ▼
                                      Holograma (núcleo animado + legenda)
```

---

## Sumário

1. [O que a RAI faz](#1-o-que-a-rai-faz)
2. [Requisitos](#2-requisitos)
3. [Instalação passo a passo](#3-instalação-passo-a-passo)
4. [Primeira execução](#4-primeira-execução)
5. [Como usar](#5-como-usar)
6. [O holograma e o chat](#6-o-holograma-e-o-chat)
7. [Escolhendo o cérebro: Gemini, Ollama ou Claude](#7-escolhendo-o-cérebro-gemini-ollama-ou-claude)
8. [Configurações (`config.py`)](#8-configurações-configpy)
9. [Criar novas habilidades](#9-criar-novas-habilidades)
10. [Problemas comuns e soluções](#10-problemas-comuns-e-soluções)
11. [Atualizar o projeto com Git](#11-atualizar-o-projeto-com-git)
12. [Segurança](#12-segurança)
13. [Estrutura dos arquivos](#13-estrutura-dos-arquivos)
14. [Perguntas frequentes](#14-perguntas-frequentes)

---

## 1. O que a RAI faz

| Você diz | O que acontece |
|---|---|
| "RAI" | Ela responde "Pois não?" e espera o seu pedido por alguns segundos |
| "RAI, que horas são?" | Responde na hora, com a hora exata do seu PC |
| "RAI, que dia é hoje?" | Responde na hora, com a data completa |
| "RAI, cria um timer de 5 minutos pro café" | Cria um timer e avisa em voz alta quando terminar |
| "RAI, abre o YouTube com música lo-fi" | Abre o navegador já na busca |
| "RAI, abre o VS Code" | Abre o aplicativo |
| "RAI, anota: revisar o deploy de amanhã" | Salva na lista de tarefas |
| "RAI, quais são minhas tarefas?" | Lê a lista de tarefas |
| "RAI, marca a tarefa 1 como feita" | Conclui a tarefa |
| "RAI, lembra que eu prefiro café sem açúcar" | Guarda na memória permanente (ela lembra nas próximas conversas) |
| "RAI, quem ganhou o jogo ontem?" | Pesquisa no Google e responde com base nas fontes |
| "RAI, quanto espaço tenho no disco C?" | Roda um comando PowerShell, **só depois que você confirmar** digitando `s` |
| "RAI, explica o que é Kubernetes" | Responde de forma curta e direta |
| "RAI, pode descansar" | Ela se despede |

> 💡 **Diga "RAI" no começo de cada pedido.** Frases sem o nome são ignoradas, para ela não reagir a conversas ao redor. No chat escrito não precisa do nome.

---

## 2. Requisitos

| Item | Detalhe |
|---|---|
| **Sistema** | Windows 10 ou 11 (a voz e a abertura de apps usam recursos do Windows) |
| **Python** | **3.12** (recomendado). Versões 3.13 e 3.14 podem não ter todas as bibliotecas prontas |
| **Microfone e alto-falante** | Para usar por voz. Sem microfone, use o chat ou o modo texto |
| **Internet** | Para o Gemini e para a voz neural. Com o Ollama, a IA funciona offline |
| **Navegador Microsoft Edge** | Já vem no Windows. É onde o holograma abre |
| **Espaço em disco** | ~1 GB (bibliotecas + modelo de reconhecimento de fala) |
| **Chave de API** | Grátis, do Gemini. Não é necessária se usar o Ollama |

---

## 3. Instalação passo a passo

### 3.1. Instalar o Python 3.12

1. Acesse https://www.python.org/downloads/windows/
2. Procure **Python 3.12.x** e baixe o **Windows installer (64-bit)**.
3. Abra o instalador e, **na primeira tela, marque a opção "Add python.exe to PATH"**. Esse passo é essencial.
4. Clique em **Install Now** e aguarde.
5. Para conferir, abra o PowerShell e digite:
   ```powershell
   python --version
   ```
   Deve aparecer `Python 3.12.x`.

> Já tem outra versão do Python? Pode instalar a 3.12 junto. O `iniciar.bat` usa a 3.12 automaticamente se ela estiver instalada.

### 3.2. Baixar o projeto

**Opção A: pelo site (mais fácil)**

1. Abra https://github.com/jonathas32/RAI
2. Clique no botão verde **Code → Download ZIP**.
3. Descompacte numa pasta fácil de achar, por exemplo `C:\RAI`.

**Opção B: com Git**

```powershell
cd C:\
git clone https://github.com/jonathas32/RAI.git
cd RAI
```

> Não tem o Git? Baixe em https://git-scm.com/download/win e instale com as opções padrão.

### 3.3. Criar a chave grátis do Gemini

1. Acesse https://aistudio.google.com e entre com sua conta Google.
2. Clique em **Get API key**.
3. Clique em **Create API key** e copie a chave gerada.
4. Guarde a chave com cuidado: **ela é como uma senha**.

> Vai usar o Ollama (IA local)? Pode pular este passo. Veja a [seção 7](#7-escolhendo-o-cérebro-gemini-ollama-ou-claude).

---

## 4. Primeira execução

1. Abra a pasta do projeto e **dê dois cliques em `iniciar.bat`**.
2. Na primeira vez, ele:
   - cria um ambiente Python isolado (a pasta `.venv`);
   - instala todas as bibliotecas (leva alguns minutos);
   - cria o arquivo `.env` e abre no **Bloco de Notas**.
3. No Bloco de Notas, troque `cole-sua-chave-gemini-aqui` pela sua chave:
   ```
   GEMINI_API_KEY=AIzaSy...sua-chave...
   ```
   - Sem aspas e sem espaços.
   - Salve com **Ctrl+S** e feche.
4. **Dê dois cliques em `iniciar.bat` de novo.**
5. Na primeira vez em modo voz, ela baixa o modelo de reconhecimento de fala (Whisper). Isso acontece só uma vez.
6. Quando aparecer no terminal:
   ```
   RAI: Olá, senhor. RAI online. É só me chamar.
   ```
   está tudo pronto. Diga **"RAI, que horas são?"** para testar.

> 🔇 Durante a calibração do microfone ("fique em silêncio um instante"), não fale por 2 segundos.

Para **encerrar**, clique na janela do terminal e aperte **Ctrl+C**.

---

## 5. Como usar

### 5.1. Por voz (estilo Alexa)

- **Pedido completo:** "RAI, abre o bloco de notas".
- **Em duas partes:** diga "RAI", espere ela responder "Pois não?" e faça o pedido logo em seguida.
- **O nome pode vir no fim:** "Que horas são, RAI?" também funciona.
- Ela reconhece o nome mesmo quando o reconhecimento de fala escreve "Raí", "Hai", "Ray", "R.A.I.", ou "Ai"/"Oi" no começo da frase.

### 5.2. Por escrito

Use a caixa de texto na parte de baixo do holograma (veja a [seção 6](#6-o-holograma-e-o-chat)), ou ative o modo texto no `config.py`:

```python
MODO = "texto"
```

Nesse modo, você digita no próprio terminal.

### 5.3. O que aparece no terminal

O terminal mostra o que está acontecendo, o que ajuda a entender qualquer demora:

```
Você: RAI, quem ganhou o jogo ontem?  (entendi em 0.7s)       ← tempo para entender sua fala
⚙  pesquisar_internet {'pergunta': '...'}                    ← ferramenta que ela usou
[pesquisa · gemini-3.5-flash-lite · 6.1s · fontes: ge.globo.com]
[gemini-3.5-flash-lite · pensamento minimal · 2.3s]         ← tempo do cérebro
RAI: O Palmeiras venceu por 2 a 1, senhor.  (9.4s)           ← tempo total
(ignorado, diga "RAI" antes) ...                              ← frases sem o nome
```

---

## 6. O holograma e o chat

Ao iniciar, abre uma janela com um núcleo animado que mostra o que a RAI está fazendo. Aperte **F11** para tela cheia.

| Cor / movimento | Significa |
|---|---|
| Azul, respirando devagar | Esperando você dizer "RAI" |
| Azul claro, reagindo à sua voz | Ouvindo o pedido |
| Dourado, girando rápido | Pensando |
| Azul pulsando com ondas | Falando (a resposta aparece como legenda) |
| Vermelho | Sem conexão com a RAI |

**Chat escrito:**

- Digite na caixa de baixo e aperte **Enter**. No chat não precisa dizer "RAI".
- Comece a digitar em qualquer lugar da janela e o texto vai direto para a caixa.
- O botão **Histórico** mostra toda a conversa, incluindo o que foi falado por voz.
- Para receber só a resposta escrita, sem voz: `FALAR_RESPOSTA_DO_CHAT = False`.

> 🔒 Só a janela da própria RAI consegue enviar mensagens para ela. Outros sites abertos no navegador não conseguem dar comandos.

Para não abrir o holograma: `HOLOGRAMA = False`.

---

## 7. Escolhendo o cérebro: Gemini, Ollama ou Claude

No `config.py`, a linha `CEREBRO` define qual IA a RAI usa.

| | **Gemini** (padrão) | **Ollama** | **Claude** |
|---|---|---|---|
| Custo | Grátis (com limites) ou pago | Grátis | Pago |
| Onde roda | Servidores do Google | **No seu PC** | Servidores da Anthropic |
| Internet | Precisa | **Não precisa** | Precisa |
| Pesquisa na web | Sim (Google) | Não | Sim |
| Velocidade | ~5–10 s no plano grátis, mais rápido no pago | 1–3 s com placa de vídeo | Rápido |
| Chave | `GEMINI_API_KEY` | Nenhuma | `ANTHROPIC_API_KEY` |

### 7.1. Gemini (padrão)

```python
CEREBRO = "gemini"
```

- Ao ligar, a RAI **descobre sozinha** quais modelos a sua chave pode usar e mede qual responde mais rápido.
- Se um modelo estiver lotado ou for desativado pelo Google, ela troca para outro automaticamente.
- **Quer mais velocidade?** No AI Studio, ative o faturamento da chave. O plano pago responde bem mais rápido, e o uso pessoal costuma custar centavos.

### 7.2. Ollama (IA local, grátis e offline)

1. Instale o Ollama em https://ollama.com e deixe-o aberto.
2. No PowerShell, baixe um modelo:
   ```powershell
   ollama pull qwen2.5:7b
   ```
3. No `config.py`:
   ```python
   CEREBRO = "ollama"
   OLLAMA_MODELO = "qwen2.5:7b"
   ```
4. Rode o `iniciar.bat`.

| Modelo | Indicado para |
|---|---|
| `qwen2.5:7b` | **Recomendado.** Bom em português. Ideal com placa de vídeo de 8 GB ou mais |
| `llama3.1:8b` | Alternativa parecida |
| `qwen2.5:3b` | PC sem placa de vídeo ou mais fraco: mais rápido, porém menos inteligente |

> O modelo precisa suportar **ferramentas (tools)** para a RAI conseguir criar timers, abrir apps etc.

### 7.3. Claude (Anthropic)

1. Crie uma chave em https://console.anthropic.com (é cobrada à parte da assinatura do Claude).
2. Cole no `.env`: `ANTHROPIC_API_KEY=sk-ant-...`
3. No `config.py`: `CEREBRO = "claude"`.

---

## 8. Configurações (`config.py`)

Abra o `config.py` com o Bloco de Notas ou o VS Code. Depois de mudar algo, feche a RAI (Ctrl+C) e abra de novo.

### Identidade

| Opção | Padrão | O que faz |
|---|---|---|
| `NOME` | `"RAI"` | Nome da assistente |
| `TRATAMENTO` | `"senhor"` | Como ela chama você ("chefe", seu nome...) |

### Cérebro

| Opção | Padrão | O que faz |
|---|---|---|
| `CEREBRO` | `"gemini"` | `"gemini"`, `"ollama"` ou `"claude"` |
| `MODELOS_GEMINI` | `[]` | Vazio = escolha automática. Ou force um modelo: `["nome-do-modelo"]` |
| `TEMPERATURA` | `0.3` | Mais baixo = respostas mais precisas e consistentes |
| `RESPOSTA_RAPIDA` | `True` | Pede ao Gemini para "pensar" o mínimo (bem mais rápido) |
| `TEMPO_MAX_RESPOSTA_SEG` | `25` | Se um modelo travar mais que isso, ela tenta outro |
| `ESCOLHER_MAIS_RAPIDO` | `True` | Mede a velocidade dos modelos ao ligar e usa o mais rápido |
| `PESQUISA_WEB_GEMINI` | `True` | Permite pesquisar no Google para fatos atuais |
| `MOSTRAR_TEMPOS` | `True` | Mostra no terminal quanto cada etapa levou |
| `OLLAMA_MODELO` | `"qwen2.5:7b"` | Modelo usado no Ollama |
| `MODELO_CLAUDE` | `"claude-haiku-4-5"` | Modelo usado no Claude |

### Ouvido e conversa

| Opção | Padrão | O que faz |
|---|---|---|
| `MODO` | `"voz"` | `"voz"` ou `"texto"` (digitar no terminal) |
| `WHISPER_MODELO` | `"base"` | `tiny` (mais rápido) · `base` · `small` (entende melhor) · `medium` |
| `SENSIBILIDADE_MIC` | `3.0` | Maior = precisa falar mais alto para ela começar a gravar |
| `SILENCIO_FIM_SEG` | `0.7` | Quanto tempo de silêncio encerra sua frase |
| `ESPERA_PEDIDO_SEG` | `8` | Depois de "RAI" sozinho, quanto tempo ela espera o pedido |
| `JANELA_CONVERSA_SEG` | `0` | `0` = sempre dizer "RAI". Ex.: `15` = pode continuar a conversa sem repetir o nome |

### Voz

| Opção | Padrão | O que faz |
|---|---|---|
| `TTS_MOTOR` | `"edge"` | `"edge"` (voz natural, precisa de internet) ou `"offline"` (voz do Windows) |
| `VOZ` | `"pt-BR-AntonioNeural"` | Outras: `pt-BR-FranciscaNeural`, `pt-BR-ThalitaNeural`, `en-GB-OllieMultilingualNeural` (português com sotaque britânico) |
| `VELOCIDADE` | `"+6%"` | Ex.: `"-10%"`, `"+15%"` |
| `TOM` | `"-6Hz"` | Mais grave: `"-10Hz"`. Mais agudo: `"+5Hz"` |

### Apps e holograma

| Opção | O que faz |
|---|---|
| `APPS` | Lista de apps que ela sabe abrir: `"nome falado": "comando do Windows"` |
| `HOLOGRAMA` | `True` abre a janela do núcleo animado com o chat |
| `FALAR_RESPOSTA_DO_CHAT` | Se ela responde em voz alta o que você escreve no chat |

**Exemplo: adicionar o WhatsApp à lista de apps**

```python
APPS = {
    "bloco de notas": "notepad",
    "whatsapp": "whatsapp:",
    # ...
}
```

---

## 9. Criar novas habilidades

As habilidades ficam em `ferramentas.py`. A IA lê a descrição de cada uma e decide sozinha quando usar.

**Exemplo: uma habilidade que joga um dado.**

**1.** Adicione a descrição na lista `DEFINICOES`:

```python
{
    "name": "jogar_dado",
    "description": "Joga um dado e retorna o número sorteado. Use quando o usuário pedir para jogar um dado.",
    "input_schema": {
        "type": "object",
        "properties": {"lados": {"type": "integer", "description": "Quantidade de lados do dado"}},
    },
},
```

**2.** Crie o método na classe `Ferramentas`, com o nome começando por `_`:

```python
def _jogar_dado(self, lados=6):
    import random
    return f"Saiu {random.randint(1, int(lados))}."
```

**3.** Reinicie a RAI e diga: **"RAI, joga um dado de 20 lados"**.

> Ideias: controlar luzes com o Home Assistant, ler a agenda, consultar o status de um pipeline, tocar música no Spotify, mandar uma mensagem.

---

## 10. Problemas comuns e soluções

> 📄 Quando algo dá errado, a RAI fala o motivo, mostra o erro no terminal e salva os detalhes em `rai_erros.log`, na pasta do projeto.

### Instalação

| Problema | Solução |
|---|---|
| `python` não é reconhecido | Reinstale o Python marcando **"Add python.exe to PATH"** |
| "ERRO na instalacao" ou falha ao instalar um pacote | Use o **Python 3.12**. Apague a pasta `.venv` e rode o `iniciar.bat` de novo |
| `No module named ...` | Apague o arquivo `.venv\instalado_v2.ok` e rode o `iniciar.bat` para reinstalar |
| O Bloco de Notas salvou como `.env.txt` | No Explorador, ative *Exibir → Extensões de nomes de arquivos* e renomeie para `.env` |

### Chave e cérebro

| Mensagem ou erro | Causa e solução |
|---|---|
| "Falta a chave da API" | O `.env` não existe ou está sem chave. Veja a [seção 4](#4-primeira-execução) |
| "Minha chave do Gemini foi recusada" / `API_KEY_INVALID` | A chave está errada ou foi apagada. Gere outra no AI Studio |
| `404 NOT_FOUND ... no longer available` | O Google desativou um modelo. A RAI troca sozinha. Se persistir, deixe `MODELOS_GEMINI = []` |
| `429 RESOURCE_EXHAUSTED` | Limite do plano grátis atingido. Espere um minuto (ou até o dia seguinte) ou ative o faturamento |
| `503 UNAVAILABLE` | Servidores do Google lotados. Ela tenta outro modelo. Se persistir, espere um pouco |
| `504 DEADLINE_EXCEEDED` | O Gemini demorou demais. Tente de novo. Se for frequente, considere o plano pago ou o Ollama |
| "A conexão segura foi bloqueada" | Antivírus ou proxy da rede bloqueando o Python |
| "O Ollama não está rodando" | Abra o Ollama e rode a RAI de novo |
| "O modelo não está baixado no Ollama" | Rode `ollama pull nome-do-modelo` |

### Velocidade

| Situação | Solução |
|---|---|
| Ela demora para responder | Veja os tempos no terminal. Se a demora for no Gemini (`[gemini... 9s]`), é o servidor do plano grátis: ative o faturamento ou use o Ollama |
| "entendi em" muito alto | Use `WHISPER_MODELO = "tiny"` |
| Demora para perceber que terminei de falar | Diminua `SILENCIO_FIM_SEG` (ex.: `0.5`) |

### Microfone e voz

| Problema | Solução |
|---|---|
| Ela não reage ao "RAI" | Veja no terminal como sua fala foi escrita. Se for outra grafia, adicione-a na lista `WAKE` do `main.py` |
| Entende errado o que eu falo | Use `WHISPER_MODELO = "small"` e fale perto do microfone |
| Não me ouve ou corta as frases | Diminua `SENSIBILIDADE_MIC` (ex.: `2.0`) e confira o microfone padrão em Configurações → Sistema → Som |
| Ativa sozinha com barulho | Aumente `SENSIBILIDADE_MIC` (ex.: `4.0`) |
| Sem voz | A voz `edge` precisa de internet. Sem internet, use `TTS_MOTOR = "offline"` |

### Holograma

| Problema | Solução |
|---|---|
| A janela não abriu | Abra manualmente o endereço que aparece no terminal (ex.: `http://127.0.0.1:8765/`) |
| Aparece "DESCONECTADO" | A RAI foi encerrada. Rode o `iniciar.bat` de novo |

---

## 11. Atualizar o projeto com Git

### Enviar suas mudanças para o GitHub

Na pasta do projeto, no PowerShell:

```powershell
git add .
git status                      # confira: o .env NÃO pode aparecer na lista
git commit -m "descreva o que mudou"
git push
```

### Baixar a versão mais nova em outro PC

```powershell
git pull
```

### Primeira vez enviando (repositório novo)

```powershell
git init
git add .
git status
git commit -m "RAI - Rotildino Avelino Inteligência"
git branch -M main
git remote add origin https://github.com/SEU-USUARIO/RAI.git
git push -u origin main
```

**Problemas comuns no push:**

| Erro | Solução |
|---|---|
| `Permission denied to outra-conta` | O Git usou outra conta salva no Windows. Rode `git remote set-url origin https://SEU-USUARIO@github.com/SEU-USUARIO/RAI.git` e faça o push de novo |
| `rejected (fetch first)` | O GitHub tem arquivos que você não tem. Rode `git pull origin main --allow-unrelated-histories --no-edit` e depois `git push` |

---

## 12. Segurança

- 🔑 **A chave fica só no arquivo `.env`**, que está no `.gitignore` e **nunca vai para o GitHub**.
- 🚫 Nunca cole chaves ou tokens no código, em issues, em prints ou em conversas. Se vazar, apague a chave e gere outra.
- ⚠️ **Não suba o projeto arrastando arquivos no site do GitHub**: por esse caminho o `.gitignore` não vale e o `.env` pode ir junto. Use o Git.
- ✅ Comandos no computador (PowerShell) **sempre pedem confirmação** antes de rodar.
- 🏠 Tarefas, memória e o log de erros ficam só no seu PC (pasta `dados/` e `rai_erros.log`), fora do GitHub.
- 🔒 O holograma só aceita mensagens da própria janela da RAI e só funciona no seu computador (`127.0.0.1`).

---

## 13. Estrutura dos arquivos

```
RAI/
├── main.py            Loop principal: ouvir → entender → pensar → falar
├── cerebro.py         Conversa com a IA (Gemini, Ollama ou Claude) e executa as ferramentas
├── ferramentas.py     Habilidades da RAI (timer, apps, sites, tarefas, memória, PowerShell)
├── ouvido.py          Microfone + reconhecimento de fala (Whisper, roda no PC)
├── voz.py             Fala (Edge TTS ou voz do Windows)
├── holograma.py       Servidor local da janela do holograma e do chat
├── holograma.html     Visual do holograma, legenda e chat escrito
├── config.py          Todas as configurações
├── iniciar.bat        Instala (na primeira vez) e inicia a RAI
├── requirements.txt   Bibliotecas Python necessárias
├── .env.exemplo       Modelo do arquivo de chaves
├── .gitignore         O que NÃO vai para o GitHub (.env, .venv, dados...)
└── README.md          Este arquivo

Criados automaticamente (não vão para o GitHub):
├── .env               Suas chaves
├── .venv/             Ambiente Python com as bibliotecas
├── dados/             Tarefas e memória da RAI
└── rai_erros.log      Registro de erros
```

---

## 14. Perguntas frequentes

**Preciso pagar alguma coisa?**
Não. O Gemini tem plano gratuito (com limites de uso e velocidade) e o Ollama é totalmente grátis. A voz e o reconhecimento de fala também são gratuitos.

**Funciona no Mac ou no Linux?**
Hoje não. A RAI usa recursos do Windows para tocar a voz e abrir apps.

**Ela fica ouvindo e mandando tudo para a internet?**
Não. O reconhecimento de fala roda no seu PC, e só os pedidos que começam com "RAI" (ou que você escreve no chat) são enviados para a IA. Com o Ollama, nada sai do seu computador.

**Ela lembra das conversas?**
Ela lembra o que você pede para lembrar ("RAI, lembra que..."), mesmo depois de fechar. O histórico da conversa atual é perdido ao encerrar.

**Instalei em outro PC e ela não lembra de nada.**
Normal: a memória fica na pasta `dados/` de cada PC. Copie essa pasta se quiser levar a memória junto.

**Posso mudar o nome dela?**
Pode. Mude `NOME` no `config.py` e ajuste a lista `WAKE` no `main.py` com as grafias do novo nome.

---

<p align="center">
  <b>RAI · Rotildino Avelino Inteligência</b><br>
  Feito com Python, Whisper, Gemini e muita curiosidade.
</p>
