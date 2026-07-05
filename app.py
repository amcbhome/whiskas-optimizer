import streamlit as st
import pulp
import pandas as pd
import plotly.graph_objects as go

# Set up page configurations
st.set_page_config(page_title="Whiskas Optimizer", layout="wide")

# Custom CSS to inject to style our blocks as "Cards"
st.markdown("""
    <style>
    /* Style for the visual containers to look like independent cards */
    div[data-testid="stVerticalBlock"] > div:has(div.card-wrapper) {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        border: 1px solid #e6e9ef;
        margin-bottom: 20px;
    }
    /* Style specifically for the big Unit Cost metric card */
    div[data-testid="stMetricValue"] {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f77b4;
    }
    </style>
    """, unsafe_allow_html=True)

# App Header matching your sketch
st.title("Whiskas Optimization Dashboard")
st.markdown("---")

# ----------------------------------------------------
# Sidebar Inputs
# ----------------------------------------------------
st.sidebar.header("Optimization Constraints")
cost_chicken = st.sidebar.slider("Chicken Cost (£/g)", 0.001, 0.020, 0.013, step=0.001)
cost_beef = st.sidebar.slider("Beef Cost (£/g)", 0.001, 0.020, 0.008, step=0.001)

min_protein = st.sidebar.slider("Minimum Protein Required (%)", 5.0, 15.0, 8.0, step=0.5)
min_fat = st.sidebar.slider("Minimum Fat Required (%)", 1.0, 10.0, 6.0, step=0.5)

# ----------------------------------------------------
# PuLP Linear Programming Solver
# ----------------------------------------------------
prob = pulp.LpProblem("The_Whiskas_Problem", pulp.LpMinimize)
x1 = pulp.LpVariable("ChickenPercent", lowBound=0, upBound=100)
x2 = pulp.LpVariable("BeefPercent", lowBound=0, upBound=100)

prob += cost_chicken * x1 + cost_beef * x2, "Total_Cost_per_Can"
prob += x1 + x2 == 100, "Percentage_Sum_Constraint"
prob += 0.100 * x1 + 0.200 * x2 >= min_protein, "Protein_Constraint"
prob += 0.080 * x1 + 0.100 * x2 >= min_fat, "Fat_Constraint"

status = prob.solve(pulp.PULP_CBC_CMD(msg=False))

if pulp.LpStatus[status] == "Optimal":
    opt_chicken = round(x1.varValue, 1)
    opt_beef = round(x2.varValue, 1)
    total_cost = round(pulp.value(prob.objective), 2)
else:
    opt_chicken, opt_beef, total_cost = 0, 0, 0.0

# ----------------------------------------------------
# UI Layout (Cards Architecture)
# ----------------------------------------------------

col_mix, col_details = st.columns([2, 3], gap="large")

# LEFT COLUMN CARD: The "Mix" Donut Chart Card
with col_mix:
    # Creating a container box
    with st.container():
        # HTML marker to apply our custom CSS wrapper style
        st.markdown('<div class="card-wrapper"></div>', unsafe_allow_html=True)
        st.subheader("Mix Breakdown")
        
        if total_cost > 0:
            labels = ['Chicken', 'Beef']
            values = [opt_chicken, opt_beef]
            
            fig = go.Figure(data=[go.Pie(
                labels=labels, 
                values=values, 
                hole=0.5, # The donut ring hole from your drawing
                marker=dict(colors=['#ff9999', '#66b3ff']),
                textinfo='percent+label'
            )])
            
            fig.update_layout(
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
                margin=dict(t=10, b=10, l=10, r=10),
                height=300
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.error("No optimal mix found. Adjust constraints.")

# RIGHT COLUMN CARDS: Vertically stacked cards matching your blueprint
with col_details:
    
    # CARD 1: Unit Cost Card
    with st.container():
        st.markdown('<div class="card-wrapper"></div>', unsafe_allow_html=True)
        st.metric(
            label="Optimized Unit Cost (per Can)", 
            value=f"£{total_cost:,.2f}"
        )
    
    # CARD 2: Ingredients Card
    with st.container():
        st.markdown('<div class="card-wrapper"></div>', unsafe_allow_html=True)
        st.subheader("Ingredients Allocation")
        if total_cost > 0:
            ingredients_data = {
                "Ingredient": ["Chicken", "Beef"],
                "Optimal Ratio": [f"{opt_chicken}%", f"{opt_beef}%"],
                "Mass (per 100g)": [f"{opt_chicken}g", f"{opt_beef}g"]
            }
            st.table(pd.DataFrame(ingredients_data))
        else:
            st.write("N/A")

    # CARD 3: Nutrients Card
    with st.container():
        st.markdown('<div class="card-wrapper"></div>', unsafe_allow_html=True)
        st.subheader("Nutrients Target Compliance")
        if total_cost > 0:
            achieved_protein = (0.100 * opt_chicken) + (0.200 * opt_beef)
            achieved_fat = (0.080 * opt_chicken) + (0.100 * opt_beef)
            
            st.success(f"✔️ Protein Content: {achieved_protein:.1f}% (Required: ≥ {min_protein}%)")
            st.success(f"✔️ Crude Fat Content: {achieved_fat:.1f}% (Required: ≥ {min_fat}%)")
        else:
            st.write("N/A")
