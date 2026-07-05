import streamlit as st
import pulp
import pandas as pd
import altair as alt

# 1. Page Configuration & Custom Styling
st.set_page_config(page_title="Whiskas Optimizer", layout="wide", initial_sidebar_state="expanded")

# Injecting Custom CSS to match the provided dashboard aesthetic
st.markdown("""
    <style>
    /* Main background and text */
    .stApp {
        background-color: #1a1a1c;
        color: #ffffff;
    }
    
    /* Styling the metric cards (The Grid and New Chart Panel) */
    [data-testid="stMetric"], [data-testid="stAltairChart"] {
        background-color: #262628;
        border: 1px solid #3e3e42;
        border-radius: 12px;
        padding: 15px 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    
    /* Metric Labels (Targeting the pale yellow from the image) */
    [data-testid="stMetricLabel"] {
        color: #e5f396 !important;
        font-size: 1.1rem !important;
        font-weight: 600;
    }
    
    /* Metric Values (Targeting the purple accent) */
    [data-testid="stMetricValue"] {
        color: #aa85f8 !important;
        font-weight: 800;
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #e5f396;
    }
    
    /* Ensure chart panel gets correct card styling */
    [data-testid="stAltairChart"] {
        padding: 0; /* Let Altair handle its padding */
    }
    </style>
""", unsafe_allow_html=True)

st.title("Dashboard Infographic: Whiskas Optimization")
st.markdown("---")

# 2. Sidebar for User Inputs
st.sidebar.header("Model Parameters")

st.sidebar.subheader("Constraint Limits")
req_protein = st.sidebar.number_input("Minimum Protein (g)", value=8.0, step=0.5)
req_fat = st.sidebar.number_input("Minimum Fat (g)", value=6.0, step=0.5)
max_fibre = st.sidebar.number_input("Maximum Fibre (g)", value=2.0, step=0.1)
max_salt = st.sidebar.number_input("Maximum Salt (g)", value=0.4, step=0.05)

st.sidebar.subheader("Ingredient Costs (£/g)")
cost_beef = st.sidebar.number_input("Beef Cost", value=0.008, format="%.3f")
cost_chicken = st.sidebar.number_input("Chicken Cost", value=0.013, format="%.3f")
cost_mutton = st.sidebar.number_input("Mutton Cost", value=0.010, format="%.3f")
cost_rice = st.sidebar.number_input("Rice Cost", value=0.002, format="%.3f")
cost_wheat = st.sidebar.number_input("Wheat Bran Cost", value=0.005, format="%.3f")
cost_gel = st.sidebar.number_input("Gel Cost", value=0.001, format="%.3f")

# 3. Data Setup
Ingredients = ['Chicken', 'Beef', 'Mutton', 'Rice', 'Wheat_bran', 'Gel']
costs = {'Chicken': cost_chicken, 'Beef': cost_beef, 'Mutton': cost_mutton, 'Rice': cost_rice, 'Wheat_bran': cost_wheat, 'Gel': cost_gel}
protein = {'Chicken': 0.100, 'Beef': 0.200, 'Mutton': 0.150, 'Rice': 0.000, 'Wheat_bran': 0.040, 'Gel': 0.000}
fat = {'Chicken': 0.080, 'Beef': 0.100, 'Mutton': 0.110, 'Rice': 0.010, 'Wheat_bran': 0.010, 'Gel': 0.000}
fibre = {'Chicken': 0.001, 'Beef': 0.005, 'Mutton': 0.003, 'Rice': 0.100, 'Wheat_bran': 0.150, 'Gel': 0.000}
salt = {'Chicken': 0.002, 'Beef': 0.005, 'Mutton': 0.007, 'Rice': 0.002, 'Wheat_bran': 0.008, 'Gel': 0.000}

# 4. PuLP Model Execution
prob = pulp.LpProblem("Whiskas_Optimization", pulp.LpMinimize)
x = pulp.LpVariable.dicts("Mix", Ingredients, lowBound=0, cat='Continuous')

# Objective
prob += pulp.lpSum([costs[i] * x[i] for i in Ingredients])

# Constraints
prob += pulp.lpSum([x[i] for i in Ingredients]) == 100
prob += pulp.lpSum([protein[i] * x[i] for i in Ingredients]) >= req_protein
prob += pulp.lpSum([fat[i] * x[i] for i in Ingredients]) >= req_fat
prob += pulp.lpSum([fibre[i] * x[i] for i in Ingredients]) <= max_fibre
prob += pulp.lpSum([salt[i] * x[i] for i in Ingredients]) <= max_salt

