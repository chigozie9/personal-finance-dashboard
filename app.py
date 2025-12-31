import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import os

DATA_FILE = "data/sample_transactions.csv"

# ---------- Data load / init ----------
os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)

if not os.path.exists(DATA_FILE):
    df = pd.DataFrame(columns=["date", "description", "amount", "category", "type"])
    df.to_csv(DATA_FILE, index=False)
else:
    df = pd.read_csv(DATA_FILE)
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")

st.set_page_config(page_title="Finance Dashboard", layout="wide")
st.title("💰 Personal Finance Dashboard")

# ---------- Sidebar: Add transaction ----------
with st.sidebar:
    st.header("Add New Transaction")
    date = st.date_input("Date", datetime.now())
    description = st.text_input("Description")
    amount = st.number_input("Amount", min_value=0.0, step=0.01)
    type_ = st.selectbox("Type", ["Income", "Expense"])
    category = st.selectbox(
        "Category",
        ["Salary", "Food", "Transport", "Entertainment", "Rent", "Utilities", "Shopping", "Other"],
        index=6,
    )

    if st.button("Add Transaction"):
        if description and amount > 0:
            new_row = {
                "date": date,
                "description": description,
                "amount": amount if type_ == "Income" else -amount,
                "category": category,
                "type": type_,
            }
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            df.to_csv(DATA_FILE, index=False)
            st.success("Transaction added!")
            st.rerun()
        else:
            st.error("Fill description and amount!")

# ---------- Tabs ----------
tab1, tab2, tab3 = st.tabs(["📊 Overview", "📋 Transactions", "📈 Insights"])

with tab1:
    if df.empty:
        st.info("No transactions yet. Add one from the sidebar.")
    else:
        # Ensure datetime
        df["date"] = pd.to_datetime(df["date"], errors="coerce")

        balance = df["amount"].sum()
        st.metric("Current Balance", f"${balance:,.2f}", delta_color="normal")

        col1, col2 = st.columns(2)

        with col1:
            # Group by year-month as string for clean axis labels
            df["year_month"] = df["date"].dt.strftime("%Y-%m")
            monthly = df.groupby("year_month", as_index=False)["amount"].sum()
            monthly = monthly.sort_values("year_month")

            fig_line = px.line(
                monthly,
                x="year_month",
                y="amount",
                title="Monthly Net Flow",
                labels={"year_month": "Month", "amount": "Net Amount ($)"},
                markers=True,
            )
            fig_line.update_traces(line=dict(width=2))
            fig_line.update_layout(xaxis_title="Month", yaxis_title="Net ($)")
            st.plotly_chart(fig_line, use_container_width=True)

        with col2:
            # Make expenses a DataFrame (fix for px.pie values/names)
            expenses = (
                df.loc[df["amount"] < 0]
                .groupby("category", as_index=False)["amount"]
                .sum()
            )
            expenses["amount"] = expenses["amount"].abs()

            if expenses.empty:
                st.info("No expenses yet.")
            else:
                fig_pie = px.pie(
                    expenses,
                    values="amount",
                    names="category",
                    title="Expense Breakdown by Category",
                    hole=0.4,
                )
                fig_pie.update_traces(textposition="inside", textinfo="percent+label")
                st.plotly_chart(fig_pie, use_container_width=True)

with tab2:
    if df.empty:
        st.info("No transactions to show yet.")
    else:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        st.dataframe(df.sort_values("date", ascending=False), use_container_width=True)

with tab3:
    st.write("More insights coming soon: budgets, forecasts, auto-categorization...")

# ---------- Quick stats ----------
if not df.empty:
    st.subheader("Quick Stats")
    col_a, col_b, col_c = st.columns(3)

    total_income = df.loc[df["amount"] > 0, "amount"].sum()
    total_expenses = abs(df.loc[df["amount"] < 0, "amount"].sum())  # FIX: abs(...) not .abs() on numpy float
    txn_count = len(df)

    col_a.metric("Total Income", f"${total_income:,.2f}")
    col_b.metric("Total Expenses", f"${total_expenses:,.2f}")
    col_c.metric("Transactions", f"{txn_count}")
