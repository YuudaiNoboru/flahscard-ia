import argparse
import logging
from datetime import datetime
from typing import Optional

from dotenv import load_dotenv

from anki_deck_generator import (
    create_and_save_deck,
    flashcards_to_anki_cards,
)  # Novo módulo

# Importar os módulos necessários
from coda_integration import EstudoError
from flashcard_generator import (
    generate_flashcards,
    print_flashcards,
)


# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()


def create_filename(estudo_error: EstudoError, extension: str = 'json') -> str:
    """Cria um nome de arquivo para os flashcards baseado nas informações do erro."""
    date_str = datetime.now().strftime('%Y%m%d')
    disciplina = estudo_error.disciplina.replace(' ', '_').lower()
    assunto = estudo_error.assunto.replace(' ', '_').lower()
    assunto = assunto[:30]  # Limitar o tamanho
    return f'flashcards_{date_str}_{disciplina}_{assunto}_{estudo_error.id}.{extension}'


def process_error(
    estudo_error: EstudoError,
    model: str = 'llama-3.3-70b-versatile',
) -> bool:
    """Processa um erro de estudo e gera flashcards e um baralho Anki.

    Args:
        estudo_error: Objeto EstudoError com as informações do erro
        model: Modelo LLM a ser utilizado

    Returns:
        Optional[str]: Nome do arquivo de flashcards gerado, ou None se falhou
    """
    logger.info(
        f'Processando erro: {estudo_error.id} - {estudo_error.assunto}',
    )

    if not estudo_error.resolucao or len(estudo_error.resolucao) < 20:
        logger.warning(
            f'Resolução muito curta ou vazia para o erro {estudo_error.id}',
        )
        return None

    try:
        # Gerar flashcards
        flashcards = generate_flashcards(
            text=estudo_error.resolucao,
            model=model,
        )


        # Converter flashcards para o formato Anki
        anki_cards = flashcards_to_anki_cards(
            flashcards.flashcards,
            discipline=estudo_error.disciplina,
            topic=estudo_error.assunto,
            source_id=estudo_error.id,
        )

        # Criar e salvar baralho Anki
        create_and_save_deck(anki_cards, main_deck_name='Concurso')

        # Imprimir flashcards
        print('\n' + '=' * 50)
        print(f'Flashcards gerados para: {estudo_error.assunto}')
        print(f'Disciplina: {estudo_error.disciplina}')
        print(f'Concurso: {estudo_error.concurso}')
        print('=' * 50 + '\n')
        print_flashcards(flashcards)

        return True

    except Exception as e:
        logger.error(f'Erro ao gerar flashcards para {estudo_error.id}: {e}')
        return False


def process_pending_flashcards(
    limit: int = 5,
    model: str = "llama-3.3-70b-versatile",
):
    """Processa os erros de estudo pendentes que ainda não têm flashcards.

    Args:
        limit: Número máximo de erros a processar
        model: Modelo LLM a ser utilizado
    """
    from coda_integration import CodaIntegration

    logger.info(f"Buscando até {limit} erros pendentes para processamento")

    # Inicializar a integração com o Coda
    coda = CodaIntegration()

    # Buscar erros pendentes
    pending_errors = coda.get_pending_flashcards(limit=limit)

    if not pending_errors:
        logger.info("Não há erros pendentes para processamento")
        return

    logger.info(f"Encontrados {len(pending_errors)} erros pendentes")

    # Lista para acumular todos os flashcards
    all_anki_cards = []

    # Processar cada erro
    for error in pending_errors:
        try:
            # Gerar flashcards
            flashcards = generate_flashcards(
                text=error.resolucao,
                model=model,
            )

            # Converter flashcards para o formato Anki
            anki_cards = flashcards_to_anki_cards(
                flashcards.flashcards,
                discipline=error.disciplina,
                topic=error.assunto,
                source_id=error.id,
            )

            # Adicionar os flashcards à lista acumulada
            all_anki_cards.extend(anki_cards)

            # Marcar como criado no Coda
            coda.mark_as_created(error.id)
            logger.info(f"Flashcards gerados e marcados como concluídos para {error.id}")

        except Exception as e:
            logger.error(f"Erro ao processar erro {error.id}: {e}")

    # Criar e salvar um único baralho Anki com todos os flashcards
    if all_anki_cards:
        create_and_save_deck(all_anki_cards, main_deck_name="Concurso")
        logger.info("Baralho Anki único criado com sucesso.")
    else:
        logger.warning("Nenhum flashcard foi gerado.")


