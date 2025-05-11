import pandas as pd
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import sys
import os

def resource_path(relative_path):
    """Retorna o caminho absoluto, compatível com execução direta ou empacotada."""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

# Mapeamentos para categoria de risco
risco_valor = {
    'VU': 0.0,    # Vulnerável
    'EN': 0.2,    # Em perigo
    'CR': 0.4,    # Criticamente em perigo
    'CR(PEX)': 0.6,  # Provavelmente extinto
    'EW': 0.8,    # Extinto na natureza
    'EX': 1.0     # Extinto
}

# Matriz de similaridade entre grupos
similaridade_grupo = {
    'anfibios': {'anfibios': 1, 'aves': 0.2, 'invertebrados aquáticos': 0.6, 'invertebrados terrestres': 0.4,
                 'mamíferos': 0.1, 'peixes': 0.7, 'répteis': 0.8},
    'aves': {'anfibios': 0.2, 'aves': 1, 'invertebrados aquáticos': 0.1, 'invertebrados terrestres': 0.3,
             'mamíferos': 0.6, 'peixes': 0.4, 'répteis': 0.8},
    'invertebrados aquáticos': {'anfibios': 0.6, 'aves': 0.1, 'invertebrados aquáticos': 1, 'invertebrados terrestres': 0.8,
                                 'mamíferos': 0.2, 'peixes': 0.7, 'répteis': 0.5},
    'invertebrados terrestres': {'anfibios': 0.4, 'aves': 0.3, 'invertebrados aquáticos': 0.8, 'invertebrados terrestres': 1,
                                 'mamíferos': 0.7, 'peixes': 0.2, 'répteis': 0.6},
    'mamíferos': {'anfibios': 0.1, 'aves': 0.6, 'invertebrados aquáticos': 0.2, 'invertebrados terrestres': 0.7,
                  'mamíferos': 1, 'peixes': 0.4, 'répteis': 0.5},
    'peixes': {'anfibios': 0.7, 'aves': 0.4, 'invertebrados aquáticos': 0.7, 'invertebrados terrestres': 0.2,
               'mamíferos': 0.4, 'peixes': 1, 'répteis': 0.8},
    'répteis': {'anfibios': 0.8, 'aves': 0.8, 'invertebrados aquáticos': 0.5, 'invertebrados terrestres': 0.6,
                'mamíferos': 0.5, 'peixes': 0.8, 'répteis': 1},
}

# Pesos padrão
pesos_default = {
    'grupo': 1.0,
    'ordem': 1.5,
    'familia': 2.5,
    'especie': 4.0,
    'categoria': 0.5,
    'lista_2014': 0.5
}

class RBCApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema RBC - Espécies Ameaçadas")

        self.df = pd.read_csv(resource_path("dados.csv"))

        self.create_widgets()

    def create_widgets(self):
        frm = ttk.Frame(self.root, padding=10)
        frm.grid()

        # Entrada de atributos
        self.inputs = {}
        atributos = ['grupo', 'ordem', 'familia', 'especie', 'categoria', 'lista_2014']
        row = 0
        for att in atributos:
            ttk.Label(frm, text=f"{att}:").grid(column=0, row=row, sticky="w")
            self.inputs[att] = ttk.Entry(frm, width=30)
            self.inputs[att].grid(column=1, row=row)
            row += 1

        # Pesos
        self.pesos = {}
        for att, peso in pesos_default.items():
            ttk.Label(frm, text=f"Peso {att}:").grid(column=2, row=row - 6)
            self.pesos[att] = ttk.Entry(frm, width=5)
            self.pesos[att].insert(0, str(peso))
            self.pesos[att].grid(column=3, row=row - 6)
            row += 1

        # Botão de execução
        ttk.Button(frm, text="Calcular Similaridade", command=self.calcular_similaridade).grid(column=0, row=row+1, columnspan=4, pady=10)

        # Resultado
        self.texto_resultado = tk.Text(frm, width=100, height=25)
        self.texto_resultado.grid(column=0, row=row+2, columnspan=4)

    def calcular_similaridade(self):
        caso_entrada = {k: v.get().strip().lower() for k, v in self.inputs.items()}
        pesos = {k: float(v.get()) for k, v in self.pesos.items()}

        resultados = []

        for _, row in self.df.iterrows():
            s_locais = []
            p_total = 0

            # Grupo (matriz)
            g1, g2 = caso_entrada['grupo'], str(row['grupo']).lower()
            sim_grupo = similaridade_grupo.get(g1, {}).get(g2, 0)
            s_locais.append(sim_grupo * pesos['grupo'])
            p_total += pesos['grupo']

            # Ordem, Família, Espécie: binário
            for campo, chave in zip(['ordem', 'familia', 'especie_ou_subespecie'], ['ordem', 'familia', 'especie']):
                s = 1.0 if caso_entrada[chave] == str(row[campo]).lower() else 0.0
                s_locais.append(s * pesos[chave])
                p_total += pesos[chave]

           # Categoria (ordinal)
            entrada_cat = caso_entrada['categoria'].upper()
            if entrada_cat in risco_valor:
                r1 = risco_valor[entrada_cat]
                r2 = risco_valor.get(str(row['categoria']).upper(), 1.0)
                sim_risco = 1 - abs(r1 - r2)
            else:
                sim_risco = 0.0  # Nenhum valor válido inserido
            val = sim_risco * pesos['categoria']
            s_locais.append(val)
            p_total += pesos['categoria']


            # Lista 2014 (binário)
            try:
                l1 = int(caso_entrada['lista_2014'])
                l2 = int(row['lista_2014'])
                sim_lista = 1.0 if l1 == l2 else 0.0
            except:
                sim_lista = 0.0
            s_locais.append(sim_lista * pesos['lista_2014'])
            p_total += pesos['lista_2014']

            # Similaridade global
            sim_global = sum(s_locais) / p_total if p_total > 0 else 0
            resultados.append((sim_global, row))

        # Ordenar e mostrar
        resultados.sort(reverse=True, key=lambda x: x[0])
        self.texto_resultado.delete("1.0", tk.END)
        for sim, caso in resultados:
            self.texto_resultado.insert(tk.END, f"{sim*100:.2f}% - {caso.to_dict()}\n\n")

if __name__ == "__main__":
    root = tk.Tk()
    app = RBCApp(root)
    root.mainloop()
