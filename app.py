import streamlit as st
import pulp
import pandas as pd
import plotly.graph_objects as go

# Set up page configurations
st.set_page_config(page_title="Whiskas Optimizer", layout="wide")

# App Header matching your sketch
st.title("Whiskas Optimization Dashboard")
st.markdown("---")

# ----------------------------------------------------
# Sidebar Inputs (Allow user to adjust constraints/costs)
# ----------------------------------------------------
st.sidebar.header("Optimization Constraints & Costs")

st.sidebar.subheader("Ingredient Costs (£ per g)")
cost_chicken = st.sidebar.slider("Chicken Cost", 0.001, 0.020, 0.013, step=0.001)
cost_beef = st.sidebar.slider("Beef Cost", 0.001, 0.020, 0.008, step=0.001)

st.sidebar.subheader("Nutritional Targets (%)")
min_protein = st.sidebar.slider("Minimum Protein Required", 5.0, 15.0, 8.0, step=0.5)
min_fat = st.sidebar.slider("Minimum Fat Required", 1.0, 10.0, 6.0, step=0.5)

# ----------------------------------------------------
# PuLP Linear Programming Solver
# ----------------------------------------------------
# Create the optimization problem (Minimize cost)
prob = pulp.LpProblem("The_Whiskas_Problem", pulp.LpMinimize)

# Decision Variables (Percentages of Chicken and Beef in the 100g can)
x1 = pulp.LpVariable("ChickenPercent", lowBound=0, upBound=100)
x2 = pulp.LpVariable("BeefPercent", lowBound=0, upBound=100)

# Objective Function: Minimize Total Cost
prob += cost_chicken * x1 + cost_beef * x2, "Total_Cost_per_Can"

# Constraints
prob += x1 + x2 == 100, "Percentage_Sum_Constraint"
# Nutritional composition data (Standard Whiskas problem values)
prob += 0.100 * x1 + 0.200 * x2 >= min_protein, "Protein_Constraint"
prob += 0.080 * x1 + 0.100 * x2 >= min_fat, "Fat_Constraint"

# Solve the problem
status = prob.solve(pulp.PULP_CBC_CMD(msg=False))

# Extract results safely
if pulp.LpStatus[status] == "Optimal":
    opt_chicken = round(x1.varValue, 1)
    opt_beef = round(x2.varValue, 1)
    # Total cost of a 100g can
    total_cost = round(pulp.value(prob.objective), 2)
else:
    # Fallback if constraints are impossible to meet
    opt_chicken, opt_beef, total_cost = 0, 0, 0.0

# ----------------------------------------------------
# UI Layout (Directly mirroring your paper sketch)
# ----------------------------------------------------

# Split screen into Left Column ("Mix") and Right Column (Metrics & Details)
col_mix, col_details = st.columns([2, 3], gap="large")

# LEFT COLUMN: The "Mix" Block with Donut Chart
with col_mix:
    st.header("Mix")
    
    if total_cost > 0:
        # Donut Chart representing the 60%/40% style split from drawing
        labels = ['Chicken', 'Beef']
        values = [opt_chicken, opt_beef]
        
        fig = go.Figure(data=[go.Pie(
            labels=labels, 
            values=values, 
            hole=0.5, # Generates the inner ring center from your drawing
            marker=dict(colors=['#ff9999', '#66b3ff']),
            textinfo='percent+label'
        )])
        
        fig.update_layout(
            showlegend=False,
            margin=dict(t=10, b=10, l=10, r=10),
            height=320
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.error("No optimal mix found for the selected parameters. Adjust constraints in the sidebar.")

# RIGHT COLUMN: Stacked Cards/Containers
with col_details:
    
    # 1. Unit Cost Card
    st.metric(
        label="Unit Cost (per 100g can)", 
        value=f"£{total_cost:,.2f}"
    )
    
    # 2. Ingredients Expander
    with st.expander("Ingredients Breakdown", expanded=True):
        if total_cost > 0:
            st.write("Optimal material allocation to achieve minimum cost:")
            ingredients_data = {
                "Ingredient": ["Chicken", "Beef"],
                "Optimal Blend Ratio": [f"{opt_chicken}%", f"{opt_beef}%"],
                "Weight per Can": [f"{opt_chicken}g", f"{opt_beef}g"]
            }
            st.table(pd.DataFrame(ingredients_data))
        else:
            st.write("N/A - Adjust constraints.")

    # 3. Nutrients Expander
    with st.expander("Nutritional Compliance status", expanded=True):
        if total_cost > 0:
            # Calculate final nutritional content achieved
            achieved_protein = (0.100 * opt_chicken) + (0.200 * opt_beef)
            achieved_fat = (0.080 * opt_chicken) + (0.100 * opt_beef)
            
            st.success(f"✔️ Protein Target Met: {achieved_protein:.1f}% (Required: ≥ {min_protein}%)")
            st.success(f"✔️ Crude Fat Target Met: {achieved_fat:.1f}% (Required: ≥ {min_fat}%)")
        else:
            st.write("N/A - Adjust constraints.")
