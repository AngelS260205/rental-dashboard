import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Rental Property Analysis", layout="wide")

st.title(" Residential Rental Property Analysis")
st.write("Explore monthly rent of houses in 5 Indian cities. "
         "Use the sidebar filters - all KPIs, tables and charts will change.")

# ---------------------------------------------------------
# Load and prepare the data
# ---------------------------------------------------------
@st.cache_data                      # load the file only once, makes the app faster
def load_data():
    df = pd.read_csv("cities_magicbricks_rental_prices.csv")
    # new column: Flat / House / Villa taken from the listing title
    df["property_type"] = df["house_type"].str.extract(r"(Flat|House|Villa)")
    # new column: rent per square foot
    df["rent_per_sqft"] = df["rent"] / df["area"]
    # 5 or more bedrooms are grouped as 5
    df["bhk"] = df["beds"].clip(upper=5)
    return df

data = load_data()

# ---------------------------------------------------------
# Sidebar : filters and navigation
# ---------------------------------------------------------
st.sidebar.title("Filters")

# multiselect widgets
city_list = st.sidebar.multiselect(
    "Select City", sorted(data["city"].unique()), default=sorted(data["city"].unique()))

bhk_list = st.sidebar.multiselect(
    "Select BHK (bedrooms)", [1, 2, 3, 4, 5], default=[1, 2, 3, 4, 5])

furnish_list = st.sidebar.multiselect(
    "Select Furnishing", sorted(data["furnishing"].unique()),
    default=sorted(data["furnishing"].unique()))

type_list = st.sidebar.multiselect(
    "Select Property Type", ["Flat", "House", "Villa"], default=["Flat", "House", "Villa"])

# slider widget
rent_range = st.sidebar.slider(
    "Monthly Rent Range (Rs)", 1000, 1000000, (1000, 1000000), step=1000)

# checkbox widget
remove_outliers = st.sidebar.checkbox(
    "Remove unrealistic records (area < 100 or > 10000 sq.ft)", value=True)

# selectbox widget : which category to compare
compare_by = st.sidebar.selectbox(
    "Compare rent by", ["city", "furnishing", "property_type", "bhk"])

# radio widget : average or median
measure = st.sidebar.radio("Rent measure", ["Average", "Median"])

# ---------------------------------------------------------
# Apply the filters
# ---------------------------------------------------------
df = data[
    (data["city"].isin(city_list)) &
    (data["bhk"].isin(bhk_list)) &
    (data["furnishing"].isin(furnish_list)) &
    (data["property_type"].isin(type_list)) &
    (data["rent"] >= rent_range[0]) &
    (data["rent"] <= rent_range[1])
]

if remove_outliers:
    df = df[(df["area"] >= 100) & (df["area"] <= 10000)]

# stop if nothing is selected
if df.empty:
    st.warning("No records match the selected filters. Please change the filters.")
    st.stop()

# ---------------------------------------------------------
# KPIs (inside columns)
# ---------------------------------------------------------
st.header("Key Performance Indicators")
col1, col2, col3, col4, col5 = st.columns(5)

col1.metric("Total Records", f"{len(df):,}")
col2.metric("Average Rent", f"Rs {df['rent'].mean():,.0f}")
col3.metric("Median Rent", f"Rs {df['rent'].median():,.0f}")
col4.metric("Sum of Rent", f"Rs {df['rent'].sum() / 10000000:,.2f} Cr")
col5.metric("Average Area", f"{df['area'].mean():,.0f} sq.ft")

# ---------------------------------------------------------
# Tabs
# ---------------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs(
    ["Dataset Overview", "Data Analysis", "Visualizations", "Insights"])

