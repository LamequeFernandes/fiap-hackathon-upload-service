from enum import Enum


class AnalysisStatus(str, Enum):
    RECEBIDO = "RECEBIDO"
    EM_PROCESSAMENTO = "EM_PROCESSAMENTO"
    ANALISADO = "ANALISADO"
    ERRO = "ERRO"
