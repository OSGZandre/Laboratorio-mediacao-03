import requests
import pandas as pd
from utils import calcular_tempo_analise
import os
import time
from dotenv import load_dotenv

# Configuração de caminhos
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, "..", "data")
os.makedirs(DATA_DIR, exist_ok=True)
DATASET_PATH = os.path.join(DATA_DIR, "dataset_lab03_final.csv")

load_dotenv()
token = os.getenv('GITHUB_TOKEN')
HEADERS = {"Authorization": f"token {token}"}

SESSION = requests.Session()
SESSION.headers.update(HEADERS)

def fazer_requisicao_infinita(url, params=None):
    """Faz requisições infinitamente até conseguir resposta"""
    while True:
        try:
            response = SESSION.get(url, params=params, timeout=60)
            
            # Gerencia rate limit agressivamente
            if response.status_code == 403:
                reset_time = int(response.headers.get('X-RateLimit-Reset', time.time() + 3600))
                sleep_time = max(reset_time - time.time(), 0) + 30
                print(f"Rate limit detectado. Dormindo {sleep_time/60:.1f} minutos...")
                time.sleep(sleep_time)
                continue
                
            if response.status_code == 200:
                return response
            elif response.status_code == 422:
                print(f"Erro 422 - Repositório sem PRs: {url}")
                return None
            else:
                print(f"Erro {response.status_code}. Tentando novamente em 30s...")
                time.sleep(30)
                continue
                
        except requests.exceptions.Timeout:
            print("Timeout. Tentando novamente em 30s...")
            time.sleep(30)
        except requests.exceptions.ConnectionError:
            print("Erro de conexão. Tentando novamente em 60s...")
            time.sleep(60)
        except Exception as e:
            print(f"Erro inesperado: {e}. Tentando em 30s...")
            time.sleep(30)

def get_repositorios_populares(n=200):
    """Busca os 200 repositórios mais populares do GitHub"""
    print(f"Buscando {n} repositórios mais populares...")
    repos = []
    page = 1
    
    while len(repos) < n:
        url = "https://api.github.com/search/repositories"
        params = {
            "q": "stars:>1",
            "sort": "stars", 
            "order": "desc",
            "per_page": 100,
            "page": page
        }
        
        response = fazer_requisicao_infinita(url, params)
        if not response:
            break
            
        data = response.json()
        items = data.get("items", [])
        
        if not items:
            break
            
        for item in items:
            repos.append(item["full_name"])
        
        print(f"Repositórios coletados: {len(repos)}/{n}")
        page += 1
        time.sleep(2)
        
        if len(items) < 100:
            break
            
    return repos[:n]

def verificar_repositorio_qualificado(repo_name):
    """Verifica SE o repositório atende TODOS os critérios do enunciado"""
    
    # Critério 1: Pelo menos 100 PRs (MERGED + CLOSED)
    url = "https://api.github.com/search/issues"
    
    # PRs fechados (merged + closed sem merge)
    params_closed = {
        "q": f"repo:{repo_name} type:pr state:closed",
        "per_page": 1
    }
    
    response = fazer_requisicao_infinita(url, params_closed)
    if not response:
        return False
        
    data = response.json()
    total_prs = data.get("total_count", 0)
    
    if total_prs < 100:
        print(f"  {repo_name}: Apenas {total_prs} PRs (precisa de 100)")
        return False
    
    print(f"  {repo_name}: {total_prs} PRs - QUALIFICADO")
    return True

