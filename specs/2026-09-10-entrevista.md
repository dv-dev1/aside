# aside — modo entrevista

## Intenção

Numa entrevista em inglês, as três sugestões deixam de ser frases genéricas e
passam a ser respostas que o candidato consegue falar: em primeira pessoa,
curtas, em inglês simples, e sustentadas só em fatos verificados do perfil
dele e da vaga. O contexto mora em `~/.config/aside/`, fora do repositório
público, porque carrega dado pessoal e informação sob NDA.

## Critério de aceite

### 1. Carregamento do contexto

    python3 -m pytest tests/test_contexto.py -q

Carrega todos os `.md` da pasta em ordem alfabética, ignora outros arquivos,
e devolve vazio quando a pasta não existe.

### 2. Resposta de entrevista sustentada no perfil

    python3 -m aside.nuvem --pergunta "Can you tell me about a project you are proud of?"

As três respostas citam projetos reais do perfil. Nenhuma nomeia o cliente
hospitalar e nenhuma usa a palavra "accuracy".

### 3. Sem contexto, nada quebra

    ASIDE_CONTEXTO=/nao/existe python3 -m aside.nuvem --pergunta "How are you?"

Devolve três sugestões genéricas, sem erro.

## Fora de escopo

- Gravar, resumir ou guardar a entrevista.
- Copiar o perfil para dentro do repositório.
- Ensinar vocabulário ao modelo de fala; o Parakeet não aceita hotwords.

## Critérios acrescentados após o primeiro ensaio

### 4. Toda pergunta dispara sugestão

    python3 -m pytest tests/test_turno.py -q -k "turno or pergunta"

Pergunta seguida de 0,3s de silêncio fecha o turno mesmo quando o modelo não
produz texto novo. Era isso que deixava a sugestão congelada: o turno só era
avaliado quando o texto mudava, e no silêncio depois da pergunta o texto não
muda. A sugestão responde sempre à fala mais recente; o que chega enquanto a
chamada anterior roda é juntado, não enfileirado.

### 5. Inglês de quem se faz entender

    python3 -m aside.nuvem --pergunta "Can you tell me about a project you are proud of?"

Cada sugestão tem no máximo 15 palavras, sem expressão idiomática. Fato com
número sai das frases prontas de `vaga.md`, sem paráfrase: nunca "rate" para os
agendamentos.
