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
    
    /* Styling the metric cards (The Grid and Chart Panel) */
    [data-testid="stMetric"], [data-testid="stAltairChart"] {
        background-color: #262628;
        border: 1px solid #3e3e42;
        border-radius: 12px;
        padding: 15px 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        height: 100%; /* Ensures all cards stretch equally */
    }
    
    /* Metric Labels */
    [data-testid="stMetricLabel"] {
        color: #e5f396 !important;
        font-size: 0.95rem !important; /* Scaled down slightly to fit 4 cards perfectly */
        font-weight: 600;
        white-space: nowrap; /* Prevents awkward text wrapping on smaller screens */
    }
    
    /* Metric Values */
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
        padding: 0; 
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
    
    # Main Dashboard Area (1x2 column layout)
    mix_chart_col, mix_metrics_col = st.columns([1, 1.5])
    
    # Left Column: Pie Chart
    with mix_chart_col:
        st.subheader("Mix Composition")
        
        # Prepare Data for Chart
        df_mix = pd.DataFrame({
            'Ingredient': [ing.replace("_", " ") for ing in Ingredients],
            'Grams': [max(0.0, x[ing].varValue) for ing in Ingredients]
        })
        
        # Create combined labels (e.g., "Beef 60.0%")
        df_mix['Percent_Label'] = df_mix['Grams'].map('{:.1f}%'.format)
        df_mix['Chart_Label'] = df_mix['Ingredient'] + ' ' + df_mix['Percent_Label']
        df_mix_chart = df_mix[df_mix['Grams'] > 0]
        
        neon_colors = ["#A678E2", "#FFFC99", "#8EE6D5", "#98E68D", "#89E6E3", "#94E2E0"] 
        custom_scale = alt.Scale(domain=df_mix['Ingredient'].tolist(), range=neon_colors[:len(Ingredients)])

        # Base chart with legend removed (legend=None)
        base = alt.Chart(df_mix_chart).encode(
            theta=alt.Theta("Grams:Q", stack=True),
            color=alt.Color("Ingredient:N", scale=custom_scale, legend=None),
            tooltip=["Ingredient:N", "Percent_Label:N", alt.Tooltip("Grams:Q", format=".1f")]
        )
        
        # Create solid Pie Chart (innerRadius=0) and define a fixed outer radius
        pie = base.mark_arc(innerRadius=0, outerRadius=110, stroke="#3e3e42", strokeWidth=1)
        
        # Place the combined text labels outside the pie slices
        text = base.mark_text(radius=145, fill="#e5f396", fontSize=14, fontWeight="bold").encode(
            text=alt.Text("Chart_Label:N")
        )
        
        # Add padding to prevent the outside labels from being clipped off the canvas
        chart_final = alt.layer(pie, text).properties(
            height=350,
            padding=40,
            background="#262628" 
        ).configure_view(strokeWidth=0)
        
        st.altair_chart(chart_final, use_container_width=True)

    # Right Column: Unified Metrics Grid
    with mix_metrics_col:
        
        # --- Subsection 1: Ingredient Weights ---
        st.subheader("Ingredient Weights")
        
        # Create a 3-column grid for ingredients (2 rows)
        ing_cols1 = st.columns(3)
        ing_cols2 = st.columns(3)
        
        for idx, ing in enumerate(Ingredients):
            val = x[ing].varValue
            display_val = max(0.0, val)
            # Route first 3 ingredients to the top row, next 3 to the bottom row
            target_col = ing_cols1[idx] if idx < 3 else ing_cols2[idx - 3]
            with target_col:
                st.metric(label=ing.replace("_", " "), value=f"{display_val:.1f}g")
                
        st.markdown("<br>", unsafe_allow_html=True)

        # --- Subsection 2: Nutritional Breakdown ---
        st.subheader("Nutritional Breakdown")
        
        # Create a 4-column grid for nutritional data so they all fit on ONE line
        nut_cols = st.columns(4)
        
        final_prot = sum([protein[i] * max(0.0, x[i].varValue) for i in Ingredients])
        final_fat = sum([fat[i] * max(0.0, x[i].varValue) for i in Ingredients])
        final_fib = sum([fibre[i] * max(0.0, x[i].varValue) for i in Ingredients])
        final_salt = sum([salt[i] * max(0.0, x[i].varValue) for i in Ingredients])
        
        # Shortened titles (e.g. "Total Protein" -> "Protein") to guarantee single-line fit
        with nut_cols[0]:
            st.metric(label="Protein (g)", value=f"{final_prot:.2f}", delta=f"Min: {req_protein}", delta_color="off")
        with nut_cols[1]:
            st.metric(label="Fat (g)", value=f"{final_fat:.2f}", delta=f"Min: {req_fat}", delta_color="off")
        with nut_cols[2]:
            st.metric(label="Fibre (g)", value=f"{final_fib:.2f}", delta=f"Max: {max_fibre}", delta_color="inverse")
        with nut_cols[3]:
            st.metric(label="Salt (g)", value=f"{final_salt:.3f}", delta=f"Max: {max_salt}", delta_color="inverse")

else:
    st.error("No optimal solution found with the current constraints. Try relaxing the limits in the sidebar.")
