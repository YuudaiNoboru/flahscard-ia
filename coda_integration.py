import logging
import os
from datetime import datetime
from typing import Dict, List, Optional

import requests
from dotenv import load_dotenv
from pydantic import BaseModel


# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()

# Obter a chave da API do Coda
CODA_API_KEY = os.getenv('CODA_API_KEY')
if not CODA_API_KEY:
    raise ValueError('CODA_API_KEY não encontrada nas variáveis de ambiente')

# Definir o ID do documento e da tabela
CODA_DOC_ID = os.getenv('CODA_DOC_ID')
CODA_TABLE_ID = os.getenv('CODA_TABLE_ID')
if not CODA_DOC_ID or not CODA_TABLE_ID:
    raise ValueError(
        'CODA_DOC_ID ou CODA_TABLE_ID não encontrados nas variáveis de ambiente',
    )

# Configurações da API
CODA_API_URL = 'https://coda.io/apis/v1'
HEADERS = {
    'Authorization': f'Bearer {CODA_API_KEY}',
    'Content-Type': 'application/json',
}


# Modelo para representar um item de erro de estudo
class EstudoError(BaseModel):
    id: str
    assunto: str
    concurso: str
    disciplina: str
    resolucao: str
    flashcard_criado: bool = False
    tipo_erro: Optional[str] = None
    tarefa: Optional[str] = None
    atividade: Optional[str] = None
    created_at: Optional[datetime] = None


