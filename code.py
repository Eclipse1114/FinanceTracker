import pandas as pd
import sqlite3
import streamlit as st

st.markdonw("""
    .stApp {
        background-color: LightGreen;
        broder: solid;
        border-color: Cyan;
        border-width: 10px;
    }
""", unsafe_allow_html=True)

conn = sqlite3.connect("purchases.db", check_same_thread=False)
c = conn.cursor()
c.execute(
    """CREATE TABLE IF NOT EXISTS spending (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT,
        amount REAL,
        description TEXT,
        date TEXT
    )"""
)
conn.commit()

st.set_page_config(
    page_title="SpendSense",
    page_icon="💰",
    layout="wide"
)

# ============================================================
# CATEGORIES & BUDGETS
# ============================================================
default_categories = [
    "Transportation/Travel",
    "Games/Toys",
    "Food",
    "Clothing"
]

st.sidebar.header("⚙️ Budget Settings")
budgets = {}

for category in default_categories:
    budgets[category] = st.sidebar.number_input(
        category,
        min_value=0.0,
        value=100.0,
        step=10.0
    )

# Custom category
st.sidebar.divider()
st.sidebar.subheader("Custom Category")
custom_category = st.sidebar.text_input("Add your own category").strip()

if custom_category:
    if custom_category not in default_categories:
        default_categories.append(custom_category)
    budgets[custom_category] = st.sidebar.number_input(
        f"{custom_category} Budget",
        min_value=0.0,
        value=100.0,
        step=10.0
    )

# ============================================================
# TITLE
# ============================================================
st.title("💰 SpendSense")
st.caption("Track your spending. Set your limits. Stay in control.")

# ============================================================
# DASHBOARD STATISTICS
# ============================================================
c.execute("SELECT SUM(amount) FROM spending")
total = c.fetchone()[0] or 0

c.execute("SELECT COUNT(*) FROM spending")
purchases = c.fetchone()[0]

col1, col2, col3 = st.columns(3)
col1.metric("Total Spent", f"${total:.2f}")
col2.metric("Purchases", purchases)

c.execute("SELECT COUNT(DISTINCT category) FROM spending")
categories_used = c.fetchone()[0]
col3.metric("Categories Used", categories_used)

st.divider()

# ============================================================
# ADD PURCHASE
# ============================================================
st.subheader("➕ Add a Purchase")
col1, col2 = st.columns(2)

with col1:
    choice = st.selectbox("Category", default_categories)
    amount = st.number_input("Amount", min_value=0.0, step=0.01, format="%.2f")

with col2:
    description = st.text_input("What did you buy?")
    date = st.date_input("Purchase date")

if st.button("Add Purchase", type="primary"):
    if amount <= 0:
        st.error("Please enter an amount greater than $0.")
    elif not description.strip():
        st.error("Please enter a description.")
    else:
        c.execute(
            """INSERT INTO spending (category, amount, description, date) 
               VALUES (?, ?, ?, ?)""",
            (choice, amount, description.strip(), str(date))
        )
        conn.commit()
        st.success(f"Added ${amount:.2f} to {choice}!")
        st.rerun()

st.divider()

# ============================================================
# BUDGET PROGRESS
# ============================================================
st.subheader("📊 Budget Progress")
budget_status = []

for category in default_categories:
    c.execute(
        "SELECT SUM(amount) FROM spending WHERE category = ?",
        (category,)
    )
    spent = c.fetchone()[0] or 0
    budget = budgets.get(category, 100.0)
    
    if budget > 0:
        percentage = spent / budget
    else:
        percentage = 0
        
    budget_status.append((category, spent, budget, percentage))
    
    st.write(f"**{category}** — ${spent:.2f} / ${budget:.2f}")
    st.progress(min(percentage, 1.0))
    
    if spent > budget:
        st.warning(f"You're ${spent - budget:.2f} over your {category} budget.")
    elif percentage >= 0.8:
        st.info(f"You've used {percentage * 100:.0f}% of your {category} budget.")

# ============================================================
# BUDGET SUMMARY
# ============================================================
within_budget = sum(
    spent <= budget for category, spent, budget, percentage in budget_status
)
total_budgets = len(budget_status)
st.write(f"**Budget Status:** {within_budget}/{total_budgets} categories within budget.")

st.divider()

# ============================================================
# SPENDING BREAKDOWN
# ============================================================
c.execute(
    "SELECT category, SUM(amount) "
    "FROM spending "
    "GROUP BY category"
)
data = c.fetchall()

if data:
    st.subheader("💳 Spending Breakdown")
    df = pd.DataFrame(data, columns=["Category", "Total"]).set_index("Category")
    st.bar_chart(df)
else:
    st.info("No purchases yet. Add your first purchase above!")

st.divider()

# ============================================================
# RECENT PURCHASES
# ============================================================
c.execute(
    "SELECT category, amount, description, date "
    "FROM spending "
    "ORDER BY id DESC "
    "LIMIT 5"
)
recent = c.fetchall()

if recent:
    st.subheader("🧾 Recent Purchases")
    recent_df = pd.DataFrame(
        recent,
        columns=["Category", "Amount", "Description", "Date"]
    )
    recent_df["Amount"] = recent_df["Amount"].map(lambda x: f"${x:.2f}")
    st.dataframe(recent_df, hide_index=True, use_container_width=True)
