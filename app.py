import streamlit as st
import pulp
import pandas as pd
import plotly.graph_objects as go

# Set up page configurations
st.set_page_config(page_title="Whiskas Optimizer", layout="wide")

# Custom CSS to inject to style our blocks as distinct "Cards"
st.markdown("""
    <style>
    /* Card Container Layout */
    div[data-testid="stVerticalBlock"] > div:has(div.card-wrapper) {
        background-color: #ffffff;
        padding: 22px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        border: 1px solid #e6e9ef;
        margin-bottom: 20px;
    }
    /* Hero Metric Styling */
    div[data-testid="stMetricValue"] {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f77b4;
    }
    </style>
    """, unsafe_allow_html=True)

# App Title matching your sketch
st.title("Whiskas Optimization Dashboard")
st.markdown("---")

# ----------------------------------------------------
# Editable Data Input Tables (Replacing Sliders)
# ----------------------------------------------------
st.subheader("📋 Input parameters & Specifications")

col_input1, col_input2 = st.columns(2, gap="large")

with col_input1:
    st.markdown("**Ingredient Matrix (Edit Costs & Nutritional Values)**")
    # Default Whiskas problem numbers mapped to an editable dataframe
    default_ingredients = {
        "Ingredient": ["Chicken", "Beef"],
        "Cost (£/g)": [0.013, 0.008],
        "Protein (%)": [10.0, 20.0],
        "Fat (%)": [8.0, 10.0]
    }
    df_ingredients = pd.DataFrame(default_ingredients)
    # st.data_editor lets users directly click cells and type new values
    edited_ingredients = st.data_editor(df_ingredients, num_rows="fixed", use_container_width=True, hide_index=True)

with col_input2:
    st.markdown("**Minimum Requirements (Edit Constraints)**")
    default_constraints = {
        "Nutrient Target": ["Minimum Protein Required", "Minimum Fat Required"],
        "Target Percentage (%)": [8.0, 6.0]
    }
    df_constraints = pd.DataFrame(default_constraints)
    edited_constraints = st.data_editor(df_constraints, num_rows="fixed", use_container_width=True, hide_index=True)

# ----------------------------------------------------
# Calculation Trigger Button
# ----------------------------------------------------
st.markdown("---")
calculate_clicked = st.button("🚀 Calculate Optimization", type="primary", use_container_width=True)

# We use streamlit's session state to keep results on screen after clicking calculate
if "optimized" not in st.session_state:
    st.session_state.optimized = False

if calculate_clicked:
    # 1. Parse data out of the editable dataframes
    cost_chicken = edited_ingredients.iloc[0]["Cost (£/g)"]
    prot_chicken = edited_ingredients.iloc[0]["Protein (%)"] / 100.0
    fat_chicken = edited_ingredients.iloc[0]["Fat (%)"] / 100.0

    cost_beef = edited_ingredients.iloc[1]["Cost (£/g)"]
    prot_beef = edited_ingredients.iloc[1]["Protein (%)"] / 100.0
    fat_beef = edited_ingredients.iloc[1]["Fat (%)"] / 100.0

    min_protein = edited_constraints.iloc[0]["Target Percentage (%)"]
    min_fat = edited_constraints.iloc[1]["Target Percentage (%)"]

    # 2. Setup and run the PuLP optimization problem
    prob = pulp.LpProblem("The_Whiskas_Problem", pulp.LpMinimize)
    x1 = pulp.LpVariable("ChickenPercent", lowBound=0, upBound=100)
    x2 = pulp.LpVariable("BeefPercent", lowBound=0, upBound=100)

    # Objective function
    prob += cost_chicken * x1 + cost_beef * x2, "Total_Cost_per_Can"
    
    # Constraints
    prob += x1 + x2 == 100, "Percentage_Sum_Constraint"
    prob += prot_chicken * x1 + prot_beef * x2 >= min_protein, "Protein_Constraint"
    prob += fat_chicken * x1 + fat_beef * x2 >= min_fat, "Fat_Constraint"

    status = prob.solve(pulp.PULP_CBC_CMD(msg=False))

    # Save results to session state
    if pulp.LpStatus[status] == "Optimal":
        st.session_state.opt_chicken = round(x1.varValue, 1)
        st.session_state.opt_beef = round(x2.varValue, 1)
        st.session_state.total_cost = round(pulp.value(prob.objective), 2)
        st.session_state.achieved_protein = (prot_chicken * 100 * st.session_state.opt_chicken / 100) + (prot_beef * 100 * st.session_state.opt_beef / 100)
        st.session_state.achieved_fat = (fat_chicken * 100 * st.session_state.opt_chicken / 100) + (fat_beef * 100 * st.session_state.opt_beef / 100)
        st.session_state.min_p = min_protein
        st.session_state.min_f = min_fat
        st.session_state.optimized = True
    else:
        st.session_state.optimized = "Failed"

# ----------------------------------------------------
# UI Dashboard Output Layout (Cards Architecture)
# ----------------------------------------------------
if st.session_state.optimized == True:
    st.markdown("### 📊 Optimization Results")
    col_mix, col_details = st.columns([2, 3], gap="large")

    # LEFT COLUMN CARD: The "Mix" Donut Chart Card from sketch
    with col_mix:
        with st.container():
            st.markdown('<div class="card-wrapper"></div>', unsafe_allow_html=True)
            st.subheader("Mix")
            
            labels = ['Chicken', 'Beef']
            values = [st.session_state.opt_chicken, st.session_state.opt_beef]
            
            fig = go.Figure(data=[go.Pie(
                labels=labels, 
                values=values, 
                hole=0.5, # Custom Donut Hole from sketch
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

    # RIGHT COLUMN CARDS: Vertically stacked cards matching your sketch template
    with col_details:
        
        # CARD 1: Unit Cost Card
        with st.container():
            st.markdown('<div class="card-wrapper"></div>', unsafe_allow_html=True)
            st.metric(
                label="Unit Cost (per Can)", 
                value=f"£{st.session_state.total_cost:,.2f}"
            )
        
        # CARD 2: Ingredients Allocation Table
        with st.container():
            st.markdown('<div class="card-wrapper"></div>', unsafe_allow_html=True)
            st.subheader("Ingredients")
            ingredients_data = {
                "Ingredient": ["Chicken", "Beef"],
                "Optimal Ratio": [f"{st.session_state.opt_chicken}%", f"{st.session_state.opt_beef}%"],
                "Mass (per 100g can)": [f"{st.session_state.opt_chicken}g", f"{st.session_state.opt_beef}g"]
            }
            st.table(pd.DataFrame(ingredients_data))

        # CARD 3: Nutrients Target Verification
        with st.container():
            st.markdown('<div class="card-wrapper"></div>', unsafe_allow_html=True)
            st.subheader("Nutrients")
            st.success(f"✔️ Protein Content: {st.session_state.achieved_protein:.1f}% (Required: ≥ {st.session_state.min_p}%)")
            st.success(f"✔️ Crude Fat Content: {st.session_state.achieved_fat:.1f}% (Required: ≥ {st.session_state.min_f}%)")

elif st.session_state.optimized == "Failed":
    st.error("❌ The linear constraints are impossible to fulfill with current parameters. Please adjust your input matrices and click Calculate again.")
else:
    st.info("💡 Adjust the metrics in the tables above if desired, then click 'Calculate Optimization' to view the optimal blend results.")
