import sqlite3
import pandas as pd
from sqlalchemy import create_engine
import numpy as np
import yfinance as yf
import streamlit as st
from datetime import datetime
import altair as alt
import os


def loaddata():
    # Maak connectie met de database en geef de locaties aan van de input bestanden
    conn = sqlite3.connect('DatabaseVB.db')
    posdirectory = './Input/Posrecon'
    tradedirectory = './Input/Traderecon'
    
    # Loop over de input bestanden en laad ze in de database
    for file in os.listdir(posdirectory):
        df = pd.read_csv(posdirectory+'/'+file)
        df.to_sql('Posrecon', if_exists = "append", con = conn)
    
    for file in os.listdir(tradedirectory):
        df = pd.read_csv(tradedirectory+'/'+file)
        df.to_sql('Traderecon', if_exists = "append", con = conn)


@st.cache
def GetRendement(x):
    #conn = sqlite3.connect('DatabaseVB.db')
    engine = create_engine('sqlite:///DatabaseVB.db')
    ### Lees POSRECON in en sla deze op in de database
    #df = pd.read_csv('Input/Posrecon.csv', parse_dates = True)#
    #df.to_sql('BalansDB', if_exists = "replace", con = conn)
    
    df_posrecon = pd.read_sql(f'''SELECT "Datum", ROUND(sum("Waarde EUR"),2) as "Eind Waarde" 
                      FROM "Posrecon" where "RekNr" = "{x}" group by "Datum" order by "Datum"''', con = engine).set_index('Datum')

    ### Lees TRADERECON in en sla deze op in de database
    # df_traderecon = pd.read_csv('Input/Traderecon.csv', parse_dates = True, )#decimal = ','
    # df_traderecon.to_sql('BalansTraderecon', if_exists = 'replace' , con = conn)
    
    ### LEES UIT DE DATABASE DE SOM VAN DE ONTTREKKINGEN / OVERBOEKINGEN / LICHTINGEN / STORTINGEN VOOR REKNR X
    df_onttrekking = pd.read_sql(f''' Select Datum, sum("Aantal") as "Onttrekkingen" from Traderecon
                       where RekNr = "{x}" and "Unnamed: 34" = 5025 OR "Unnamed: 34" = 5000 group by "Datum" ''', con = engine).set_index('Datum')

    df_stortingen = pd.read_sql(f''' Select Datum, sum("Aantal") as "Stortingen" from Traderecon
                       where RekNr = "{x}"  and "Unnamed: 34" = 5026 group by "Datum" ''', con = engine).set_index('Datum')

    df_lichtingen = pd.read_sql(f''' Select Datum, sum("Aantal") as "Lichtingen" from Traderecon
                        where RekNr = "{x}" and "Type" = "L" group by "Datum" ''', con = engine).set_index('Datum')

    df_deponeringen = pd.read_sql(f''' Select Datum, sum("Aantal") as "Deponeringen" from Traderecon
                        where RekNr = "{x}" and "Type" = "D" group by "Datum" ''', con = engine).set_index('Datum')
    
    # Concat de 4 dataframes uit de Traderecon query in 1 dataframe en merge deze met de Posrecon dataframe
    traderecon_data = [df_onttrekking, df_stortingen, df_lichtingen, df_deponeringen]
    df_tot_tr = pd.concat(traderecon_data)
    df_final = df_posrecon.merge(df_tot_tr, on='Datum', how='left')
    
    ### VOEG DE OVERBOEKINGEN AAN DE DATAFRAME MET DE WAARDES PORTEFEUILLE
    traderecon_columns = ['Onttrekkingen','Stortingen', 'Lichtingen','Deponeringen']
    df_final[traderecon_columns] = df_final[traderecon_columns].fillna(0.0)
    
    ### MAAK KOLOM ACTUELE RENDEMENT EN BEREKEN RENDEMENT VAN WAARDE PORTEFEUILLE EN ONTTREKKINGEN / STORTINGEN
    df_final['Start Waarde'] = df_final["Eind Waarde"].shift(1)
    df_final['Dag Rendement'] = ((df_final['Eind Waarde'] - df_final['Start Waarde'] - df_final['Stortingen'] - df_final['Deponeringen'] + df_final['Onttrekkingen'] + df_final['Lichtingen'] ) ) / (df_final['Start Waarde'] + df_final['Stortingen'] - df_final['Onttrekkingen']).round(5)
    df_final['Portfolio Cumulatief Rendement'] = (1 + df_final['Dag Rendement']).cumprod()
    #df_final['Eind Waarde'] =  pd.to_numeric(df_final['Eind Waarde'], downcast = 'float')
    columns = ['Start Waarde','Stortingen','Deponeringen', 'Onttrekkingen', 'Lichtingen', 'Eind Waarde', 'Dag Rendement', 'Portfolio Cumulatief Rendement']
    
    return df_final[columns]

@st.cache
def GetBenchmark(data, name_bench):
    ticker = yf.Ticker(name_bench)
    df_benchmark = ticker.history(period = 'max').reset_index()
    df_benchmark = df_benchmark.rename(columns = {'Date':'Datum', 'Close': f'{name_bench} Eind Waarde'})
    df_benchmark[f'{name_bench} Dag Rendement'] = df_benchmark[f'{name_bench} Eind Waarde'].pct_change().round(5)
    df_benchmark['Datum'] = pd.to_datetime(df_benchmark['Datum'])
    final_df_benchmark = df_benchmark[['Datum', f'{name_bench} Eind Waarde', f'{name_bench} Dag Rendement']].set_index('Datum')
    df_bal_bench = data.join(final_df_benchmark)
    cols = [f'{name_bench} Eind Waarde', f'{name_bench} Dag Rendement']
    df[cols] = df_bal_bench[cols].fillna(method = 'ffill')
    return df

