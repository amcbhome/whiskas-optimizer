import streamlit as st
import pulp
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Set up page configurations
st.set_page_config(page_title="Whiskas Optimizer", layout="wide", initial_sidebar_state="expanded")

# Custom CSS for the overall background
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    </style>
    """, unsafe_allow_html=True)

# ----------------------------------------------------
# Sidebar: What-If Controls
# ----------------------------------------------------
with st.sidebar:
    st.subheader("What-If Analysis")
    
    # Default baseline costs
    default_costs = pd.DataFrame({
        "Ingredient": ["Chicken", "Beef", "Mutton", "Rice", "Wheat", "Gel"],
        "Cost (£/g)": [0.013, 0.008, 0.010, 0.002, 0.005, 0.001]
    })
    
    # The st.form prevents the app from rerunning until the button is clicked
    with st.form("what_if_form"):
        st.markdown("Adjust ingredient market costs:")
        edited_costs = st.data_editor(default_costs, hide_index=True, use_container_width=True)
        calculate_btn = st.form_submit_button("Calculate", type="primary", use_container_width=True)

# App Title
st.title("Optimization Dashboard")

# ----------------------------------------------------
# Data & PuLP Optimization Model
# ----------------------------------------------------
data = {
    "Ingredient": ["Chicken", "Beef", "Mutton", "Rice", "Wheat", "Gel"],
    # Dynamically pull the costs from the sidebar form
    "Cost": edited_costs["Cost (£/g)"].tolist(), 
    "Protein": [0.100, 0.200, 0.150, 0.000, 0.040, 0.000],
    "Fat": [0.080, 0.100, 0.110, 0.010, 0.010, 0.000],
    "Fibre": [0.001, 0.005, 0.003, 0.010, 0.015, 0.000],
    "Salt": [0.002, 0.005, 0.007, 0.002, 0.008, 0.000],
    "Risk_Score": [0.05, 0.08, 0.06, 0.02, 0.03, 0.01] 
}
df = pd.DataFrame(data)

# Targets
min_protein = 8.0
min_fat = 6.0
max_fibre = 2.0
max_salt = 0.4

# Initialize Model
prob = pulp.LpProblem("Whiskas_6_Ingredient", pulp.LpMinimize)
ingredient_vars = pulp.LpVariable.dicts("Ing", df["Ingredient"], lowBound=0, upBound=100)

# Objective: Minimize Cost
prob += pulp.lpSum([df.loc[i, "Cost"] * ingredient_vars[df.loc[i, "Ingredient"]] for i in df.index]), "Total_Cost"

# Constraints
prob += pulp.lpSum([ingredient_vars[ing] for ing in df["Ingredient"]]) == 100, "PercentagesSum"
prob += pulp.lpSum([df.loc[i, "Protein"] * ingredient_vars[df.loc[i, "Ingredient"]] for i in df.index]) >= min_protein, "MinProtein"
prob += pulp.lpSum([df.loc[i, "Fat"] * ingredient_vars[df.loc[i, "Ingredient"]] for i in df.index]) >= min_fat, "MinFat"
prob += pulp.lpSum([df.loc[i, "Fibre"] * ingredient_vars[df.loc[i, "Ingredient"]] for i in df.index]) <= max_fibre, "MaxFibre"
prob += pulp.lpSum([df.loc[i, "Salt"] * ingredient_vars[df.loc[i, "Ingredient"]] for i in df.index]) <= max_salt, "MaxSalt"

# Solve
prob.solve(pulp.PULP_CBC_CMD(msg=False))

# Extract Results
results = []
total_risk = 0
actual_protein = 0
actual_fat = 0
actual_fibre = 0
actual_salt = 0

for i in df.index:
    ing = df.loc[i, "Ingredient"]
    val = ingredient_vars[ing].varValue
    cost_contrib = val * df.loc[i, "Cost"]
    risk_contrib = val * df.loc[i, "Risk_Score"]
    
    actual_protein += val * df.loc[i, "Protein"]
    actual_fat += val * df.loc[i, "Fat"]
    actual_fibre += val * df.loc[i, "Fibre"]
    actual_salt += val * df.loc[i, "Salt"]
    total_risk += risk_contrib
    
    results.append({
        "Ingredient": ing, 
        "Percentage": val, 
        "Cost_Contribution": cost_contrib, 
        "Risk_Contribution": risk_contrib
    })

df_res = pd.DataFrame(results)
optimized_cost = pulp.value(prob.objective)

# ----------------------------------------------------
# Explicit Color Mapping
# ----------------------------------------------------
ingredient_colors = {
    "Beef": "#c6f7d0",     
    "Chicken": "#114b5f",  
    "Gel": "#1a936f",      
    "Mutton": "#45c4a0",   
    "Rice": "#88d49e",     
    "Wheat": "#0a2e36"     
}

# ----------------------------------------------------
# 4-Quadrant UI Dashboard Output
# ----------------------------------------------------
UNIVERSAL_HEIGHT = 320 

# TOP ROW
col1, col2 = st.columns(2, gap="medium")

# Quadrant 1: Optimised Cost
with col1:
    with st.container(border=True):
        st.subheader("Optimised Cost")
        
        fig1 = go.Figure(go.Indicator(
            mode = "number+delta",
            value = optimized_cost,
            number = {'prefix': "£", 'valueformat': ".2f", 'font': {'weight': 'bold'}},
            delta = {'position': "bottom", 'reference': 1.50, 'relative': False, 'valueformat': ".2f"},
            title = {"text": "Cost per 100g Can<br><span style='font-size:0.8em;color:gray'>vs Benchmark (£1.50)</span>"}
        ))
        fig1.update_layout(height=UNIVERSAL_HEIGHT, margin=dict(t=30, b=10, l=10, r=10))
        st.plotly_chart(fig1, use_container_width=True)

# Quadrant 2: Cost Breakdown Table
with col2:
    with st.container(border=True):
        st.subheader("Cost breakdown of 6 ingredients")
        
        table_rows = []
        for index, row in df_res.iterrows():
            ing = row['Ingredient']
            unit_cost = df.loc[df['Ingredient'] == ing, 'Cost'].values[0]
            
            table_rows.append({
                "Ingredient": ing,
                "g": row['Percentage'],
                "Cost": f"£{unit_cost:.3f}",
                "Total": f"£{row['Cost_Contribution']:.3f}"
            })
        
        df_table = pd.DataFrame(table_rows)
        
        grand_total_row = pd.DataFrame([{
            "Ingredient": "Grand Total",
            "g": 100.0,
            "Cost": "-",
            "Total": f"£{optimized_cost:.3f}"
        }])
        df_table = pd.concat([df_table, grand_total_row], ignore_index=True)
        
        df_table['g'] = df_table['g'].apply(lambda x: f"{x:.1f}" if isinstance(x, float) else x)
        
        styled_table = df_table.style.set_properties(**{
            'font-size': '15px',
            'font-weight': 'bold',
            'font-family': 'sans-serif'
        })
        
        st.dataframe(styled_table, height=UNIVERSAL_HEIGHT, hide_index=True, use_container_width=True)

# BOTTOM ROW
col3, col4 = st.columns(2, gap="medium")

# Quadrant 3: Optimised Ingredient Mix
with col3:
    with st.container(border=True):
        st.subheader("Optimised Ingredient Mix")
        
        fig3 = px.pie(df_res[df_res["Percentage"] > 0], 
                      values="Percentage", 
                      names="Ingredient", 
                      color="Ingredient",
                      color_discrete_map=ingredient_colors) 
        
        fig3.update_traces(textposition='inside', texttemplate='<b>%{label}</b><br>%{value:.1f}%', textfont_size=18)
        fig3.update_layout(showlegend=False, height=UNIVERSAL_HEIGHT, margin=dict(t=10, b=10, l=10, r=10))
        st.plotly_chart(fig3, use_container_width=True)

# Quadrant 4: Nutrient Requirement Table
with col4:
    with st.container(border=True):
        st.subheader("Nutrient Requirement")
        
        def get_status(actual, target, is_min=True):
            if is_min:
                return "✔️" if round(actual, 4) >= target else "❌"
            else:
                return "✔️" if round(actual, 4) <= target else "❌"

        req_data = {
            "Nutrient": ["Protein", "Fat", "Fibre", "Salt"],
            "Constraint": [
                f">= {min_protein:.1f}g", 
                f">= {min_fat:.1f}g", 
                f"<= {max_fibre:.1f}g", 
                f"<= {max_salt:.1f}g"
            ],
            "Actual (g)": [
                f"{actual_protein:.2f}", 
                f"{actual_fat:.2f}", 
                f"{actual_fibre:.2f}", 
                f"{actual_salt:.2f}"
            ],
            "Status": [
                get_status(actual_protein, min_protein, is_min=True),
                get_status(actual_fat, min_fat, is_min=True),
                get_status(actual_fibre, max_fibre, is_min=False),
                get_status(actual_salt, max_salt, is_min=False)
            ]
        }
        
        df_req = pd.DataFrame(req_data)
        
        styled_req = df_req.style.set_properties(**{
            'font-size': '15px',
            'font-weight': 'bold',
            'font-family': 'sans-serif'
        })
        
        st.dataframe(styled_req, height=UNIVERSAL_HEIGHT, hide_index=True, use_container_width=True)
