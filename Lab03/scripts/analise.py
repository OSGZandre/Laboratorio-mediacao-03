import pandas as pd
from scipy.stats import spearmanr, pearsonr

# Carregar dataset
df = pd.read_csv("../data/dataset_lab03S01.csv")

# Exemplo de correlação: tamanho do PR x tempo de análise
x = df["linhas_adicionadas"] + df["linhas_removidas"]
y = df["tempo_analise_horas"]

# Spearman (mais indicado para dados que não são lineares)
corr, p_valor = spearmanr(x, y, nan_policy="omit")

print("Correlação de Spearman entre tamanho do PR e tempo de análise:")
print(f"Coeficiente = {corr:.4f}, p-valor = {p_valor:.4f}")

# Pearson (caso queira comparar com correlação linear)
corr2, p_valor2 = pearsonr(x.fillna(0), y.fillna(0))
print("Correlação de Pearson (linear):")
print(f"Coeficiente = {corr2:.4f}, p-valor = {p_valor2:.4f}")