class CodaIntegration:
    def __init__(self):
        self.api_url = CODA_API_URL
        self.doc_id = CODA_DOC_ID
        self.table_id = CODA_TABLE_ID
        self.headers = HEADERS

    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Dict = None,
        data: Dict = None,
    ) -> Dict:
        """Faz uma requisição para a API do Coda.io."""
        url = f'{self.api_url}/{endpoint}'

        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self.headers,
                params=params,
                json=data,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f'Erro na requisição para o Coda.io: {e}')
            if hasattr(e, 'response') and e.response:
                logger.error(f'Resposta da API: {e.response.text}')
            raise

    def get_pending_flashcards(self, limit: int = 10) -> List[EstudoError]:
        """Busca os erros de estudo que ainda não tiveram flashcards criados.

        Args:
            limit: Número máximo de registros a serem retornados (padrão: 10)

        Returns:
            List[EstudoError]: Lista de erros de estudo pendentes
        """
        endpoint = f"docs/{self.doc_id}/tables/{self.table_id}/rows"
        estudo_errors = []
        offset = 0  # Iniciar o offset em 0
        batch_size = 25  # Tamanho máximo de cada lote (limite da API do Coda)

        while len(estudo_errors) < limit:
            # Calcular o número de itens a serem solicitados no lote atual
            remaining = limit - len(estudo_errors)
            current_batch_size = min(batch_size, remaining)

            # Fazer a requisição com o offset e o tamanho do lote atual
            params = {
                "query": "Flashcard Criado:false",
                "limit": current_batch_size,
                "offset": offset,
                "useColumnNames": True,
                "valueFormat": "simple",
            }

            response = self._make_request("GET", endpoint, params=params)

            # Processar os itens do lote atual
            for row in response.get("items", []):
                cells = row.get("values", {})
                criado_em = cells.get("Criado em")
                created_at = None

                if criado_em:
                    try:
                        created_at = datetime.fromisoformat(criado_em)
                    except ValueError:
                        logger.warning(f"Data inválida recebida: {criado_em}")

                estudo_error = EstudoError(
                    id=row.get("id", ""),
                    assunto=cells.get("Assunto", ""),
                    concurso=cells.get("Concurso", ""),
                    disciplina=cells.get("Disciplina", ""),
                    resolucao=cells.get("Resolução", ""),
                    flashcard_criado=cells.get("Flashcard Criado", False),
                    tipo_erro=cells.get("Tipo de Erro", ""),
                    tarefa=cells.get("Tarefa", ""),
                    atividade=cells.get("Atividade", ""),
                    created_at=created_at,
                )
                estudo_errors.append(estudo_error)

            # Verificar se atingimos o limite ou se não há mais itens
            if len(response.get("items", [])) < current_batch_size:
                break  # Não há mais itens para buscar

            # Atualizar o offset para o próximo lote
            offset += current_batch_size

        logger.info(f"Encontrados {len(estudo_errors)} registros pendentes de criação de flashcards")
        return estudo_errors

    def mark_as_created(self, row_id: str) -> bool:
        """Marca um erro de estudo como tendo flashcard criado.

        Args:
            row_id: ID da linha na tabela do Coda

        Returns:
            bool: True se a atualização foi bem-sucedida
        """
        endpoint = f'docs/{self.doc_id}/tables/{self.table_id}/rows/{row_id}'
        
        # Usando o ID da coluna em vez do nome
        data = {
            'row': {
                'cells': [
                    {
                        'column': 'c-YGQq5IUq3f',  # ID da coluna "Flashcard Criado"
                        'value': True
                    }
                ]
            }
        }

        try:
            self._make_request('PUT', endpoint, data=data)
            logger.info(
                f'Flashcard marcado como criado para o erro ID: {row_id}',
            )
            return True
        except Exception as e:
            logger.error(f'Erro ao marcar flashcard como criado: {e}')
            return False

    def get_row_by_id(self, row_id: str) -> Optional[EstudoError]:
        """Busca um erro de estudo específico pelo ID.

        Args:
            row_id: ID da linha na tabela do Coda

        Returns:
            Optional[EstudoError]: Objeto EstudoError se encontrado, None caso contrário
        """
        endpoint = f'docs/{self.doc_id}/tables/{self.table_id}/rows/{row_id}'
        params = {
            'useColumnNames': True,
            'valueFormat': 'simple'
        }

        try:
            response = self._make_request('GET', endpoint, params=params)

            cells = response.get('values', {})

            estudo_error = EstudoError(
                id=row_id,
                assunto=cells.get('Assunto', ''),
                concurso=cells.get('Concurso', ''),
                disciplina=cells.get('Disciplina', ''),
                resolucao=cells.get('Resolução', ''),
                flashcard_criado=cells.get('Flashcard Criado', False),
                tipo_erro=cells.get('Tipo de Erro', ''),
                tarefa=cells.get('Tarefa', ''),
                atividade=cells.get('Atividade', ''),
            )

            return estudo_error
        except Exception as e:
            logger.error(f'Erro ao buscar linha por ID: {e}')
            return None

    def search_errors_by_discipline(
        self,
        discipline: str,
        limit: int = 20,
    ) -> List[EstudoError]:
        """Busca erros de estudo por disciplina.

        Args:
            discipline: Nome da disciplina para filtrar
            limit: Número máximo de registros a serem retornados (padrão: 20)

        Returns:
            List[EstudoError]: Lista de erros de estudo da disciplina especificada
        """
        endpoint = f'docs/{self.doc_id}/tables/{self.table_id}/rows'
        
        # Correção: formatação correta da query para filtrar por disciplina
        params = {
            'query': f'"Disciplina":"{discipline}"',  # Formato correto com aspas duplas
            'limit': limit,
            'useColumnNames': True,
            'valueFormat': 'simple',
        }

        response = self._make_request('GET', endpoint, params=params)

        estudo_errors = []
        for row in response.get('rows', []):
            cells = row.get('values', {})

            estudo_error = EstudoError(
                id=row.get('id', ''),
                assunto=cells.get('Assunto', ''),
                concurso=cells.get('Concurso', ''),
                disciplina=cells.get('Disciplina', ''),
                resolucao=cells.get('Resolução', ''),
                flashcard_criado=cells.get('Flashcard Criado', False),
                tipo_erro=cells.get('Tipo de Erro', ''),
                tarefa=cells.get('Tarefa', ''),
                atividade=cells.get('Atividade', ''),
            )

            estudo_errors.append(estudo_error)

        logger.info(
            f"Encontrados {len(estudo_errors)} registros para a disciplina '{discipline}'",
        )
        return estudo_errors
