import streamlit as st
import pulp

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
    
    /* Styling the metric cards (The Grid) */
    [data-testid="stMetric"] {
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
    </style>
""", unsafe_allow_html=True)

st.title("Dashboard Infographic: Whiskas Optimization")
st.markdown("---")

# 2. Sidebar for User Inputs
st.sidebar.header("Model Parameters")

st.sidebar.subheader("Constraint Limits")
req_protein = st.sidebar.number_input("Minimum Protein", value=8.0, step=0.5)
req_fat = st.sidebar.number_input("Minimum Fat", value=6.0, step=0.5)
max_fibre = st.sidebar.number_input("Maximum Fibre", value=2.0, step=0.1)
max_salt = st.sidebar.number_input("Maximum Salt", value=0.4, step=0.05)

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
    
    # Second Row: Optimized Ingredient Mix
    st.subheader("Optimized Ingredient Mix")
    mix_cols = st.columns(6)
    for idx, ing in enumerate(Ingredients):
        with mix_cols[idx]:
            val = x[ing].varValue
            st.metric(label=ing.replace("_", " "), value=f"{val:.1f}g")

    st.markdown("<br>", unsafe_allow_html=True)

    # Third Row: Final Nutritional Values vs Constraints
    st.subheader("Nutritional Breakdown")
    nut_col1, nut_col2, nut_col3, nut_col4 = st.columns(4)
    
    final_prot = sum([protein[i] * x[i].varValue for i in Ingredients])
    final_fat = sum([fat[i] * x[i].varValue for i in Ingredients])
    final_fib = sum([fibre[i] * x[i].varValue for i in Ingredients])
    final_salt = sum([salt[i] * x[i].varValue for i in Ingredients])
    
    with nut_col1:
        st.metric(label="Total Protein", value=f"{final_prot:.2f}", delta=f"Min: {req_protein}", delta_color="off")
    with nut_col2:
        st.metric(label="Total Fat", value=f"{final_fat:.2f}", delta=f"Min: {req_fat}", delta_color="off")
    with nut_col3:
        st.metric(label="Total Fibre", value=f"{final_fib:.2f}", delta=f"Max: {max_fibre}", delta_color="inverse")
    with nut_col4:
        st.metric(label="Total Salt", value=f"{final_salt:.3f}", delta=f"Max: {max_salt}", delta_color="inverse")

else:
    st.error("No optimal solution found with the current constraints. Try relaxing the limits in the sidebar.")
