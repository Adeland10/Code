#coding: utf-8

import pandas as pd
import openpyxl as xl
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt  #pour rep histogramme

#-------------------------------------------------------------------------------------------------
#importation du fichier excel et de la fenêtre contenant les raw data
filepath = r'C:\Users\adele\Bureau\INEM\Code-MTECC\HNE PredictCFdec162k p1+3F508del and CastanierSoleneWT p1+3 and no cells in 5 6 20 06 24_comp.xlsx'
sheet= 'HNE PredictCFdec162k p1+3F508de'
df = pd.read_excel(filepath, sheet)
#print("fichier loaded") #vérif
# print(df.head())      #vérif

""" DATA TEST 
df_test=df.head()
"""

# groupby() de pandas pour regrouper par Marker
grouped = df.groupby('Marker')

#-------------------------------------------------------------------------------------------------
# Fonction pour calculer les moyennes des dernières 
# valeurs d'un même marker avant l'ajout de la drogue

def calculate_means(df):
    # Initialisation dictionnaire pour stocker les moyennes des 10 dernières valeurs par colonne et par marqueur
    means_dict = {}

    for marker, group in grouped:
        # Sélect 10 dernières lignes/valeurs pour chaque marqueur
        last_10_rows = group.tail(10)
        #print(last_10_rows) # Verif 10 dernières valeurs de GT, Ieq, Iraw, PD, RT pour chaque marker
        
        # Calcul moyennes pour les colonnes GT, Ieq, Iraw, PD, RT  
        means_dict[marker] = {
            'GT': last_10_rows['GT'].mean(),
            'Ieq': last_10_rows['Ieq'].mean(),
            'Iraw': last_10_rows['Iraw'].mean(),
            'PD': last_10_rows['PD'].mean(),
            'RT': last_10_rows['RT'].mean()
        }

    return pd.DataFrame(means_dict).T  # .T --> transposition, plus facile à lire

#-------------------------------------------------------------------------------------------------
# Fonction pour calculer les deltas entre les marqueurs successifs de chaque puit 

delta_names = ['ΔAmi', 'ΔFsk/IBMX', 'ΔVX770', 'ΔApi', 'ΔInh', 'ΔATP']

def calculate_delta_by_well(df, means_df):
    all_deltas = {}
    wells = df['Well'].unique() #savoir combien de puits diff existent

    for well in wells:
        deltas = {}
        markers = sorted(means_df.index) #trier marker en ordre croissant pour calculer deltas de manière séquentielle entre les marqueurs
        delta_index = 0
    
        for i in range(1, len(markers)):
            marker1 = markers[i]
            marker0 = markers[i - 1]
            delta_name = delta_names[delta_index] if delta_index < len(delta_names) else f"Δ{marker0}-{marker1}"
            
        # Utiliser les moyennes globales pour calculer les deltas
            delta_GT = means_df.loc[marker1]['GT'] - means_df.loc[marker0]['GT']
            delta_Ieq = means_df.loc[marker1]['Ieq'] - means_df.loc[marker0]['Ieq']
            delta_Iraw = means_df.loc[marker1]['Iraw'] - means_df.loc[marker0]['Iraw']
            delta_PD = means_df.loc[marker1]['PD'] - means_df.loc[marker0]['PD']
            delta_RT = means_df.loc[marker1]['RT'] - means_df.loc[marker0]['RT']
            
            deltas[delta_name] = {
                'GT': delta_GT,
                'Ieq': delta_Ieq,
                'Iraw': delta_Iraw,
                'PD': delta_PD,
                'RT': delta_RT
            }
            delta_index += 1

        all_deltas[well] = deltas #stocker les deltas calculés pour un puit
    
    return all_deltas

#-------------------------------------------------------------------------------------------------
# Calculer les moyennes des 10 dernières valeurs par marqueur
moyennes = calculate_means(df)
"""
print("Moyennes des 10 dernières valeurs par marqueur :")
print(moyennes)
"""
# Calculer les deltas
deltas_par_puits = calculate_delta_by_well(df, moyennes)
"""
print("Deltas entre les marqueurs successifs pour chaque puit :")
for well, deltas in deltas_par_puits.items():
    print(f"Puits {well} :")
    for delta_name, delta_values in deltas.items():
        print(f"{delta_name}: {delta_values}")
"""

#-------------------------------------------------------------------------------------------------
# Fonction pour générer le tableau de valeurs 

