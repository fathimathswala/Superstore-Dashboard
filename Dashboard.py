import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import numpy as np

st.set_page_config(page_title="Superstore Dashboard",page_icon="📊",layout="wide",initial_sidebar_state="expanded")

@st.cache_data(ttl=600)
def load_data():
    df=pd.read_csv(r"C:\Users\Swala Nasar\OneDrive\Super Store\output\superstore_clean.csv",parse_dates=["Order Date","Ship Date"])
    return df


df=load_data()

st.title("Superstore Sales Dashboard")

with st.sidebar:
    st.header("Filters")
    regions = st.multiselect("Region",options=df["Region"].unique(),default=df["Region"].unique())
    years= st.multiselect("Order Year", options=df["Order Year"].unique(),default=df["Order Year"].unique())

    with st.form("filters"):
        start=st.date_input("Start date", value=df["Order Date"].min().date())
        end=st.date_input("End date", value=df["Order Date"].max().date())
        submitted=st.form_submit_button("Apply") 
    if st.sidebar.button("Refresh data"):
        st.cache_data.clear()
        st.rerurn()

filtered = df[df["Region"].isin(regions) & df["Order Year"].isin(years)]    
if submitted:
    filtered= filtered(filtered["Order Date"].dt.date.between(start,end))
st.write(f"showing {len(filtered):,} rows")

disc_arr = filtered['Discount'].values
sales_arr = filtered['Sales'].values
high_disc_pct= np.percentile(disc_arr, 75) if len(disc_arr)else 0
high_dics_n = int(np.sum(disc_arr > high_disc_pct)) if len(disc_arr)else 0
z_score = (sales_arr - np.mean(sales_arr)) / np.std(sales_arr) if len(sales_arr) else 0
outlier_n = int(np.sum(np.abs(z_score)>3)) if len(z_score) else 0
mean_margin = filtered["Profit Margin"].mean() if len(filtered) else 0

c1,c2,c3=st.columns(3)
c1.metric("Total Sales",f"${filtered.Sales.sum():,.0f}")
c2.metric("Total Profit",f"${filtered.Profit.sum():,.0f}")
c3.metric("Average Discount",f"{filtered.Discount.mean()*100:.1f}%")

tab1,tab2,tab3,tab4=st.tabs(["Overview","By category","Region","Quality Alerts"])
with tab1:
   st.write("Filtered data-First 20 rows")
   st.dataframe(filtered, use_container_width=True, hide_index=True)

   st.subheader("Monthly sales by year")
   monthly_yr=(filtered.groupby([filtered["Order Date"].dt.to_period("M").astype(str),"Order Year"])["Sales"].sum().reset_index().rename(columns={"Order Date":"Month"}))
   fig=px.line(monthly_yr,x="Month",y="Sales",color="Order Year",title="plotly grouped line:monthly sales by year")
   st.plotly_chart(fig,use_container_width=True)

with tab2:
     filtered=df.copy()
     top10=filtered.groupby("sub_category")['Sales'].sum().nlargest(10).sort_values()
     fig,ax=plt.subplots(figsize=(7,4))
     bars=ax.barh(top10.index,top10.values,color="#80F63B")
     ax.bar_label(bars,fmt="$%.0f",padding=4,fontsize=8)
     ax.set_title("Top 10 Sub-Categories by Sales")
     ax.set_xlabel(" Total Sales")
     plt.tight_layout()
     st.pyplot(fig)
     plt.close(fig)
     st.subheader("Sub-category breakdown")
     summary=filtered.groupby("sub_category").agg(Sales=("Sales","sum"),profit=("Profit","sum")).sort_values("Sales",ascending=False)
     st.dataframe(summary.style.format("${:,.0f}"),use_container_width=True)
     st.header("Sales vs Profit")
     fig=px.scatter(df,x="Sales",y="Profit",color="Category",size="Quantity",hover_data=["sub_category"],title="Plotly scatter Sales vs Profit")
     st.plotly_chart(fig,use_container_width=True)
with tab3:
     st.subheader("Profit Share by Region")
     reg=filtered.groupby("Region")["Profit"].sum().reset_index()
     fig=px.pie(reg,names="Region",values="Profit", hole=0.4,title="Profit share by Region")
     st.plotly_chart(fig,use_container_width=True)
with tab4:
     st.subheader("Quality Alerts")

     if mean_margin < 10:
         st.error(f"Low margin :{mean_margin:.1f}% - investigate discounts and product wix")
     elif mean_margin < 20:
         st.warning(f"Moderate margin :{mean_margin:.1f}% - room to improve")
     else:
         st.success(f"Healthy Margin: {mean_margin:.1f}%- pricing strategy is working")
     st.info(f"{high_dics_n} ordrs have discount above the 75th percentile({high_disc_pct * 100:.0f}%).")
       
     if outlier_n > 0:
         st.warning(f"{outlier_n}Sales outliers ditected (|Z-Score| > 3).")
     else:
         st.success("No Sales outliers detected.")
    
     with st.expander("View outlier rows"):
         outlier_mask = np.abs(z_score) > 3 if len(z_score)else 0
         outliers = filtered[outlier_mask] if len(outlier_mask)else 0
         st.dataframe(outliers[["Order ID","Order Date","Sales","Profit","Region"]],use_container_width=True)


st.markdown("---")
min_year=filtered["Order Year"].min()
max_year=filtered["Order Year"].max()
st.caption(f"Showing {len(filtered):,}rows-{min_year}-{max_year}.Built by Fathimath Swala")