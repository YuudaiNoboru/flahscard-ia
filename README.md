# Gerador de Flashcards para Estudo

Este projeto automatiza a criação de flashcards a partir de anotações de erros de estudo armazenadas no Coda.io, utilizando a API da Groq para geração de conteúdo com LLMs.

## Funcionalidades

- Integração com Coda.io para buscar erros de estudo
- Geração automática de flashcards de alta qualidade usando LLMs (via Groq)
- Categorização inteligente dos flashcards
- Marcação automática de itens processados
- Filtragem por disciplina, status de processamento ou ID específico
- Armazenamento local dos flashcards em formato JSON

## Requisitos

- Python 3.8+
- Conta no Coda.io com uma tabela de erros de estudo
- Chave de API da Groq
- Pacotes Python: requests, pydantic, python-dotenv

## Configuração

1. Clone o repositório
2. Crie um arquivo `.env` na raiz do projeto com as seguintes variáveis:
   ```
   GROQ_API_KEY=sua_chave_api_groq
   CODA_API_KEY=sua_chave_api_coda
   CODA_DOC_ID=seu_documento_id
   CODA_TABLE_ID=sua_tabela_id
   ```
3. Instale as dependências: `pip install -r requirements.txt`

## Uso

### Processar erros pendentes
```bash
python flashcard_manager.py --pending --limit 5
```

### Processar erros de uma disciplina específica
```bash
python flashcard_manager.py --discipline "AUDITORIA PRIVADA" --limit 10
```

### Processar um erro específico por ID
```bash
python flashcard_manager.py --id "i-abc123"
```

### Opções adicionais
- `--model`: Especificar o modelo LLM (padrão: llama-3.3-70b-versatile)
- `--cards`: Número de flashcards a gerar por erro (padrão: 3)

## Estrutura do Projeto

- `flashcard_manager.py`: Script principal que coordena o processo
- `coda_integration.py`: Módulo de integração com a API do Coda.io
- `flashcard_generator.py`: Módulo de geração de flashcards com a API da Groq

## Exemplos de Uso

### Gerar 3 flashcards para cada um dos 5 erros pendentes usando o modelo padrão
```bash
python flashcard_manager.py --pending
```

### Gerar 5 flashcards para cada um dos 10 erros da disciplina "ADMINISTRAÇÃO" usando o modelo llama3-8b-8192
```bash
python flashcard_manager.py --discipline "ADMINISTRAÇÃO" --limit 10 --cards 5 --model llama3-8b-8192
```

## Formato dos Flashcards

Os flashcards são gerados em formato JSON e incluem:
- Pergunta
- Resposta
- Tópico/categoria
- Resumo do conteúdo

---

Desenvolvido para auxiliar nos estudos para concursos públicos.