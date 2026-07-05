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
# Sidebar Navigation
# ----------------------------------------------------
with st.sidebar:
    st.title("🪶 Feather")
    st.markdown("---")
    st.button("⬛ Dashboard", use_container_width=True, type="primary")
    st.button("👥 Team", use_container_width=True)
    st.button("📁 Folders", use_container_width=True)
    st.button("📊 Reports", use_container_width=True)
    st.button("⚙️ Settings", use_container_width=True)

# App Title
st.title("Optimization Dashboard")

# ----------------------------------------------------
# Data & PuLP Optimization Model (6 Ingredients, 4 Nutrients)
# ----------------------------------------------------
data = {
    "Ingredient": ["Chicken", "Beef", "Mutton", "Rice", "Wheat", "Gel"],
    "Cost": [0.013, 0.008, 0.010, 0.002, 0.005, 0.001],
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

# Define Theme Colors
teal_palette = ['#1a936f', '#114b5f', '#45c4a0', '#88d49e', '#0a2e36', '#c6f7d0']

# ----------------------------------------------------
# 4-Quadrant UI Dashboard Output
# ----------------------------------------------------

# TOP ROW
col1, col2 = st.columns(2, gap="medium")

# Quadrant 1: Optimised Cost (Top Left)
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
        fig1.update_layout(height=250, margin=dict(t=30, b=10, l=10, r=10))
        st.plotly_chart(fig1, use_container_width=True)

# Quadrant 2: Cost Breakdown (Top Right)
with col2:
    with st.container(border=True):
        st.subheader("Cost Breakdown by Ingredient")
        
        fig2 = px.bar(df_res, 
                      x="Cost_Contribution", 
                      y="Ingredient", 
                      orientation='h',
                      color="Ingredient",
                      color_discrete_sequence=teal_palette)
        
        fig2.update_traces(texttemplate='<b>%{x:.3f}</b>', textposition='inside')
        
        fig2.update_layout(
            showlegend=False, 
            height=250, 
            margin=dict(t=10, b=10, l=10, r=10),
            xaxis_title="Cost (£)", 
            yaxis_title=None,
            yaxis={'categoryorder':'total ascending'} 
        )
        st.plotly_chart(fig2, use_container_width=True)

# BOTTOM ROW
col3, col4 = st.columns(2, gap="medium")

# Quadrant 3: Optimised Ingredient Mix (Bottom Left)
with col3:
    with st.container(border=True):
        st.subheader("Optimised Ingredient Mix")
        
        fig3 = px.pie(df_res[df_res["Percentage"] > 0], values="Percentage", names="Ingredient", 
                      color_discrete_sequence=teal_palette)
        
        # Changed to % format and explicitly enlarged the font size
        fig3.update_traces(textposition='inside', texttemplate='<b>%{label}</b><br>%{value:.1f}%', textfont_size=18)
        fig3.update_layout(showlegend=False, height=280, margin=dict(t=10, b=10, l=10, r=10))
        st.plotly_chart(fig3, use_container_width=True)

# Quadrant 4: Nutrient grams per 100g tin (Bottom Right)
with col4:
    with st.container(border=True):
        st.subheader("Nutrient grams per 100g tin")
        
        nutrients_data = {
            'Nutrient': ['Protein', 'Fat', 'Fibre', 'Salt'],
            'Target Requirement': [min_protein, min_fat, max_fibre, max_salt],
            'Actual Achieved': [actual_protein, actual_fat, actual_fibre, actual_salt]
        }
        df_nut = pd.DataFrame(nutrients_data)
        
        df_nut = df_nut.sort_values(by='Actual Achieved', ascending=True)

        fig4 = go.Figure(data=[
            go.Bar(name='Target Requirement', 
                   y=df_nut['Nutrient'], 
                   x=df_nut['Target Requirement'], 
                   orientation='h', 
                   marker_color='#c6f7d0', 
                   text=[f'<b>{val:.1f}</b>' for val in df_nut['Target Requirement']], 
                   textposition='auto'),
            go.Bar(name='Actual Achieved', 
                   y=df_nut['Nutrient'], 
                   x=df_nut['Actual Achieved'], 
                   orientation='h', 
                   marker_color='#114b5f',
                   text=[f'<b>{val:.1f}</b>' for val in df_nut['Actual Achieved']], 
                   textposition='auto')
        ])
        
        fig4.update_layout(barmode='group', height=280, margin=dict(t=10, b=10, l=10, r=10),
                           xaxis_title="Grams (g)",
                           legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        st.plotly_chart(fig4, use_container_width=True)