# ================= TAB 1 : DATASET OVERVIEW =================
with tab1:
    st.subheader("Dataset Overview")
    st.write("**Domain:** Residential rental real estate")
    st.write("**Source:** MagicBricks rental listings (Mumbai, New Delhi, Bangalore, Pune, Nagpur)")
    st.write("**Target variable:** rent (monthly rent in Rs)")

    c1, c2 = st.columns(2)
    c1.info(f"Records in original file: {len(data):,}")
    c2.success(f"Records after filters: {len(df):,}")

    with st.expander("Show filtered data table"):
        st.dataframe(df[["city", "locality", "property_type", "bhk", "bathrooms",
                         "furnishing", "area", "rent"]])

    with st.expander("Show column details"):
        st.write("- **city, locality** : place of the property")
        st.write("- **property_type** : Flat / House / Villa")
        st.write("- **bhk, bathrooms, balconies** : number of rooms")
        st.write("- **furnishing** : Furnished / Semi-Furnished / Unfurnished")
        st.write("- **area** : size in square feet")
        st.write("- **rent** : monthly rent in Rs")
        st.write("- **rent_per_sqft** : rent divided by area")

    with st.expander("Show statistical summary"):
        st.dataframe(df[["area", "bathrooms", "balconies", "rent"]].describe())

# ================= TAB 2 : DATA ANALYSIS =================
with tab2:
    st.subheader("Category-wise Record Counts (group by)")

    a1, a2 = st.columns(2)
    with a1:
        st.write("**Records by City**")
        st.dataframe(df.groupby("city").size().reset_index(name="Records"))
        st.write("**Records by Furnishing**")
        st.dataframe(df.groupby("furnishing").size().reset_index(name="Records"))
    with a2:
        st.write("**Records by BHK**")
        st.dataframe(df.groupby("bhk").size().reset_index(name="Records"))
        st.write("**Records by Property Type**")
        st.dataframe(df.groupby("property_type").size().reset_index(name="Records"))

    with st.container():
        st.subheader(f"Rent Summary by {compare_by}")
        summary = df.groupby(compare_by)["rent"].agg(["count", "sum", "mean", "median"])
        summary.columns = ["Records", "Sum of Rent", "Average Rent", "Median Rent"]
        st.dataframe(summary.round(0))

    with st.expander("Correlation between numeric columns"):
        st.dataframe(df[["area", "beds", "bathrooms", "balconies", "rent"]].corr().round(2))