periode = {
    'Q1':
    {'start':'2020-01-02',
    'end':'2020-03-31'},
    'Q2':
    {'start':'2020-01-06',
    'end':'2020-03-25'},
    'Q3':
    {'start':'2020-02-03',
    'end':'2020-03-31'},
    'Q4':
    {'start':'2020-10-01',
    'end':'2020-12-31'},
    'YTD':
    {'start':'2020-01-01',
    'end':datetime.today().strftime('%Y-%m-%d')}
}

# Overview portefeuille Ontwikkeling
@st.cache
def GetOverview(data, kwartaals): 
    startwaarde, stortingen, deponeringen, onttrekkingen, lichtingen,eindwaarde = [],[],[],[],[],[]
    for kwartaal in kwartaals:
        startwaarde.append(data.loc[periode[kwartaal]['start'],['Start Waarde']][0])
        stortingen.append((data.loc[periode[kwartaal]['start']:periode[kwartaal]['end'],['Stortingen']]).sum()[0])
        deponeringen.append((data.loc[periode[kwartaal]['start']:periode[kwartaal]['end'],['Deponeringen']]).sum()[0])
        onttrekkingen.append((data.loc[periode[kwartaal]['start']:periode[kwartaal]['end'],['Onttrekkingen']]).sum()[0])
        lichtingen.append((data.loc[periode[kwartaal]['start']:periode[kwartaal]['end'],['Lichtingen']]).sum()[0])
        eindwaarde.append(data.loc[periode[kwartaal]['end'],['Eind Waarde']][0])
    overview = list(zip(startwaarde, stortingen, deponeringen, onttrekkingen, lichtingen, eindwaarde))
    
    df = pd.DataFrame(overview, 
           columns=["Start Waarde","Stortingen","Deponeringen","Onttrekkingen","Lichtingen","Eind Waarde"], index = kwartaals)
    df['Abs Rendement'] = df['Eind Waarde'] - df['Start Waarde'] - df['Stortingen'] - df['Deponeringen'] + df['Onttrekkingen'] + df['Lichtingen']
    df['Rendement'] = (df['Eind Waarde'] - df['Start Waarde']) / df['Start Waarde']
    return df

#Full Benchmark data
@st.cache(allow_output_mutation=True)
def getBenchmarkData(bench):
    conn = sqlite3.connect('DatabaseVB.db')
    engine = create_engine('sqlite:///DatabaseVB.db')
    ticker = yf.Ticker(bench)

    df_benchmark = ticker.history(period = 'max')
    df_benchmark.reset_index(inplace = True)
    df_benchmark.rename(columns = {'Date':'Datum', 'Close': f'{bench} Eind Waarde'}, inplace = True)
    df_benchmark.to_sql(f'{bench}', if_exists = 'replace', con = conn)

    df = pd.read_sql(f'''
    SELECT substr(Datum, 1, 10) as "Datum", "{bench} Eind Waarde" FROM "{bench}"
    ''', con = engine).set_index("Datum")
    return df

#Overview Benchmark Ontwikkeling
@st.cache
def getPerf(data, kwartaals, bench):
    kwart, startwaarde, eindwaarde = [], [], []
    for kwartaal in kwartaals:
        kwart.append(kwartaal)
        startwaarde.append(data.loc[periode[kwartaal]['start']][0])
        eindwaarde.append(data.loc[periode[kwartaal]['end']][0])

        overview = list(zip(kwart, startwaarde, eindwaarde))


        df = pd.DataFrame(overview, columns=['Kwartaal','Start Waarde','Eind Waarde'],
                         index = kwart)
        
        df['Benchmark Performance'] = (df['Eind Waarde'] - df['Start Waarde']) / df['Start Waarde']     
    return df


def Graph(data, benchmark, ticker, period):
    sorted_periode = sorted(period)
    benchmark['Benchmark Dag Rendement'] = benchmark[f'{ticker} Eind Waarde'].pct_change(4)

    df_port_bench = data.merge(benchmark, on='Datum', how='left')

    df_port_bench['Benchmark Cumulatief Rendement'] = (1 + df_port_bench['Benchmark Dag Rendement']).cumprod()
    df_port_bench['Benchmark Cumulatief Rendement'].fillna(method='ffill', inplace = True)
    df_base = df_port_bench[['Portfolio Cumulatief Rendement', 'Benchmark Cumulatief Rendement']]
    
    if len(period) > 1:
        start = periode[sorted_periode[0]]['start']
        end = periode[sorted_periode[-1]]['end']
    else:
        start = periode[sorted_periode[0]]['start']
        end = periode[sorted_periode[0]]['end']

    df = df_base.loc[start:end]

    dfn = df.reset_index().melt('Datum')
    dfn1 = alt.Chart(dfn).mark_line().encode(
        x = ('Datum:T'),
        y = ('value:Q'),
        color='variable:N').properties(
            height=500,
            width=750).interactive()

    graph = st.altair_chart(dfn1) 

    return graph

