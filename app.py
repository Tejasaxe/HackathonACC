import pandas as pd
import streamlit as st
from src.parsing.parser import parse_pdf

st.title("Financial Statement Analyzer")

st.header("Upload Financial Statements")

col1, col2, col3 = st.columns(3)

with col1:
    income_statement = st.file_uploader("Income Statement", type="pdf")

with col2:
    balance_sheet = st.file_uploader("Balance Sheet", type="pdf")

with col3:
    cash_flow = st.file_uploader("Cash Flow Statement", type="pdf")

if st.button("Parse Statements"):
    if income_statement:
        st.subheader("Income Statement Data")
        text = parse_pdf(income_statement)
        st.text_area("Income Statement Text", text, height=200)
    
    if balance_sheet:
        st.subheader("Balance Sheet Data")
        text = parse_pdf(balance_sheet)
        st.text_area("Balance Sheet Text", text, height=200)

    if cash_flow:
        st.subheader("Cash Flow Data")
        text = parse_pdf(cash_flow)
        st.text_area("Cash Flow Text", text, height=200)
