# Lab03 – Caracterizando a Atividade de Code Review no GitHub

##  Descrição
Este projeto faz parte do laboratório da disciplina **Laboratório de Experimentação de Software**.  
O objetivo é coletar e analisar dados de *Pull Requests (PRs)* de repositórios populares no GitHub, para caracterizar a atividade de *code review*.  

### Estrutura
    Lab03/
    │
    ├── data/ # datasets gerados
    ├── reports/ # relatórios (S01, S02, S03)
    └── scripts/ # scripts de coleta e análise

    
### Scripts
- **`coletar_prs.py`** → coleta os PRs via API do GitHub e salva em CSV  
- **`utils.py`** → funções auxiliares (ex.: cálculo de tempo de análise)  
- **`analise.py`** → análises estatísticas (correlações)  

### Como executar
1. Crie um ambiente virtual (opcional, mas recomendado):  
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows

pip install -r requirements.txt
python scripts/coletar_prs.py

## Membros 
- André Almeida Silva
- Davi Aguilar Nunes 