def process_by_discipline(
    discipline: str,
    limit: int = 10,
    model: str = 'llama-3.3-70b-versatile',
):
    """Processa erros de estudo de uma disciplina específica.

    Args:
        discipline: Nome da disciplina para filtrar
        limit: Número máximo de erros a processar
        model: Modelo LLM a ser utilizado
    """
    from coda_integration import CodaIntegration

    logger.info(f'Buscando até {limit} erros da disciplina "{discipline}"')

    # Inicializar a integração com o Coda
    coda = CodaIntegration()

    # Buscar erros da disciplina
    errors = coda.search_errors_by_discipline(
        discipline=discipline, limit=limit
    )

    if not errors:
        logger.info(
            f'Não há erros registrados para a disciplina "{discipline}"'
        )
        return

    logger.info(
        f'Encontrados {len(errors)} erros para a disciplina "{discipline}"'
    )

    # Processar cada erro
    for error in errors:
        result = process_error(error, model=model)

        if result:
            logger.info(f'Flashcards criados para {error.id}')
        else:
            logger.warning(f'Falha ao processar erro {error.id}')


def process_specific_error(
    error_id: str,
    model: str = 'llama-3.3-70b-versatile',
):
    """Processa um erro de estudo específico pelo ID.

    Args:
        error_id: ID do erro no Coda
        model: Modelo LLM a ser utilizado
    """
    from coda_integration import CodaIntegration

    logger.info(f'Buscando erro com ID "{error_id}"')

    # Inicializar a integração com o Coda
    coda = CodaIntegration()

    # Buscar erro específico
    error = coda.get_row_by_id(error_id)

    if not error:
        logger.error(f'Erro com ID "{error_id}" não encontrado')
        return

    logger.info(f'Processando erro: {error.assunto} (ID: {error.id})')

    # Processar o erro
    result = process_error(error, model=model)

    if result:
        # Perguntar se deseja marcar como criado
        mark_as_created = input(
            'Deseja marcar o flashcard como criado no Coda? (s/n): '
        )
        if mark_as_created.lower() == 's':
            coda.mark_as_created(error.id)
            logger.info(f'Flashcards marcados como criados para {error.id}')
    else:
        logger.warning(f'Falha ao processar erro {error.id}')


# As funções process_pending_flashcards, process_by_discipline e process_specific_error
# permanecem as mesmas, mas agora também geram o baralho Anki automaticamente.

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Gerador de Flashcards e Baralhos Anki a partir de Erros de Estudo',
    )

    # Grupos de argumentos mutuamente exclusivos
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        '--pending',
        action='store_true',
        help='Processar erros pendentes',
    )
    group.add_argument(
        '--discipline',
        type=str,
        help='Processar erros de uma disciplina específica',
    )
    group.add_argument(
        '--id',
        type=str,
        help='Processar um erro específico por ID',
    )

    # Argumentos opcionais
    parser.add_argument(
        '--limit',
        type=int,
        default=5,
        help='Limite de erros a processar (padrão: 5)',
    )
    parser.add_argument(
        '--model',
        type=str,
        default='llama-3.3-70b-versatile',
        help='Modelo a ser utilizado (padrão: llama-3.3-70b-versatile)',
    )
    parser.add_argument(
        '--cards',
        type=int,
        default=3,
        help='Número de flashcards a gerar por erro (padrão: 3)',
    )

    args = parser.parse_args()

    # Processar conforme a opção escolhida
    if args.pending:
        process_pending_flashcards(
            limit=args.limit,
            model=args.model,
        )
    elif args.discipline:
        process_by_discipline(
            args.discipline,
            limit=args.limit,
            model=args.model,
        )
    elif args.id:
        process_specific_error(args.id, model=args.model)