prob.solve()

# 5. Dashboard Display Logic
if pulp.LpStatus[prob.status] == 'Optimal':
    
    # Top Row: Primary KPI
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.metric(label="Optimal Minimum Cost (Per 100g)", value=f"£{pulp.value(prob.objective):.2f}")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Second Row: Optimized Ingredient Mix Composition (Chart + Metrics)
    st.subheader("Optimized Mix Composition")
    
    # Create the 1x2 column layout for the Mix section
    mix_chart_col, mix_metrics_col = st.columns([1, 1.5])
    
    # Column A: Doughnut Chart
    with mix_chart_col:
        # Prepare Data for Chart
        df_mix = pd.DataFrame({
            'Ingredient': [ing.replace("_", " ") for ing in Ingredients],
            'Grams': [max(0.0, x[ing].varValue) for ing in Ingredients],
            'Percent': [max(0.0, x[ing].varValue) for ing in Ingredients] # Grams/100 * 100 is just Grams
        })
        
        # Define Custom Color Palette (Neon yellow and purple, matching aesthetic)
        neon_colors = ["#A678E2", "#FFFC99", "#8EE6D5", "#98E68D", "#89E6E3", "#94E2E0"] 
        custom_scale = alt.Scale(domain=df_mix['Ingredient'].tolist(), range=neon_colors[:len(Ingredients)])

        # Create Doughnut Chart Base
        base = alt.Chart(df_mix).encode(
            theta=alt.Theta("Grams", stack=True),
            color=alt.Color("Ingredient", scale=custom_scale, legend=alt.Legend(title="Ingredients", orient="right", titleColor="#ffffff", labelColor="#ffffff")),
            order=alt.Order("Grams", sort="descending"),
            tooltip=["Ingredient", alt.Tooltip("Percent", format=".1f%%"), alt.Tooltip("Grams", format=".1fg")]
        ).properties(
            title={"text": "Ingredient % Breakdown", "color": "#e5f396", "fontSize": 16},
            background="#262628" # Match card background
        )
        
        doughnut = base.mark_arc(innerRadius=60, stroke="#3e3e42", strokeWidth=1).interactive()
        
        # Add labels directly to the segments (FIX APPLIED HERE)
        text = base.mark_text(radius=80, fill="#ffffff", fontSize=12).encode(
            text=alt.Text("Percent", format=".1f%%"),
            order=alt.Order("Grams", sort="descending")
        )
        
        chart_final = (doughnut + text).configure_view(strokeWidth=0).configure_title(fontSize=18, color="#e5f396", anchor='start')
        
        st.altair_chart(chart_final, use_container_width=True)

    # Column B: The grid of individual metric cards for grams
    with mix_metrics_col:
        mix_grid_cols = st.columns(6)
        for idx, ing in enumerate(Ingredients):
            with mix_grid_cols[idx]:
                val = x[ing].varValue
                # Ensure no small negative numbers from solver
                display_val = max(0.0, val)
                st.metric(label=ing.replace("_", " "), value=f"{display_val:.1f}g")

    st.markdown("<br>", unsafe_allow_html=True)

    # Third Row: Final Nutritional Values vs Constraints
    st.subheader("Nutritional Breakdown")
    nut_col1, nut_col2, nut_col3, nut_col4 = st.columns(4)
    
    final_prot = sum([protein[i] * max(0.0, x[i].varValue) for i in Ingredients])
    final_fat = sum([fat[i] * max(0.0, x[i].varValue) for i in Ingredients])
    final_fib = sum([fibre[i] * max(0.0, x[i].varValue) for i in Ingredients])
    final_salt = sum([salt[i] * max(0.0, x[i].varValue) for i in Ingredients])
    
    with nut_col1:
        st.metric(label="Total Protein (g)", value=f"{final_prot:.2f}", delta=f"Min: {req_protein}", delta_color="off")
    with nut_col2:
        st.metric(label="Total Fat (g)", value=f"{final_fat:.2f}", delta=f"Min: {req_fat}", delta_color="off")
    with nut_col3:
        st.metric(label="Total Fibre (g)", value=f"{final_fib:.2f}", delta=f"Max: {max_fibre}", delta_color="inverse")
    with nut_col4:
        st.metric(label="Total Salt (g)", value=f"{final_salt:.3f}", delta=f"Max: {max_salt}", delta_color="inverse")

else:
    st.error("No optimal solution found with the current constraints. Try relaxing the limits in the sidebar.")
