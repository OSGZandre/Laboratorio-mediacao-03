from datetime import datetime

def calcular_tempo_analise(criado_em, fechado_em):
    """Calcula tempo de análise do PR em horas."""
    if not criado_em or not fechado_em:
        return None
    formato = "%Y-%m-%dT%H:%M:%SZ"
    dt_criado = datetime.strptime(criado_em, formato)
    dt_fechado = datetime.strptime(fechado_em, formato)
    diff = dt_fechado - dt_criado
    return diff.total_seconds() / 3600
