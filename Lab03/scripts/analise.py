import pandas as pd
import numpy as np
from scipy.stats import spearmanr, pearsonr
import matplotlib.pyplot as plt
import seaborn as sns

# Configurações de visualização
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

def carregar_dados():
    """Carrega e prepara o dataset"""
    df = pd.read_csv("../data/dataset_lab03S02.csv")
    
    # Calcula métricas compostas
    df['tamanho_total'] = df['linhas_adicionadas'] + df['linhas_removidas']
    df['tamanho_pr'] = df['arquivos_alterados']
    df['interacoes_total'] = df['comentarios'] + df['review_comments']
    
    # Filtra apenas PRs merged e closed conforme metodologia
    df = df[df['estado'].isin(['merged', 'closed'])]
    
    return df

def analisar_correlacoes(df):
    """Executa todas as análises de correlação"""
    
    resultados = []
    
    # Métricas independentes
    metricas_independentes = {
        'tamanho_pr': 'Número de arquivos alterados',
        'tamanho_total': 'Total de linhas modificadas', 
        'tempo_analise_horas': 'Tempo de análise (horas)',
        'descricao_caracteres': 'Tamanho da descrição (caracteres)',
        'num_participantes': 'Número de participantes',
        'interacoes_total': 'Total de interações'
    }
    
    # Dimensões dependentes
    dimensoes = {
        'estado': 'Feedback Final (merged/closed)',
        'num_reviews': 'Número de revisões'
    }
    
    # RQ 01-04: Feedback Final vs Métricas
    print("=== DIMENSÃO A: Feedback Final das Revisões ===")
    df_merged = df[df['estado'] == 'merged']
    df_closed = df[df['estado'] == 'closed']
    
    for metrica, nome in metricas_independentes.items():
        if metrica in ['estado', 'num_reviews']:
            continue
            
        # Teste de diferença entre grupos usando Mann-Whitney (não paramétrico)
        from scipy.stats import mannwhitneyu
        
        try:
            stat, p_valor = mannwhitneyu(
                df_merged[metrica].dropna(),
                df_closed[metrica].dropna(),
                alternative='two-sided'
            )
            
            mediana_merged = df_merged[metrica].median()
            mediana_closed = df_closed[metrica].median()
            
            resultados.append({
                'RQ': '01-04',
                'Dimensão': 'Feedback Final',
                'Métrica': nome,
                'Mediana_Merged': f"{mediana_merged:.2f}",
                'Mediana_Closed': f"{mediana_closed:.2f}",
                'p_valor': f"{p_valor:.4f}",
                'Significativo': p_valor < 0.05
            })
            
            print(f"{nome}:")
            print(f"  Merged (mediana): {mediana_merged:.2f}")
            print(f"  Closed (mediana): {mediana_closed:.2f}") 
            print(f"  p-valor: {p_valor:.4f} {'*' if p_valor < 0.05 else ''}")
            
        except Exception as e:
            print(f"Erro na análise de {nome}: {e}")
    
    print("\n=== DIMENSÃO B: Número de Revisões ===")
    # RQ 05-08: Número de Revisões vs Métricas
    for metrica, nome in metricas_independentes.items():
        if metrica in ['estado', 'num_reviews']:
            continue
            
        # Correlação de Spearman (não assume normalidade)
        corr, p_valor = spearmanr(
            df[metrica].dropna(), 
            df['num_reviews'].dropna(),
            nan_policy='omit'
        )
        
        resultados.append({
            'RQ': '05-08', 
            'Dimensão': 'Número de Revisões',
            'Métrica': nome,
            'Correlação_Spearman': f"{corr:.4f}",
            'p_valor': f"{p_valor:.4f}",
            'Significativo': p_valor < 0.05
        })
        
        print(f"{nome} vs Número de Revisões:")
        print(f"  Correlação Spearman: {corr:.4f}")
        print(f"  p-valor: {p_valor:.4f} {'*' if p_valor < 0.05 else ''}")
    
    return pd.DataFrame(resultados)

def gerar_visualizacoes(df):
    """Gera visualizações para o relatório"""
    
    # 1. Distribuição dos estados
    plt.figure(figsize=(10, 6))
    df['estado'].value_counts().plot(kind='bar')
    plt.title('Distribuição dos PRs por Estado Final')
    plt.ylabel('Quantidade')
    plt.tight_layout()
    plt.savefig('../reports/distribuicao_estados.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 2. Boxplots por estado
    metricas_boxplot = ['tamanho_total', 'tempo_analise_horas', 'descricao_caracteres', 'num_participantes']
    
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    axes = axes.ravel()
    
    for i, metrica in enumerate(metricas_boxplot):
        df_box = df[['estado', metrica]].dropna()
        df_box[metrica] = np.log1p(df_box[metrica])  # Transformação log para melhor visualização
        
        sns.boxplot(data=df_box, x='estado', y=metrica, ax=axes[i])
        axes[i].set_title(f'Distribuição de {metrica} por Estado')
        axes[i].set_ylabel(f'log({metrica})')
    
    plt.tight_layout()
    plt.savefig('../reports/boxplots_por_estado.png', dpi=300, bbox_inches='tight')
    plt.close()

def salvar_resultados(resultados):
    """Salva resultados em CSV"""
    resultados.to_csv('../reports/resultados_correlacoes.csv', index=False)
    print("Resultados salvos em '../reports/resultados_correlacoes.csv'")

if __name__ == "__main__":
    print("Carregando dados...")
    df = carregar_dados()
    
    print(f"Dataset carregado com {len(df)} PRs")
    print(f"Colunas disponíveis: {df.columns.tolist()}")
    
    print("\nExecutando análises de correlação...")
    resultados = analisar_correlacoes(df)
    
    print("\nGerando visualizações...")
    gerar_visualizacoes(df)
    
    print("\nSalvando resultados...")
    salvar_resultados(resultados)
    
    print("\n=== RESUMO DOS RESULTADOS ===")
    print(resultados[['RQ', 'Métrica', 'p_valor', 'Significativo']].to_string(index=False))
