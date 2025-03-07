import json
import time
import logging
import os
from typing import List, Optional

from dotenv import load_dotenv
from groq import Groq
from pydantic import BaseModel, Field


# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# Obter a chave da API do arquivo .env
api_key = os.getenv('GROQ_API_KEY')
if not api_key:
    raise ValueError('GROQ_API_KEY não encontrada nas variáveis de ambiente')

# Inicializa a API da Groq
groq = Groq(api_key=api_key)


# Modelo Pydantic para representar os flashcards
class Flashcard(BaseModel):
    question: str
    answer: str
    topic: Optional[str] = Field(
        None,
        description='Tópico ou categoria do flashcard',
    )


class FlashcardResponse(BaseModel):
    flashcards: List[Flashcard]
    summary: Optional[str] = Field(
        None,
        description='Resumo do conteúdo analisado',
    )


def generate_flashcards(
    text: str,
    model: str = "llama3-70b-8192",
) -> FlashcardResponse:
    """Gera flashcards a partir de um texto usando a API da Groq.

    Args:
        text: Texto a ser analisado para gerar flashcards
        model: Modelo LLM a ser utilizado (padrão: llama3-70b-8192)

    Returns:
        Objeto FlashcardResponse contendo os flashcards gerados

    Raises:
        GroqError: Quando ocorre um erro na API da Groq
        ValueError: Quando o texto está vazio
    """
    if not text.strip():
        raise ValueError("O texto não pode estar vazio")

    try:
        logger.info(f"Gerando flashcards usando o modelo {model}")

        # Adicionar um atraso de 2 segundos antes de cada requisição
        time.sleep(2)

        chat_completion = groq.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Você é um professor especialista em técnicas de aprendizado e criação de flashcards de alta qualidade. "
                        "TAREFA: Analise o texto e crie flashcards altamente eficazes para memorização. "
                        "\nSEGUINDO ESTAS DIRETRIZES ESPECÍFICAS:"
                        "\n1. DIVERSIDADE DE FORMATOS: Use pelo menos 3 tipos diferentes de perguntas:"
                        "\n   - Pergunta direta ('O que é X?')"
                        "\n   - Preenchimento de lacunas ('No método ___, a entidade deve...')"
                        "\n   - Verdadeiro/Falso com justificativa ('É correto afirmar que... Por quê?')"
                        "\n   - Pergunta de aplicação ('Como X se aplicaria em Y situação?')"
                        "\n   - Pergunta de associação ('Relacione X com Y')"
                        "\n   - Pergunta de distinção ('Qual a diferença entre X e Y?')"
                        "\n2. QUALIDADE DAS RESPOSTAS:"
                        "\n   - Respostas precisas e completas sem serem vagas"
                        "\n   - Evite respostas circulares que apenas repetem a pergunta"
                        "\n   - Inclua referências específicas às normas quando pertinente (item, parágrafo)"
                        "\n   - Limite a 2-3 frases objetivas, focando nos pontos essenciais"
                        "\n3. CATEGORIZAÇÃO PRECISA:"
                        "\n   - Use categorias específicas (ex: 'Fluxo de Caixa - Método Direto', 'Atividades de Financiamento')"
                        "\n   - Não use categorias genéricas como apenas 'Contabilidade'"
                        "\n4. RESUMO INFORMATIVO:"
                        "\n   - Inclua um resumo que sintetize os principais conceitos e suas relações"
                        "\n   - Destaque as informações mais importantes e as distinções críticas"
                        "\n   - O resumo deve ter entre 3-5 frases estruturadas"
                        "\n5. FOCO NO VALOR EDUCACIONAL:"
                        "\n   - Priorize conceitos que frequentemente aparecem em avaliações"
                        "\n   - Destaque as distinções sutis que causam confusão"
                        "\n   - Formule as perguntas para estimular a recuperação ativa do conhecimento"
                        "\n6. NÚMERO DE FLASHCARDS:"
                        "\n   - Analise o texto e determine quantos flashcards são necessários para cobrir os principais conceitos."
                        "\n   - O número máximo de flashcards é 5."
                        f"\n\nO JSON deve seguir este esquema: {json.dumps(FlashcardResponse.model_json_schema(), indent=2)}"
                    ),
                },
                {"role": "user", "content": text},
            ],
            model=model,
            temperature=0.2,  # Um pouco de temperatura para variedade, mas mantendo precisão
            stream=False,
            response_format={"type": "json_object"},
            max_tokens=4000,
        )

        response_content = chat_completion.choices[0].message.content if chat_completion.choices else None
        if not response_content:
            raise ValueError("Resposta vazia da API da Groq")
        logger.debug(f"Resposta da API: {response_content}")

        return FlashcardResponse.model_validate_json(response_content)

    except Exception as e:
        logger.error(f"Erro inesperado: {e}")
        raise


def print_flashcards(response: FlashcardResponse):
    """Exibe os flashcards gerados de forma formatada."""
    if response.summary:
        print(f'📚 Resumo do conteúdo:\n{response.summary}\n')

    print(f'📝 Total de flashcards: {len(response.flashcards)}\n')

    for i, flashcard in enumerate(response.flashcards, start=1):
        topic_str = f' [{flashcard.topic}]' if flashcard.topic else ''
        print(f'{i}.{topic_str} Pergunta: {flashcard.question}')
        print(f'   Resposta: {flashcard.answer}\n')


# Exemplo de uso
if __name__ == '__main__':
    text = """
    A entidade que utiliza o método indireto para apurar o fluxo de caixa das atividades operacionais deve apresentar a conciliação entre o lucro líquido e o fluxo de caixa líquido das atividades operacionais. ERRADO. 

    Com base no que prevê o CPC 03 (R2), é o método direto, não o indireto, como afirmado na alternativa, vejamos:

    20A. A conciliação entre o lucro líquido e o fluxo de caixa líquido das atividades operacionais deve ser fornecida, obrigatoriamente, caso a entidade use o método direto para apurar o fluxo líquido das atividades operacionais. A conciliação deve apresentar, separadamente, por categoria, os principais itens a serem conciliados, à semelhança do que deve fazer a entidade que usa o método indireto em relação aos ajustes ao lucro líquido ou prejuízo para apurar o fluxo de caixa líquido das atividades operacionais.

    As atividades de financiamento são aquelas que resultam em mudanças no tamanho e na composição do capital próprio e no capital de terceiros da entidade.

    CORRETA. A assertiva está em perfeita consonância com o item 6 do CPC 03 (R2):

    6. Atividades de financiamento são aquelas que resultam em mudanças no tamanho e na composição do capital próprio e no capital de terceiros da entidade.
    """

    try:
        flashcards = generate_flashcards(text, num_cards=3)
        print_flashcards(flashcards)
        save_flashcards(flashcards)
    except Exception as e:
        logger.error(f'Falha ao gerar flashcards: {e}')