def create_delta_table(deltas_par_puits):
    columns = pd.MultiIndex.from_product(
        [['GT', 'PD', 'Ieq', 'Iraw', 'RT'], delta_names],
        names=['Measure', 'Delta']
    )
    wells = list(deltas_par_puits.keys())
    delta_table = pd.DataFrame(index=wells, columns=columns)

    for well, deltas in deltas_par_puits.items():
        for delta_name, delta_values in deltas.items():
            for measure, value in delta_values.items():
                delta_table.loc[well, (measure, delta_name)] = value

    return delta_table

# Générer le tableau de valeurs
delta_table = create_delta_table(deltas_par_puits)

# Afficher le tableau
#print(delta_table)

# Optionnel: Sauvegarder le tableau dans un fichier Excel
delta_table.to_excel('delta_table.xlsx')
#-------------------------------------------------------------------------------------------------
# Représentation des deltas --> Test 1 : HISTOGRAMME pour chaque puits avec 5 histogrammes pour chaque puit, un pour chaque mesure

#avec Matplotlib
"""
def plot_deltas_histograms(deltas_par_puits):
    delta_names = ['ΔAmi', 'ΔFsk/IBMX', 'ΔVX770', 'ΔApi', 'ΔInh', 'ΔATP']
    colors = {'GT': 'blue', 'Ieq': 'green', 'Iraw': 'orange', 'PD': 'red', 'RT': 'purple'}

    # Parcourir chaque puits et créer un histogramme pour chaque type de delta
    for well, deltas in deltas_par_puits.items():
        fig, axs = plt.subplots(5, 1, figsize=(10, 20), sharex=True)

        # Pour chaque mesure (GT, Ieq, Iraw, PD, RT)
        for i, measure in enumerate(['GT', 'Ieq', 'Iraw', 'PD', 'RT']):
            values = []
            for delta_name in delta_names:
                values.append(deltas[delta_name][measure])

            values_log = np.log10(np.abs(values) + 1e-10)  # convertir en log et 1e-10 pour pas avoir log(0)
            # Barres de l'histogramme en échelle log
            x = np.arange(len(delta_names))
            axs[i].bar(x, values_log, color=colors[measure])
            axs[i].set_ylabel(measure + ' (log scale)')
            axs[i].set_xticks(x)
            axs[i].set_xticklabels(delta_names)
            axs[i].set_title(f"{well}: {measure} Delta Histogram (log scale)")
        
        plt.tight_layout()
        plt.show() # Bloque jusqu'à ce que la fenêtre soit fermée
        break
#plot_deltas_histograms(deltas_par_puits)
"""

#avec seaborn
sns.set_style('darkgrid', {'grid.linestyle': '--'})
colors = sns.color_palette("tab10", 8)
units = {'GT': 'GT(mSiemens)', 'Ieq': 'Ieq(μA.cm²)', 'Iraw': 'Iraw(μA.cm²)', 'PD': 'PD(μV)', 'RT': 'RT(kΩ.cm²)'}
measures = ['GT', 'Ieq', 'Iraw', 'PD', 'RT']

def plot_histo_par_puits(deltas_par_puits):
    for well, deltas in deltas_par_puits.items():
        fig, axs = plt.subplots(5, 1, figsize=(10, 15))
        fig.suptitle(f'Deltas pour le puit {well}', fontsize=16)
        
        for i, measure in enumerate(measures):
            data_list = []
            for delta_name, delta_values in deltas.items():
                data_list.append({'Delta': delta_name, 'Value': delta_values[measure]})
            
            data = pd.DataFrame(data_list)
            
            if not data.empty:
                sns.histplot(data=data, x='Delta', weights='Value', multiple='dodge', ax=axs[i], color=colors[i])
                axs[i].set_ylabel(units[measure], fontsize=9)
                axs[i].set_xlabel('Delta', fontsize=9)
                axs[i].tick_params(axis='x', rotation=0, labelsize=8)
        
        fig.canvas.manager.set_window_title(f"Puits {well}")
        
        if well == 'D6':
            def on_close(event):
                plt.close('all')  # Ferme toutes les fenêtres

            fig.canvas.mpl_connect('close_event', on_close)

        plt.tight_layout(rect=[0, 0, 1, 0.96])
        plt.subplots_adjust(hspace=0.5)
    plt.show() #bloque jusqu'à ce que la fenêtre se ferme 

plot_histo_par_puits(deltas_par_puits)
print("Fin du programme.")





