# Fluentia com NVIDIA AI

Esta versão transforma a conversa gravada em conversação real usando a API da NVIDIA. A chave fica apenas no servidor, em uma variável de ambiente, e nunca é enviada ao navegador.

## Rodar localmente

1. Instale Python 3.10 ou mais recente.
2. Copie `.env.example` para `.env`.
3. Abra `.env` e coloque sua chave NVIDIA em `NVIDIA_API_KEY`.
4. Execute:

```bash
python server.py
```

5. Abra `http://localhost:8000`.

O servidor envia para a NVIDIA apenas o tópico, nível e histórico recente da conversa. A resposta é validada para conter exatamente duas opções em inglês e tradução em português.

## Publicar

Publique esta pasta em uma hospedagem que execute Python (por exemplo, Render, Railway ou Fly.io). Configure `NVIDIA_API_KEY` como variável secreta no painel da hospedagem. Não faça upload do arquivo `.env`.

Endpoint de teste: `/health`.