def coletar_prs_por_repositorio(repo_name):
    """Coleta PRs de um repositório que atendem aos critérios"""
    print(f"Mineração {repo_name}...")
    dados = []
    page = 1
    prs_processados = 0
    prs_coletados = 0
    
    while True:
        url = f"https://api.github.com/repos/{repo_name}/pulls"
        params = {
            "state": "closed",
            "per_page": 100,
            "page": page,
            "sort": "created",
            "direction": "desc"
        }
        
        response = fazer_requisicao_infinita(url, params)
        if not response:
            break
            
        prs = response.json()
        if not prs:
            break
            
        for pr in prs:
            pr_number = pr["number"]
            prs_processados += 1
            
            # Busca dados detalhados do PR
            pr_detail_url = f"https://api.github.com/repos/{repo_name}/pulls/{pr_number}"
            pr_detail_response = fazer_requisicao_infinita(pr_detail_url)
            
            if not pr_detail_response:
                continue
                
            pr_detail = pr_detail_response.json()
            
            # Busca reviews para verificar critérios
            reviews_url = f"https://api.github.com/repos/{repo_name}/pulls/{pr_number}/reviews"
            reviews_response = fazer_requisicao_infinita(reviews_url)
            reviews = reviews_response.json() if reviews_response else []
            
            # Filtra apenas reviews humanas
            reviews_humanas = [r for r in reviews if r.get("user") and not r.get("user", {}).get("type") == "Bot"]
            num_reviews = len(reviews_humanas)
            
            # Calcula tempo de análise
            tempo_analise = calcular_tempo_analise(pr["created_at"], pr.get("closed_at"))
            
            # APLICA FILTROS DO ENUNCIADO:
            # 1. Status: MERGED ou CLOSED (já garantido pelo state=closed)
            # 2. Pelo menos uma revisão
            # 3. Tempo de análise > 1 hora
            if num_reviews >= 1 and tempo_analise and tempo_analise > 1:
                # Coleta participantes únicos
                participantes = set()
                if pr["user"]:
                    participantes.add(pr["user"]["login"])
                for review in reviews_humanas:
                    if review.get("user"):
                        participantes.add(review["user"]["login"])
                
                # Coleta TODAS as métricas necessárias
                dados.append({
                    "repo": repo_name,
                    "numero": pr_number,
                    "titulo": pr["title"],
                    "estado": "merged" if pr.get("merged_at") else "closed",
                    "autor": pr["user"]["login"] if pr["user"] else None,
                    "criado_em": pr["created_at"],
                    "fechado_em": pr.get("closed_at"),
                    "merged_at": pr.get("merged_at"),
                    "tempo_analise_horas": tempo_analise,
                    "linhas_adicionadas": pr_detail.get("additions", 0),
                    "linhas_removidas": pr_detail.get("deletions", 0),
                    "arquivos_alterados": pr_detail.get("changed_files", 0),
                    "comentarios": pr.get("comments", 0),
                    "review_comments": pr.get("review_comments", 0),
                    "num_reviews": num_reviews,
                    "num_participantes": len(participantes),
                    "descricao_caracteres": len(pr.get("body") or "")
                })
                
                prs_coletados += 1
                print(f"    PR {pr_number}: {num_reviews} reviews, {tempo_analise:.1f}h")
            
            # Pequena pausa entre PRs
            time.sleep(0.3)
            
        print(f"  Página {page}: {prs_coletados} PRs válidos de {prs_processados} processados")
        page += 1
        
        # Pausa entre páginas
        time.sleep(1)
        
        # Para se chegou ao fim
        if len(prs) < 100:
            break
            
    print(f"  {repo_name}: {prs_coletados} PRs coletados (de {prs_processados} processados)")
    return dados

if __name__ == "__main__":
    print("INICIANDO MINERAÇÃO COMPLETA - 200 REPOSITÓRIOS")
    print("Este processo pode levar VARIAS HORAS ou DIAS")
    print("Salvamento automático habilitado")
    
    # Fase 1: Buscar 200 repositórios populares
    print("\n" + "="*50)
    print("FASE 1: Buscando 200 repositórios populares")
    print("="*50)
    
    todos_repos = get_repositorios_populares(200)
    print(f"Repositórios encontrados: {len(todos_repos)}")
    
    # Fase 2: Filtrar repositórios qualificados
    print("\n" + "="*50)
    print("FASE 2: Filtrando repositórios qualificados")
    print("="*50)
    
    repos_qualificados = []
    for i, repo in enumerate(todos_repos, 1):
        print(f"[{i}/200] Verificando {repo}...")
        if verificar_repositorio_qualificado(repo):
            repos_qualificados.append(repo)
        
        # Salva progresso da filtragem
        pd.DataFrame({"repos_qualificados": repos_qualificados}).to_csv(
            os.path.join(DATA_DIR, "repos_qualificados.csv"), index=False
        )
    
    print(f"Repositórios qualificados: {len(repos_qualificados)}")
    
    # Fase 3: Mineração completa dos PRs
    print("\n" + "="*50)
    print("FASE 3: Mineração dos PRs (PODE LEVAR MUITO TEMPO)")
    print("="*50)
    
    todos_prs = []
    
    for i, repo in enumerate(repos_qualificados, 1):
        print(f"\n[{i}/{len(repos_qualificados)}] MINERANDO {repo}")
        
        try:
            prs_repo = coletar_prs_por_repositorio(repo)
            todos_prs.extend(prs_repo)
            
            # Salva progresso a cada repositório
            df = pd.DataFrame(todos_prs)
            df.to_csv(DATASET_PATH, index=False)
            
            print(f"Progresso salvo: {len(df)} PRs de {len(repos_qualificados)} repositórios")
            
            # Estatísticas parciais
            if len(df) > 0:
                merged = len(df[df['estado'] == 'merged'])
                closed = len(df[df['estado'] == 'closed'])
                print(f"Estatísticas: {merged} merged, {closed} closed")
            
        except Exception as e:
            print(f"ERRO GRAVE em {repo}: {e}")
            print("Continuando para o próximo repositório...")
            continue
    
    # Salvamento final
    df_final = pd.DataFrame(todos_prs)
    df_final.to_csv(DATASET_PATH, index=False)
    
    print("\n" + "="*50)
    print("MINERAÇÃO CONCLUÍDA!")
    print("="*50)
    print(f"TOTAL FINAL: {len(df_final)} PRs")
    print(f"REPOSITÓRIOS: {len(repos_qualificados)}")
    print(f"ARQUIVO: {DATASET_PATH}")
    
    if len(df_final) > 0:
        print(f"MERGED: {len(df_final[df_final['estado'] == 'merged'])}")
        print(f"CLOSED: {len(df_final[df_final['estado'] == 'closed'])}")
        print(f"MEDIA POR REPO: {len(df_final)/len(repos_qualificados):.1f} PRs")