import requests
import pandas as pd
from utils import calcular_tempo_analise

TOKEN = "" 
HEADERS = {"Authorization": f"token {TOKEN}"}

def get_top_repos(n=200):
    repos = []
    per_page = 100
    pages_needed = (n // per_page) + 1
    for page in range(1, pages_needed + 1):
        url = "https://api.github.com/search/repositories"
        params = {
            "q": "stars:>1",
            "sort": "stars",
            "order": "desc",
            "per_page": per_page,
            "page": page
        }
        r = requests.get(url, headers=HEADERS, params=params)
        if r.status_code != 200:
            print(f"Erro ao buscar repositórios populares: {r.status_code}")
            break
        data = r.json()
        items = data.get("items", [])
        if not items:
            break
        for item in items:
            repos.append(item["full_name"])
        if len(repos) >= n:
            break
    return repos[:n]

def coletar_prs(repo, max_pages=3):
    dados = []
    for page in range(1, max_pages + 1):
        url = f"https://api.github.com/repos/{repo}/pulls"
        params = {
            "state": "all",
            "per_page": 100,
            "page": page
        }
        r = requests.get(url, headers=HEADERS, params=params)
        if r.status_code != 200:
            print(f"Erro em {repo}: {r.status_code}")
            break
        prs = r.json()
        if not prs:
            break
        for pr in prs:
            dados.append({
                "repo": repo,
                "id": pr["id"],
                "numero": pr["number"],
                "titulo": pr["title"],
                "estado": pr["state"],
                "autor": pr["user"]["login"] if pr["user"] else None,
                "criado_em": pr["created_at"],
                "fechado_em": pr.get("closed_at"),
                "merged": pr.get("merged_at") is not None,
                "tempo_analise_horas": calcular_tempo_analise(pr["created_at"], pr.get("closed_at")),
                "linhas_adicionadas": pr.get("additions", 0),
                "linhas_removidas": pr.get("deletions", 0),
                "arquivos_alterados": pr.get("changed_files", 0),
                "comentarios": pr.get("comments", 0),
                "review_comments": pr.get("review_comments", 0),
                "descricao": len(pr.get("body") or "")
            })
    return dados

if __name__ == "__main__":
    REPOS = get_top_repos(200)
    todos_prs = []
    for repo in REPOS:
        prs_repo = coletar_prs(repo, max_pages=5)
        todos_prs.extend(prs_repo)

    df = pd.DataFrame(todos_prs)
    df.to_csv("../data/dataset_lab03S01.csv", index=False)
    print("Dataset salvo com", len(df), "PRs")