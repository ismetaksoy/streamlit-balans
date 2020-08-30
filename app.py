import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime
import yfinance as yf
from Balans1908 import *
import matplotlib.pyplot as plt

st.sidebar.markdown("# Balans Vermogensbeheer Amsterdam")
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


# chart = alt.Chart(df.reset_index()).mark_line().encode(
# 	x = alt.X('Datum:T', axis=alt.Axis(title='Date', format=("%d %b %Y"))),
# 	y = alt.Y('Eind Waarde:Q')).properties(
#            height=500,
#            width=750
#            ).interactive()

# st.altair_chart(chart)

# chart1 = alt.Chart(df.reset_index()).mark_line().encode(
# 	x = alt.X('Datum:T', axis=alt.Axis(title='Datum', format=("%d %b %Y"))),
# 	y = alt.Y('Cumulatief Rendement:Q')).properties(
# 		height=500,
# 		width=750).interactive()

# st.altair_chart(chart1)

# #""" Encoding Data Types
# #quantitative Q   a continuous real-valued quantity - quantitative scales always start at zero unless otherwise specified
# #ordinal 	 	O 	a discrete ordered quantity		  - ordinal scales are limited to the values within the data
# #nominal		N	a discrete unordered category
# #temporal 	T	a time or date value
# #geojson		G	a geographic shape """


bench_spy = getBenchmarkData("SPYY.DE")

bench_aex = getBenchmarkData("^AEX")

bench_iusq = getBenchmarkData("IUSQ.DE")

Graph(df, getBenchmarkData(benchmark_keuze), benchmark_keuze, periode_keuze)