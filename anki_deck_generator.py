import hashlib
import logging
import os
from typing import Dict, List, Optional
from datetime import datetime

import genanki
from pydantic import BaseModel
from flashcard_generator import Flashcard


# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s \
                    - %(message)s',
)
logger = logging.getLogger(__name__)


# Modelo Pydantic para representar os flashcards para Anki
class AnkiCard(BaseModel):
    question: str
    answer: str
    topic: Optional[str] = None
    discipline: str
    source_id: Optional[str] = None


# Definição do modelo de nota Anki
BASIC_MODEL = genanki.Model(
    1607392319,  # ID único gerado para o modelo
    'Concurso Básico',
    fields=[
        {'name': 'Pergunta'},
        {'name': 'Resposta'},
        {'name': 'Assunto'},
        {'name': 'Disciplina'},
        {'name': 'Fonte'},
    ],
    templates=[
        {
            'name': 'Card',
            'qfmt': '<div class="card question">'
            '<div class="discipline">{{Disciplina}}</div>'
            '<div class="topic">{{Assunto}}</div>'
            '<div class="question">{{Pergunta}}</div>'
            '</div>',
            'afmt': '<div class="card">'
            '<div class="discipline">{{Disciplina}}</div>'
            '<div class="topic">{{Assunto}}</div>'
            '<div class="question">{{Pergunta}}</div>'
            '<hr id="answer">'
            '<div class="answer">{{Resposta}}</div>'
            '<div class="source"><small>Fonte: {{Fonte}}</small></div>'
            '</div>',
        },
    ],
    css='.card { font-family: Arial, sans-serif; font-size: 16px; text-align: left; margin: 20px; }'
    '.question { font-weight: bold; margin-bottom: 15px; }'
    '.discipline { font-size: 14px; color: #666; margin-bottom: 5px; }'
    '.topic { font-size: 14px; color: #444; margin-bottom: 15px; font-style: italic; }'
    '.answer { margin-top: 15px; }'
    '.source { margin-top: 20px; color: #888; }',
)


def get_unique_id_from_text(text: str) -> int:
    """Gera um ID único baseado no texto usando hash."""
    return int(hashlib.sha256(text.encode('utf-8')).hexdigest(), 16) % 10**9


def create_anki_deck(cards: List[AnkiCard], deck_name: str) -> genanki.Deck:
    """Cria um baralho Anki a partir de uma lista de cards.

    Args:
        cards: Lista de objetos AnkiCard
        deck_name: Nome do baralho

    Returns:
        Objeto genanki.Deck
    """
    # Gera um ID único para o baralho baseado no nome
    deck_id = get_unique_id_from_text(deck_name)

    # Cria o baralho
    deck = genanki.Deck(deck_id, deck_name)

    # Adiciona as notas ao baralho
    for card in cards:
        note = genanki.Note(
            model=BASIC_MODEL,
            fields=[
                card.question,
                card.answer,
                card.topic or 'Geral',
                card.discipline,
                card.source_id or 'Gerado por IA',
            ],
        )
        deck.add_note(note)

    return deck


def organize_cards_by_discipline(
    cards: List[AnkiCard],
) -> Dict[str, List[AnkiCard]]:
    """Organiza os cards por disciplina.

    Args:
        cards: Lista de objetos AnkiCard

    Returns:
        Dicionário com disciplinas como chaves e listas de cards como valores
    """
    organized = {}

    for card in cards:
        if card.discipline not in organized:
            organized[card.discipline] = []
        organized[card.discipline].append(card)

    return organized


def flashcards_to_anki_cards(
    flashcards: List[Flashcard],
    discipline: str,
    topic: str,
    source_id: Optional[str] = None,
) -> List[AnkiCard]:
    """Converte flashcards do formato do gerador para o formato Anki.

    Args:
        flashcards: Lista de flashcards gerados
        discipline: Disciplina dos flashcards
        topic: Assunto/tópico dos flashcards
        source_id: ID de referência do conteúdo original

    Returns:
        Lista de objetos AnkiCard
    """
    anki_cards = []

    for card in flashcards:
        anki_card = AnkiCard(
            question=card.question,
            answer=card.answer,
            topic=topic,
            discipline=discipline,
            source_id=source_id,
        )
        anki_cards.append(anki_card)

    return anki_cards


def create_and_save_deck(
    cards: List[AnkiCard],
    output_dir: str = "anki_decks",
    main_deck_name: str = "Concurso",
) -> str:
    """Cria e salva um baralho Anki organizado por disciplinas.

    Args:
        cards: Lista de objetos AnkiCard
        output_dir: Diretório onde salvar o arquivo
        main_deck_name: Nome do baralho principal

    Returns:
        Caminho do arquivo .apkg salvo
    """
    # Criar diretório se não existir
    os.makedirs(output_dir, exist_ok=True)

    # Organizar cards por disciplina
    cards_by_discipline = organize_cards_by_discipline(cards)

    # Criar pacote Anki
    package = genanki.Package()
    all_decks = []

    # Para cada disciplina, criar um sub-baralho
    for discipline, discipline_cards in cards_by_discipline.items():
        discipline_deck_name = f"{main_deck_name}::{discipline}"
        discipline_deck = create_anki_deck(discipline_cards, discipline_deck_name)
        all_decks.append(discipline_deck)

    # Adicionar todos os baralhos ao pacote
    package.decks = all_decks

    # Gerar nome de arquivo com data e hora
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{main_deck_name.replace(' ', '_')}_{timestamp}.apkg"
    filepath = os.path.join(output_dir, filename)

    # Salvar pacote
    package.write_to_file(filepath)
    logger.info(f"Baralho Anki salvo em: {filepath}")

    return filepath