# ================= TAB 3 : VISUALIZATIONS =================
with tab3:
    st.subheader("Visualizations")

    # ---------- BAR CHARTS (side by side) ----------
    st.write("### 1. Bar Charts")
    b1, b2 = st.columns(2)

    with b1:
        if measure == "Average":
            bar_data = df.groupby(compare_by)["rent"].mean()
        else:
            bar_data = df.groupby(compare_by)["rent"].median()

        fig, ax = plt.subplots(figsize=(6, 4))
        ax.bar(bar_data.index.astype(str), bar_data.values, color="steelblue", label=f"{measure} rent")
        ax.set_title(f"{measure} Monthly Rent by {compare_by}")
        ax.set_xlabel(compare_by)
        ax.set_ylabel("Rent (Rs)")
        ax.legend()
        st.pyplot(fig)
        st.caption(f"Interpretation: {bar_data.idxmax()} has the highest {measure.lower()} rent "
                   f"(Rs {bar_data.max():,.0f}).")

    with b2:
        count_data = df.groupby(["city", "furnishing"]).size().unstack(fill_value=0)
        fig, ax = plt.subplots(figsize=(6, 4))
        count_data.plot(kind="bar", ax=ax)
        ax.set_title("Number of Listings by City and Furnishing")
        ax.set_xlabel("City")
        ax.set_ylabel("Number of listings")
        ax.legend(title="Furnishing")
        plt.xticks(rotation=0)
        st.pyplot(fig)
        st.caption("Interpretation: shows which furnishing type is most common in each city.")

    # ---------- LINE CHARTS (side by side) ----------
    st.write("### 2. Line Charts")
    l1, l2 = st.columns(2)

    with l1:
        line_data = df.groupby(["bhk", "city"])["rent"].mean().unstack()
        fig, ax = plt.subplots(figsize=(6, 4))
        for c in line_data.columns:
            ax.plot(line_data.index, line_data[c], marker="o", label=c)
        ax.set_title("Average Rent as Number of Bedrooms Increases")
        ax.set_xlabel("BHK (bedrooms)")
        ax.set_ylabel("Average rent (Rs)")
        ax.set_xticks(sorted(df["bhk"].unique()))
        ax.legend(title="City")
        st.pyplot(fig)
        st.caption("Interpretation: rent goes up with every extra bedroom, and the rise is steeper for bigger homes.")

    with l2:
        bath_data = df[df["bathrooms"] <= 6].groupby(["bathrooms", "city"])["rent"].mean().unstack()
        fig, ax = plt.subplots(figsize=(6, 4))
        for c in bath_data.columns:
            ax.plot(bath_data.index, bath_data[c], marker="s", label=c)
        ax.set_title("Average Rent as Number of Bathrooms Increases")
        ax.set_xlabel("Number of bathrooms")
        ax.set_ylabel("Average rent (Rs)")
        ax.legend(title="City")
        st.pyplot(fig)
        st.caption("Interpretation: homes with more bathrooms are bigger and cost more.")

    # ---------- SCATTER PLOT ----------
    st.write("### 3. Scatter Plot")
    with st.container():
        x_col = st.selectbox("Select X-axis variable", ["area", "bathrooms", "beds", "balconies"])
        fig, ax = plt.subplots(figsize=(10, 4.5))
        for c in sorted(df["city"].unique()):
            part = df[df["city"] == c]
            ax.scatter(part[x_col], part["rent"], alpha=0.5, s=12, label=c)
        ax.set_title(f"{x_col} vs Monthly Rent")
        ax.set_xlabel(x_col)
        ax.set_ylabel("Monthly rent (Rs)")
        ax.ticklabel_format(style="plain", axis="y")
        ax.legend(title="City")
        st.pyplot(fig)
        r = df[x_col].corr(df["rent"])
        st.caption(f"Interpretation: correlation between {x_col} and rent is {r:.2f}. "
                   "Points far above the main cluster are luxury listings (outliers).")

    with st.expander("Extra: Box plot of rent by city"):
        fig, ax = plt.subplots(figsize=(8, 4))
        cities = sorted(df["city"].unique())
        ax.boxplot([df[df["city"] == c]["rent"] for c in cities], showfliers=False)
        ax.set_xticklabels(cities)
        ax.set_title("Distribution of Rent by City")
        ax.set_xlabel("City")
        ax.set_ylabel("Monthly rent (Rs)")
        st.pyplot(fig)

# ================= TAB 4 : INSIGHTS =================
with tab4:
    st.subheader("Key Insights (based on the selected filters)")

    city_rent = df.groupby("city")["rent"].mean()
    furn_rent = df.groupby("furnishing")["rent"].mean()
    area_corr = df["area"].corr(df["rent"])

    i1, i2 = st.columns(2)
    with i1:
        with st.container():
            st.write("#### City comparison")
            st.write("Most expensive city:", city_rent.idxmax(), f"(Rs {city_rent.max():,.0f})")
            st.write("Cheapest city:", city_rent.idxmin(), f"(Rs {city_rent.min():,.0f})")
        with st.container():
            st.write("#### Furnishing")
            st.write("Highest average rent:", furn_rent.idxmax(), f"(Rs {furn_rent.max():,.0f})")
            st.write("Lowest average rent:", furn_rent.idxmin(), f"(Rs {furn_rent.min():,.0f})")
    with i2:
        with st.container():
            st.write("#### Size and rent")
            st.write("Correlation of area and rent:", round(area_corr, 2))
            st.write("Most common BHK:", int(df["bhk"].mode()[0]))
            st.write("Average rent per sq.ft:", f"Rs {df['rent_per_sqft'].mean():,.1f}")
        with st.container():
            st.write("#### Top 5 localities by average rent")
            top = df.groupby("locality")["rent"].agg(["mean", "count"])
            top = top[top["count"] >= 5].sort_values("mean", ascending=False).head(5)
            st.dataframe(top.round(0))

    with st.expander("Conclusion"):
        st.write("- Tenants can find budget-friendly cities, sizes and furnishing types.")
        st.write("- Owners can compare rent per sq.ft to fix a fair rent.")
        st.write("- Rent depends mainly on city and size of the house.")
