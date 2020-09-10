import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime
import yfinance as yf
from Balans1908 import *



st.sidebar.markdown("# Balans Vermogensbeheer Amsterdam")

if st.sidebar.button('Read the files in the Input folder'):
	loaddata()

reknr = st.sidebar.text_input("Rekening nummer")
df = GetRendement(reknr)

st.sidebar.markdown("# Periode")
st.markdown("## Portefeuille Ontwikkeling")
periode_keuze = st.sidebar.multiselect("Selecteer de gewenste periode voor de portefeuille ontwikkeling", ['Q1','Q2','Q3','Q4'], default=["Q1"])
df_port_ont = st.table(GetOverview(df, periode_keuze))

st.sidebar.markdown("# Benchmark")

benchmark_keuze = st.sidebar.selectbox('Selecteer de Benchmark', ['^AEX','SPYY.DE','IUSQ.DE'])

st.markdown(f"## Benchmark Ontwikkeling {benchmark_keuze}")

full_bench_df = getBenchmarkData(benchmark_keuze)

df_bench_ont = st.table(getPerf(full_bench_df, periode_keuze, benchmark_keuze))

bench_spy = getBenchmarkData("SPYY.DE")

bench_aex = getBenchmarkData("^AEX")

bench_iusq = getBenchmarkData("IUSQ.DE")

Graph(df, getBenchmarkData(benchmark_keuze), benchmark_keuze, periode_keuze)


