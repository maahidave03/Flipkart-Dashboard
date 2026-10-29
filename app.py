import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="Flipkart Sales Analytics",
    page_icon="🛍️",
    layout="wide"
)

BLUE = "#2874F0"
YELLOW = "#FFD84D"
NAVY = "#123C6A"

st.markdown("""
<style>
.stApp {background:#EEF3FA; color:#17365D;}
.block-container {padding:1rem; max-width:1800px;}
.topbar {
 background:linear-gradient(100deg,#1556B8,#2874F0);
 color:white; padding:18px 22px; border-radius:12px;
 margin-bottom:14px;
}
.brand {color:#FFD84D;font-size:25px;font-weight:800;
 font-style:italic;}
.heading {font-size:23px;font-weight:750;margin-left:20px;}
.kpi {
 background:white;border:1px solid #DCE5F2;
 border-left:4px solid #2874F0;border-radius:11px;
 padding:13px;min-height:100px;
}
.kpi-label {font-size:11px;color:#647A99;}
.kpi-value {font-size:25px;font-weight:800;color:#123C6A;}
.kpi-note {font-size:10px;color:#647A99;}
.panel-title {font-size:15px;font-weight:750;color:#17365D;}
div[data-testid="stVerticalBlockBorderWrapper"] {
 background:white;border-radius:12px;
 border-color:#DCE5F2;
}
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_data(file):
    data = pd.read_csv(file)
    data.columns = [c.strip().lower() for c in data.columns]
    return data


st.markdown("""
<div class="topbar">
 <span class="brand">Flipkart</span>
 <span class="heading">Sales Analytics</span>
 <span style="float:right;background:#FFD84D;color:#123C6A;
 padding:6px;border-radius:5px;font-size:11px">
 SAMPLE DATA · 50K ROWS
 </span>
</div>
""", unsafe_allow_html=True)

uploaded = st.file_uploader("Upload your CSV", type="csv")

if uploaded:
    df = load_data(uploaded)
else:
    try:
        df = load_data("flipkart_synthetic_50000_rows.csv")
    except FileNotFoundError:
        st.info("Upload your Flipkart CSV to start.")
        st.stop()

# Detect columns in the provided sample dataset
def find_col(*names):
    return next((n for n in names if n in df.columns), None)

date_col = find_col("order_date", "date")
cat_col = find_col("category", "product_category")
brand_col = find_col("brand")
product_col = find_col("product_name", "product", "title")
order_col = find_col("order_id", "orderid")
price_col = find_col(
    "selling_price_inr", "selling_price",
    "product_price_inr", "price"
)
qty_col = find_col("quantity", "qty")
rating_col = find_col("rating", "product_rating")
discount_col = find_col("discount_percent", "discount")
status_col = find_col("order_status", "status")
revenue_col = find_col(
    "delivered_revenue_inr",
    "delivered_revenue",
    "revenue",
    "sales"
)

# Prepare numeric and date columns
for c in [price_col, qty_col, rating_col, discount_col, revenue_col]:
    if c:
        df[c] = pd.to_numeric(df[c], errors="coerce")

if date_col:
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")

if revenue_col:
    df["_revenue"] = df[revenue_col].fillna(0)
elif price_col and qty_col:
    df["_revenue"] = (
        df[price_col].fillna(0) * df[qty_col].fillna(0)
    )
else:
    df["_revenue"] = 0

# Filters
with st.container(border=True):
    f1, f2, f3 = st.columns(3)

    with f1:
        categories = (
            sorted(df[cat_col].dropna().unique())
            if cat_col else []
        )
        selected_cat = st.multiselect(
            "Category", categories
        )

    with f2:
        brands = (
            sorted(df[brand_col].dropna().unique())
            if brand_col else []
        )
        selected_brand = st.multiselect("Brand", brands)

    with f3:
        if price_col:
            lo = float(df[price_col].min())
            hi = float(df[price_col].max())
            price_range = st.slider(
                "Price range (₹)", lo, hi, (lo, hi)
            )
        else:
            price_range = None

data = df.copy()

if selected_cat and cat_col:
    data = data[data[cat_col].isin(selected_cat)]

if selected_brand and brand_col:
    data = data[data[brand_col].isin(selected_brand)]

if price_col and price_range:
    data = data[
        data[price_col].between(*price_range)
    ]

if data.empty:
    st.warning("No records match your filters.")
    st.stop()

# KPI cards
revenue = data["_revenue"].sum()
orders = (
    data[order_col].nunique()
    if order_col else len(data)
)
units = data[qty_col].sum() if qty_col else len(data)
avg_price = data[price_col].mean() if price_col else 0
avg_rating = data[rating_col].mean() if rating_col else 0

def money(x):
    if x >= 1e7:
        return f"₹{x/1e7:.2f} Cr"
    if x >= 1e5:
        return f"₹{x/1e5:.2f} L"
    return f"₹{x:,.2f}"

cards = [
    ("TOTAL REVENUE", money(revenue), "Revenue metric"),
    ("TOTAL ORDERS", f"{orders:,.0f}", "Distinct orders"),
    ("PRODUCTS SOLD", f"{units:,.0f}", "Units sold"),
    ("AVERAGE PRICE", money(avg_price), "Mean product price"),
    ("AVERAGE RATING", f"{avg_rating:.2f} / 5", "Mean rating"),
]

cols = st.columns(5)

for col, (label, value, note) in zip(cols, cards):
    with col:
        st.markdown(f"""
        <div class="kpi">
          <div class="kpi-label">{label}</div>
          <div class="kpi-value">{value}</div>
          <div class="kpi-note">{note}</div>
        </div>
        """, unsafe_allow_html=True)

st.write("")

def show_chart(title, fig):
    with st.container(border=True):
        st.markdown(
            f'<div class="panel-title">{title}</div>',
            unsafe_allow_html=True
        )
        fig.update_layout(
            height=260,
            margin=dict(l=10, r=10, t=20, b=10),
            paper_bgcolor="white",
            plot_bgcolor="white",
            font=dict(color=NAVY, size=10),
            showlegend=False
        )
        fig.update_xaxes(showgrid=True, gridcolor="#E7EDF6")
        fig.update_yaxes(showgrid=True, gridcolor="#E7EDF6")
        st.plotly_chart(fig, use_container_width=True)

# Charts: three columns
c1, c2, c3 = st.columns([1.1, 1, 1.15])

with c1:
    if date_col:
        trend = data.dropna(subset=[date_col]).copy()
        trend["Month"] = trend[date_col].dt.to_period("M").astype(str)
        trend = trend.groupby("Month")["_revenue"].sum().reset_index()
        fig = px.line(
            trend, x="Month", y="_revenue",
            markers=True, color_discrete_sequence=[BLUE]
        )
        fig.update_yaxes(title="Revenue (₹)", tickformat="~s")
        show_chart("Sales trend", fig)

with c2:
    if cat_col:
        category = data.groupby(cat_col)["_revenue"].sum()
        category = category.nlargest(8).reset_index()
        fig = px.pie(
            category, names=cat_col, values="_revenue",
            hole=0.58,
            color_discrete_sequence=[
                BLUE, YELLOW, "#6BA5F7", "#4B729B",
                "#8BCAD8", "#F0B85B", "#B8CDF4", "#7C8FB0"
            ]
        )
        fig.update_traces(textinfo="percent")
        show_chart("Category contribution", fig)

with c3:
    if product_col:
        top = (
            data.groupby(product_col)["_revenue"]
            .sum().nlargest(10).sort_values()
            .reset_index()
        )
        fig = px.bar(
            top, x="_revenue", y=product_col,
            orientation="h",
            color_discrete_sequence=[BLUE]
        )
        fig.update_yaxes(title=None)
        fig.update_xaxes(title="Revenue (₹)", tickformat="~s")
        show_chart("Top 10 products", fig)

c1, c2, c3 = st.columns([1.1, 1, 1.15])

with c1:
    if cat_col:
        comp = (
            data.groupby(cat_col)["_revenue"]
            .sum().nlargest(10).sort_values()
            .reset_index()
        )
        fig = px.bar(
            comp, x="_revenue", y=cat_col,
            orientation="h", color_discrete_sequence=[BLUE]
        )
        fig.update_xaxes(title="Revenue (₹)", tickformat="~s")
        fig.update_yaxes(title=None)
        show_chart("Category comparison", fig)

with c2:
    if rating_col:
        ratings = data[rating_col].dropna()
        fig = px.histogram(
            x=ratings, nbins=10,
            color_discrete_sequence=["#9CC4F7"]
        )
        fig.update_xaxes(title="Product rating")
        fig.update_yaxes(title="Records")
        show_chart("Product ratings", fig)

with c3:
    if discount_col:
        discounts = data[discount_col].dropna()
        bins = [0, 10, 20, 30, 40, 50, 101]
        labels = ["0–10%", "10–20%", "20–30%",
                  "30–40%", "40–50%", "50%+"]
        bands = pd.cut(
            discounts.clip(0, 100), bins=bins,
            labels=labels, include_lowest=True
        ).value_counts(sort=False).reset_index()
        bands.columns = ["Discount band", "Records"]
        fig = px.bar(
            bands, x="Discount band", y="Records",
            color_discrete_sequence=[YELLOW]
        )
        show_chart("Discount distribution", fig)

# Table and insights
left, right = st.columns([1.4, 1])

with left:
    with st.container(border=True):
        st.markdown("### Top-performing products")
        if product_col:
            table = (
                data.groupby(product_col)
                .agg(
                    Revenue=("_revenue", "sum"),
                    Units=(qty_col, "sum") if qty_col else
                          ("_revenue", "size")
                )
                .nlargest(10, "Revenue")
                .reset_index()
            )
            table.insert(0, "#", range(1, len(table) + 1))
            table["Revenue"] = table["Revenue"].map(money)
            st.dataframe(
                table, hide_index=True,
                use_container_width=True
            )

with right:
    with st.container(border=True):
        st.markdown("### Key insights")
        if cat_col:
            cat_sales = data.groupby(cat_col)["_revenue"].sum()
            if len(cat_sales) and revenue:
                best = cat_sales.idxmax()
                st.write(
                    f"• **{best}** is the leading category "
                    f"({cat_sales.max()/revenue:.1%} of revenue)."
                )

        if rating_col:
            st.write(
                f"• Average product rating: "
                f"**{avg_rating:.2f}/5**."
            )

        if discount_col:
            st.write(
                f"• Average discount: "
                f"**{data[discount_col].mean():.2f}%**."
            )

        if status_col:
            delivered = (
                data[status_col].astype(str).str.lower()
                .eq("delivered").mean()
            )
            st.write(
                f"• **{delivered:.1%}** of records "
                "are marked delivered."
            )

st.caption(
    "Metrics reflect the selected records. Verify the dataset's "
    "column definitions before interpreting revenue or orders."
)
