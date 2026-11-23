import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import re
import os
import base64

# ============ PAGE CONFIG ============
st.set_page_config(
    page_title="SCJ KOL Dashboard",
    page_icon="📊",
    layout="wide"
)

# ============ CUSTOM COLORS ============
NAVY = "#000749"      # primary dark (text, headers)
BLUE = "#4F7FF2"      # bright accent
PURPLE = "#4E2B81"
MAGENTA = "#B0228C"

# ============ FONT: POPPINS + COLOR THEME ============
# Poppins is loaded from Google Fonts and applied app-wide (text, inputs,
# buttons, tables, chart tooltips). Material icon glyphs are excluded so
# expander arrows / the sidebar toggle keep working.
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');

html, body, .stApp,
.stApp *:not([data-testid="stIconMaterial"]):not(.material-icons):not(.material-symbols-rounded),
#vg-tooltip-element, #vg-tooltip-element *,
.vega-embed, .vega-embed * {
    font-family: 'Poppins', sans-serif;
}

/* Sidebar: soft tinted background with a gradient edge */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #f3f5fd 0%, #ffffff 100%);
    border-right: 3px solid transparent;
    border-image: linear-gradient(180deg, #4F7FF2, #4E2B81, #B0228C) 1;
}

/* Multiselect tags (e.g. "Select All") */
span[data-baseweb="tag"] {
    background-color: #000749 !important;
    color: #ffffff !important;
}
span[data-baseweb="tag"] * { color: #ffffff !important; }

/* Buttons: navy outline, magenta on hover */
.stButton > button {
    border: 1px solid #000749;
    color: #000749;
}
.stButton > button:hover,
.stButton > button:focus:not(:active) {
    border-color: #B0228C;
    color: #B0228C;
}

/* Input focus ring */
.stTextInput input:focus { border-color: #4F7FF2 !important; box-shadow: 0 0 0 1px #4F7FF2 !important; }
</style>
""", unsafe_allow_html=True)


# ============ LOGO ============
# The logo is embedded in this script (Omnicom Media / SC Johnson), so it
# always shows, even if the PNG isn't next to the script. If a file named
# LOGO_FILE exists in the same folder as this script, that file is used
# instead -- handy for swapping the logo without editing code.
LOGO_FILE = "Logo_OM_x_SCJ.png"
LOGO_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), LOGO_FILE)

LOGO_B64 = (
    "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"
    "9pxfcrpV3gHgyI4d48XMzCc88OsEfJyJbnEAalVUqvCAkKoAIMwr7aqqCrSh8AURCiIYIgRVNKqo2/8ekGoDIhKgZCJXAHDUHsrH"
    "72hUBapCRKSp21JrJTAFEfWIwAD6ImeJaI9V/fyb1v7l9n37ZoBhK7iQ51MmkxX0TCaTyWQymcw7SUXf3J133vmp8fHxTzLzmPf+"
    "0enp6T97/fXX+8iF4d59RX3XLqapqaHH+cjWrdcq818TkV92wAON6vYe82TBPFS8PQCvCm292hq98+0hiVRVORaao+jRpvh9ClXR"
    "NudcQKRQpaj4MwBjieCiAm+iR19UjwrwA0f0V1UI37jtpZdeHo5h1y6DqSnJueaZTFbQM5lMJpPJZDLLyHy7du3iZ5555o4Qwt/d"
    "uHHj/WNjY08ePHjwC0ePHn0dC7s4ZN5tRX2+z3no/J1fvf32W8bL8n216v2W6F4FtjYitzqiDZa5sACYWvFeWqX9HS06oLEUHObD"
    "Klo3fOsVV1UIgFo1eNWzhugQAftU9dmC6AcniH587wsvnOyeVzxEVswzmQtAzkHPZDKZTCaT+RlWzJPydPDgwY1lWX44hHBDVVV9"
    "7/1LR48ePRzfx8i5wuvlhmm6F0lZf3TnTqI9ezwOHjwE4BCAvwCA3QD/3j33XGVEbvKqmwcimwDc5IDrlPkaqF4pqhPK3FORnhIZ"
    "qDIRCVQDiCpS7VvmaRU5rUTHPfCGU32tcO6NOoTX/+CFF96cGpkbCjB27aLPTE0p5aiLTCaTyWQymUwmk1m1gs4AcPPNN1/9nve8"
    "53e3b9/+2Xvuuee/vPHGG68ZUeIz6xgFKLZHM7F9Gl/C72bdudPGdm15rmQymUwmk8lkMpnMeSjpAOC2bNly7/bt2//Wfffdd3P8"
    "G+fLc3nfW21frIB5ZOdOG/uZD/uexxct85rvhx6Pobt2pc9n400mk8lkMplMJpPJXELFPZPJZDKZTCaTyWQymcy7oJRzVs4zmUxm"
    "fZLDmjKZTCaTyWQymUwmk8lkMplMJpPJZDKZTCaTyWQymUwmk8lkMplMJpPJZDKZTCaTyWQymUwmk8lkMplMJpPJZDKZTCaTyWQy"
    "mUwmk8lkMplMJpPJZDKZTCaTyWQymUwmk8lkMplMJpPJZDKZTCaTyWQymUwmk8lkMplMJpPJZDKZTCaTyWQymUwmk8lkMplMJpPJ"
    "ZDKZTCaTyWQymUwmk8lkMplMJpPJZDKZTCaTyWQymUwmk8lkMplMJpPJZDKZTCaTyWQymUwmk8lkMplMJpPJZDKZTCaTyWQymUwm"
    "k8lkMplMJpPJZDKZTCaTyWQymUwmk8lkMplMJpPJZDKZTCaTyWQymUwmk8lkMplMJpPJZDKZTCaTyWQymUwmk8lkMplMJpPJZDKZ"
    "TCaTyWQymUwmk8lkMplMJpPJZDKZTCaTyWQymcxa+f8BWGWPYfyyQIkAAAAASUVORK5CYII="
)


def get_logo():
    if os.path.exists(LOGO_PATH):
        return LOGO_PATH
    return base64.b64decode(LOGO_B64)


# ============ CUT OFF DATE (edit this each month) ============
CUT_OFF_DATE = "31-July-2027"

# ============ SIDEBAR WITH LOGO (TOP) ============
with st.sidebar:
    try:
        st.image(get_logo(), use_container_width=True)
    except TypeError:
        # Newer Streamlit versions replaced use_container_width with width
        st.image(get_logo(), width="stretch")
    except Exception as e:
        st.caption(f"Logo could not be loaded: {e}")

    st.markdown(f"""
    <div style="text-align: center; color: {NAVY}; font-size: 18px; font-weight: bold; margin-bottom: 20px;">
        S. C. Johnson & Son<br>Baygon LE Content Dashboard
    </div>
    """, unsafe_allow_html=True)

    st.divider()


# ============ LOAD DATA ============
# Name of the data file (must sit in the same folder as this script).
DATA_FILE = 'Baygon LE - Report Dashboard - KOL Data Input (Dummy).csv'


def detect_separator(path, encoding):
    """Pick the delimiter that appears most in the header row."""
    with open(path, 'r', encoding=encoding, errors='replace') as f:
        header = f.readline()
    candidates = {';': header.count(';'), ',': header.count(','), '\t': header.count('\t')}
    return max(candidates, key=candidates.get)


@st.cache_data
def load_data(path, modified_time):
    # `modified_time` is only here so the cache refreshes whenever the
    # file is replaced/edited (otherwise Streamlit keeps serving old data).
    for enc in ('utf-8-sig', 'latin-1'):
        try:
            sep = detect_separator(path, enc)
            return pd.read_csv(path, sep=sep, encoding=enc)
        except Exception:
            continue
    return pd.DataFrame()


if not os.path.exists(DATA_FILE):
    st.error(f"❌ Could not find '{DATA_FILE}'")
    st.info(
        "Put the CSV in the same folder as this script, or update "
        "DATA_FILE at the top of the data-loading section. "
        f"Files currently in the folder: {', '.join(sorted(os.listdir('.')))}"
    )
    st.stop()

df = load_data(DATA_FILE, os.path.getmtime(DATA_FILE))

if df.empty:
    st.error("❌ The file was found but could not be read as a table.")
    st.stop()


# ============ REMOVE UNWANTED COLUMNS ============
# Remove "0,019918483" column if it exists
df = df.loc[:, ~df.columns.astype(str).str.contains('0,019918483', na=False)]


# ============ CLEAN COLUMN NAMES ============
df.columns = [
    str(col).replace('\ufeff', '').strip()
    .replace(' ', '_')
    .replace('/', '_')
    .replace('-', '_')
    .replace('(', '')
    .replace(')', '')
    .replace(',', '_')
    for col in df.columns
]

# "VR (%)" turns into "VR_%" after cleaning; the rest of the code expects "VR"
df = df.rename(columns={'VR_%': 'VR'})

if 'Category.1' in df.columns:
    df = df.rename(columns={'Category': 'Product', 'Category.1': 'Category'})


# ============ DROP COLUMNS THAT ARE NOT USED ============
# Link_Post is no longer displayed anywhere in the dashboard.
df = df.drop(columns=['Link_Post'], errors='ignore')


# ============ FIX: PROPERLY HANDLE PRODUCT ============
# Check if we have a Product column
has_product = any(col in df.columns for col in ['Product', 'product', 'Produk', 'produk', 'PRODUCT'])

# If we have a Product column, rename it to Product
if has_product:
    product_columns = ['Product', 'product', 'Produk', 'produk', 'PRODUCT', 'Product_Name', 'product_name']
    for col in df.columns:
        if col in product_columns:
            df = df.rename(columns={col: 'Product'})
            break
# If no product but we have first column that might be product
elif not has_product and len(df.columns) > 0:
    first_col = df.columns[0]
    # If first column has text values (not numeric, not KOL_Name, not Month)
    if (df[first_col].dtype == 'object' and
        first_col not in ['KOL_Name', 'Platform', 'Tier', 'Brands', 'Sub_Brands', 'Objective', 'Month', 'Category']):
        df = df.rename(columns={first_col: 'Product'})

# Clean Product values
if 'Product' in df.columns:
    df['Product'] = df['Product'].astype(str).str.strip()


# ============ CLEAN PLATFORM NAMES ============
if 'Platform' in df.columns:
    df['Platform'] = df['Platform'].astype(str).str.strip()

    # Standardize TikTok variations
    df['Platform'] = df['Platform'].str.replace(
        'Tiktok', 'TikTok', case=False
    )
    df['Platform'] = df['Platform'].str.replace(
        'tiktok', 'TikTok', case=False
    )

    # Standardize X
    df['Platform'] = df['Platform'].str.replace(
        'x', 'X', case=False
    )

    # Standardize Instagram
    df['Platform'] = df['Platform'].str.replace(
        'instagram', 'Instagram', case=False
    )

    # Clean up extra spaces
    df['Platform'] = df['Platform'].str.strip()


# ============ CLEAN TIER NAMES ============
if 'Tier' in df.columns:
    df['Tier'] = df['Tier'].astype(str).str.strip()
    df['Tier'] = df['Tier'].str.capitalize()


# ============ CLEAN CATEGORY NAMES ============
if 'Category' in df.columns:
    df['Category'] = df['Category'].astype(str).str.strip()


# ============ CLEAN BRANDS ============
if 'Brands' in df.columns:
    df['Brands'] = df['Brands'].astype(str).str.strip()


# ============ CONVERT DATA TYPES ============
# Currency/count fields: some Excel exports (especially after merging
# multiple sheets) use a period as the thousands separator (e.g.
# "3.475.000"), not just a comma. If we only strip commas, values like
# that fail to parse and silently become NaN -- which is what was making
# Actual_Spends_IDR (and therefore Spend/CPV) collapse to 0. Strip BOTH
# separators here since these are whole-rupiah / whole-count fields with
# no decimals to preserve.
currency_count_cols = [
    'Followers_Number',
    'Actual_Spends_IDR',
    'Reach',
    'Views',
    'Likes',
    'Comments',
    'Share',
    'CPV_Rp'
]

for col in currency_count_cols:
    if col in df.columns:
        df[col] = (
            df[col]
            .astype(str)
            .str.replace('Rp', '', regex=False)
            .str.replace('%', '', regex=False)
            .str.replace('.', '', regex=False)
            .str.replace(',', '', regex=False)
            .str.strip()
        )
        df[col] = pd.to_numeric(df[col], errors='coerce')


# Percent fields: cleaning left exactly as before (comma stripped, not
# converted to a decimal point). This preserves the existing ~100x scale
# these values end up at, which is already compensated for everywhere
# ER/VR/ER_Views are displayed elsewhere in this file (KPI card, Top 10
# table, KOL search). Changing this here would silently break those.
percent_cols = [
    'ER',
    'ER_Views',
    'VR'
]

for col in percent_cols:
    if col in df.columns:
        df[col] = (
            df[col]
            .astype(str)
            .str.replace('%', '')
            .str.replace(',', '')
            .str.strip()
        )
        df[col] = pd.to_numeric(df[col], errors='coerce')


df_columns_debug = list(df.columns)
raw_month_values = []

# ============ FIX: CLEAN AND PARSE MONTHS ============
# Accepts formats like "Jan-26", "Nov-26", "November 2026", "2026-11",
# "01/11/2026". Rows whose month can't be read are dropped (junk rows).
if 'Month' in df.columns:
    raw_month_values = df['Month'].astype(str).str.strip().unique()[:10].tolist()
    month_str = df['Month'].astype(str).str.strip()

    parsed = pd.to_datetime(month_str, format='%b-%y', errors='coerce')

    for fmt in ('%B-%y', '%b %Y', '%B %Y', '%b-%Y', '%B-%Y', '%Y-%m', '%m/%Y'):
        missing = parsed.isna()
        if not missing.any():
            break
        parsed[missing] = pd.to_datetime(
            month_str[missing], format=fmt, errors='coerce'
        )

    missing = parsed.isna()
    if missing.any():
        parsed[missing] = pd.to_datetime(
            month_str[missing], errors='coerce', dayfirst=True
        )

    # Normalise everything to the 1st of the month
    df['Month'] = parsed.dt.to_period('M').dt.to_timestamp()
    df = df[df['Month'].notna()]



# ============ DIAGNOSTICS: NOTHING SURVIVED CLEANING ============
if df.empty:
    st.error("❌ The file loaded, but no usable rows remained after cleaning.")
    st.write("**Columns found after cleaning:**", list(df_columns_debug))
    if 'Month' in df_columns_debug:
        st.write("**Sample Month values in the file:**", raw_month_values)
    else:
        st.write("No 'Month' column was found - check the header name in the CSV.")
    st.stop()


# ============ HELPER FUNCTION TO CLEAN KOL NAME ============
def clean_kol_name(name):
    """Remove numbers/prefixes before KOL name and clean up"""

    if pd.isna(name):
        return name

    name = str(name).strip()

    # Remove patterns like "593 " or "123 " at the start
    name = re.sub(r'^\d+\s+', '', name)

    # Remove any remaining leading numbers
    name = re.sub(r'^\d+', '', name)

    name = name.strip()

    # Remove zero-width spaces and other special chars
    name = name.replace('\u200b', '').replace('\u00a0', ' ')

    # Clean up multiple spaces
    name = re.sub(r'\s+', ' ', name)

    return name


# ============ APPLY CLEAN KOL NAME TO DATAFRAME ============
if 'KOL_Name' in df.columns:
    df['KOL_Name_Original'] = df['KOL_Name']
    df['KOL_Name'] = df['KOL_Name'].apply(clean_kol_name)


# ============ SIDEBAR FILTERS (MONTH + TIER) ============
# Behaviour of the multiselects:
#  * "Select All" alone      -> everything is included (only that one tag shows)
#  * pick a specific item    -> "Select All" is removed automatically
#  * pick "Select All" again -> every other item is cleared, only "Select All" stays
#  * clear everything / manually pick every item -> back to "Select All"
SELECT_ALL = 'Select All'


def normalize_multiselect(key, all_items):
    """on_change callback: keeps 'Select All' and specific picks consistent."""
    current = list(st.session_state.get(key, []))
    previous = st.session_state.get(key + '_prev', [SELECT_ALL])

    if not current:
        new = [SELECT_ALL]
    elif SELECT_ALL in current and SELECT_ALL not in previous:
        # "Select All" was just clicked -> keep only it
        new = [SELECT_ALL]
    elif SELECT_ALL in current and len(current) > 1:
        # a specific item was picked while "Select All" was active -> drop it
        new = [x for x in current if x != SELECT_ALL]
    elif set(current) == set(all_items):
        # every item picked one by one -> collapse to "Select All"
        new = [SELECT_ALL]
    else:
        new = current

    st.session_state[key] = new
    st.session_state[key + '_prev'] = new


def reset_filters():
    for k in ('month_filter', 'tier_filter'):
        st.session_state[k] = [SELECT_ALL]
        st.session_state[k + '_prev'] = [SELECT_ALL]


for _k in ('month_filter', 'tier_filter'):
    if _k not in st.session_state:
        st.session_state[_k] = [SELECT_ALL]
        st.session_state[_k + '_prev'] = [SELECT_ALL]


with st.sidebar:
    st.subheader("Filters")

    filtered_df = df.copy()

    # ============ FILTER BY MONTH ============
    if 'Month' in df.columns and pd.api.types.is_datetime64_any_dtype(df['Month']):

        sorted_months = [
            dt.strftime('%b-%y')
            for dt in sorted(df['Month'].unique())
        ]

        st.multiselect(
            "Select Months",
            options=[SELECT_ALL] + sorted_months,
            key='month_filter',
            on_change=normalize_multiselect,
            args=('month_filter', sorted_months)
        )

        selected_months = st.session_state['month_filter']

        if SELECT_ALL not in selected_months:
            filtered_df = filtered_df[
                filtered_df['Month']
                .dt.strftime('%b-%y')
                .isin(selected_months)
            ]


    # ============ FILTER BY TIER ============
    if 'Tier' in df.columns:

        sorted_tiers = sorted(
            df['Tier']
            .dropna()
            .unique()
            .tolist()
        )

        st.multiselect(
            "Select Tiers",
            options=[SELECT_ALL] + sorted_tiers,
            key='tier_filter',
            on_change=normalize_multiselect,
            args=('tier_filter', sorted_tiers)
        )

        selected_tiers = st.session_state['tier_filter']

        if SELECT_ALL not in selected_tiers:
            filtered_df = filtered_df[
                filtered_df['Tier'].isin(selected_tiers)
            ]


    # ============ CLEAR ALL FILTERS ============
    st.button(
        "Clear All Filters",
        use_container_width=True,
        on_click=reset_filters
    )


# ============ FORMATTING FUNCTIONS ============
def format_number(num):

    if pd.isna(num) or num == 0:
        return "0"

    num = float(num)

    if num >= 1_000_000_000:
        val = num / 1_000_000_000
        return f"{val:.1f}B".replace('.0B', 'B')

    elif num >= 1_000_000:
        val = num / 1_000_000
        return f"{val:.1f}M".replace('.0M', 'M')

    elif num >= 1_000:
        val = num / 1_000
        return f"{val:.1f}K".replace('.0K', 'K')

    else:
        return f"{num:,.0f}"


def format_currency(num):

    if pd.isna(num) or num == 0:
        return "Rp 0"

    num = float(num)

    if num >= 1_000_000_000:
        val = num / 1_000_000_000
        return f"Rp {val:.1f}B".replace('.0B', 'B')

    elif num >= 1_000_000:
        val = num / 1_000_000
        return f"Rp {val:.1f}M".replace('.0M', 'M')

    elif num >= 1_000:
        val = num / 1_000
        return f"Rp {val:.1f}K".replace('.0K', 'K')

    else:
        return f"Rp {num:,.0f}"


def format_percent(num):

    if pd.isna(num):
        return "0%"

    if num <= 1:
        num = num * 100

    formatted = f"{num:.2f}%"

    formatted = formatted.replace('.00%', '%')

    if '.' in formatted:
        while formatted.endswith('0%'):
            formatted = formatted[:-2] + '%'

        if formatted.endswith('.%'):
            formatted = formatted[:-2] + '%'

    return formatted


def format_currency_short(num):

    if pd.isna(num) or num == 0:
        return "Rp 0"

    return f"Rp {num:,.2f}"


# ============ BAR CHART FUNCTION ============
def create_bar_chart(data, x_col, y_col, color=None):

    df = data.reset_index()

    df.columns = [x_col, y_col]

    # Soft vertical gradient (bright blue -> navy) unless a flat color is given
    bar_fill = color if color else alt.Gradient(
        gradient='linear',
        stops=[
            alt.GradientStop(color='#6f96f7', offset=0),
            alt.GradientStop(color=NAVY, offset=1)
        ],
        x1=1, x2=1, y1=0, y2=1
    )

    bars = alt.Chart(df).mark_bar(
        color=bar_fill,
        cornerRadiusTopLeft=6,
        cornerRadiusTopRight=6
    ).encode(

        x=alt.X(
            x_col + ':O',
            axis=alt.Axis(
                labels=True,
                title=None,
                labelAngle=0
            ),
            sort=None
        ),

        y=alt.Y(
            y_col + ':Q',
            axis=alt.Axis(
                labels=False,
                title=None,
                grid=False
            )
        ),

        tooltip=[
            x_col,
            alt.Tooltip(
                y_col,
                format=',.0f'
            )
        ]
    )

    text = alt.Chart(df).mark_text(
        align='center',
        baseline='bottom',
        dy=-10,
        fontSize=13,
        font='Poppins',
        fontWeight='bold',
        color=NAVY
    ).encode(

        x=alt.X(
            x_col + ':O',
            sort=None
        ),

        y=alt.Y(
            y_col + ':Q'
        ),

        text=alt.Text(
            y_col + ':Q',
            format=',.0f'
        )
    )

    chart = (
        bars + text
    ).properties(
        width='container',
        height=350
    ).configure_view(
        strokeWidth=0
    ).configure_axis(
        labelFontSize=12,
        labelFont='Poppins',
        labelColor='#5b6180',
        grid=False
    )

    return chart


# ============ RESPONSIVE STACKED BAR (pure HTML/CSS) ============
# The horizontal stacked charts are drawn with HTML + CSS instead of a
# canvas chart. Widths are percentages, so they follow the container
# exactly when the window is resized or the page is zoomed in/out, and a
# segment's % label is hidden by a CSS container query whenever its
# segment gets too narrow to hold it.
st.markdown("""
<style>
.sb-wrap { width: 100%; margin: 6px 0 10px 0; }
.sb-legend {
    display: flex; flex-wrap: wrap; justify-content: center;
    gap: 8px 18px; margin-bottom: 14px; font-size: 13px; color: #000749;
}
.sb-chip { display: inline-flex; align-items: center; gap: 6px; }
.sb-dot { width: 10px; height: 10px; border-radius: 50%; display: inline-block; }
.sb-row { display: flex; align-items: center; gap: 12px; margin: 8px 0; }
.sb-month { flex: 0 0 58px; font-size: 12px; color: #5b6180; text-align: right; }
.sb-track { flex: 1 1 auto; min-width: 0; }
.sb-bar {
    display: flex; height: 34px; border-radius: 8px; overflow: hidden;
    box-shadow: 0 1px 3px rgba(0, 7, 73, 0.12);
}
.sb-seg {
    container-type: inline-size;
    display: flex; align-items: center; justify-content: center;
    min-width: 0; overflow: hidden; transition: filter 0.15s ease;
}
.sb-seg:hover { filter: brightness(1.12); }
.sb-lbl { display: none; font-size: 11px; font-weight: 600; white-space: nowrap; }
@container (min-width: 34px) { .sb-lbl { display: block; } }
</style>
""", unsafe_allow_html=True)


def _is_light(hex_color):
    """True if a hex color is light enough to need dark label text."""
    h = hex_color.lstrip('#')
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return (0.299 * r + 0.587 * g + 0.114 * b) > 165


def render_stacked_bars(data, group_col, order, colors):
    """Horizontal 100%-style stacked bars per month, scaled to the largest month."""
    import html as _html

    d = data.copy()
    d[group_col] = d[group_col].astype(str)

    months = sorted(d['Month'].unique())
    totals = d.groupby('Month')['Actual_Spends_IDR'].sum()
    max_total = totals.max() if len(totals) else 0

    color_map = {str(g): colors[i % len(colors)] for i, g in enumerate(order)}

    legend = ''.join(
        f'<span class="sb-chip"><span class="sb-dot" style="background:{color_map[str(g)]}"></span>'
        f'{_html.escape(str(g))}</span>'
        for g in order
    )

    rows = []
    for m in months:
        m_label = pd.Timestamp(m).strftime('%b-%y')
        mdf = d[d['Month'] == m]
        total = float(totals.get(m, 0) or 0)
        bar_w = (total / max_total * 100) if max_total and max_total > 0 else 0

        segs = []
        for g in order:
            row = mdf[mdf[group_col] == str(g)]
            if row.empty:
                continue
            v = float(row['Actual_Spends_IDR'].iloc[0] or 0)
            if not v > 0 or total <= 0:
                continue
            share = v / total * 100
            lbl = row['Percentage_Label'].iloc[0]
            col = color_map[str(g)]
            txt = '#000749' if _is_light(col) else '#ffffff'
            tip = _html.escape(f"{m_label} | {g} | Rp {v:,.0f} | {lbl}")
            segs.append(
                f'<div class="sb-seg" style="flex:0 0 {share:.4f}%;background:{col};color:{txt}" '
                f'title="{tip}"><span class="sb-lbl">{lbl}</span></div>'
            )

        rows.append(
            f'<div class="sb-row"><div class="sb-month">{m_label}</div>'
            f'<div class="sb-track"><div class="sb-bar" style="width:{bar_w:.4f}%">'
            f'{"".join(segs)}</div></div></div>'
        )

    st.markdown(
        f'<div class="sb-wrap"><div class="sb-legend">{legend}</div>{"".join(rows)}</div>',
        unsafe_allow_html=True
    )


# ============ HEADER STYLE FUNCTIONS ============
def section_header_with_divider(title):

    st.divider()

    st.markdown(f"""
    <div style="color: #000749; font-size: 24px; font-weight: bold; margin-bottom: 15px; margin-top: 10px;">
        {title}
    </div>
    """, unsafe_allow_html=True)


def section_header_no_divider(title):

    st.markdown(f"""
    <div style="color: #000749; font-size: 24px; font-weight: bold; margin-bottom: 15px; margin-top: 10px;">
        {title}
    </div>
    """, unsafe_allow_html=True)


def section_header_with_cutoff(title, cutoff_text):

    st.markdown(f"""
    <div style="
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 15px;
        margin-top: 10px;
    ">
        <div style="color: #000749; font-size: 24px; font-weight: bold;">
            {title}
        </div>
        <div style="
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: #eef2fd;
            color: {NAVY};
            border: 1px solid #d9deef;
            border-left: 3px solid {MAGENTA};
            border-radius: 20px;
            padding: 6px 14px;
            font-size: 13px;
            font-weight: 600;
            letter-spacing: 0.3px;
            white-space: nowrap;
        ">
            📅 {cutoff_text}
        </div>
    </div>
    """, unsafe_allow_html=True)


# ============ CALCULATE CPV ============
if (
    'Actual_Spends_IDR' in filtered_df.columns
    and 'Views' in filtered_df.columns
):

    filtered_df['CPV_Calculated'] = (
        filtered_df['Actual_Spends_IDR']
        / filtered_df['Views']
    )

    filtered_df['CPV_Calculated'] = (
        filtered_df['CPV_Calculated']
        .replace([np.inf, -np.inf], np.nan)
        .fillna(0)
    )


# ============ CALCULATE KPIS ============
total_views = (
    filtered_df['Views'].sum()
    if 'Views' in filtered_df.columns
    else 0
)

total_engagement = (
    filtered_df['Likes'].sum()
    + filtered_df['Comments'].sum()
    + filtered_df['Share'].sum()
    if all(
        col in filtered_df.columns
        for col in ['Likes', 'Comments', 'Share']
    )
    else 0
)

total_spend = (
    filtered_df['Actual_Spends_IDR'].sum()
    if 'Actual_Spends_IDR' in filtered_df.columns
    else 0
)

total_reach = (
    filtered_df['Reach'].sum()
    if 'Reach' in filtered_df.columns
    else 0
)


# ============ FIXED KOL COUNT ============
if 'KOL_Name' in filtered_df.columns:

    kol_cleaned = (
        filtered_df['KOL_Name']
        .astype(str)
        .str.strip()
    )

    kol_cleaned = kol_cleaned.str.replace(
        r'\s+',
        ' ',
        regex=True
    )

    kol_cleaned = kol_cleaned.str.replace(
        '\u200b',
        '',
        regex=False
    )

    kol_cleaned = kol_cleaned.str.replace(
        '\u00a0',
        ' ',
        regex=False
    )

    # Lowercase before counting uniques: KOL handles are case-insensitive
    # on the actual platforms (e.g. "Ninitata" and "ninitata" are the same
    # account), and Excel's UNIQUE() already treats them as one entry by
    # default. Without this, pandas' case-sensitive nunique() overcounts
    # any KOL whose name appears with inconsistent capitalization.
    kol_cleaned = kol_cleaned.str.lower()

    total_kols = kol_cleaned.nunique()

else:
    total_kols = 0


total_posts = len(filtered_df)


# ============ FIXED ER CALCULATION (sum of engagement / sum of followers) ============
if (
    'Followers_Number' in filtered_df.columns
    and filtered_df['Followers_Number'].sum() > 0
):
    engagement_rate = total_engagement / filtered_df['Followers_Number'].sum()
else:
    engagement_rate = 0


avg_cpv = (
    filtered_df['Actual_Spends_IDR'].sum() / filtered_df['Views'].sum()
    if 'Actual_Spends_IDR' in filtered_df.columns
    and 'Views' in filtered_df.columns
    and filtered_df['Views'].sum() > 0
    else 0
)


# ============ KPI METRICS - ROW 1 ============
section_header_with_cutoff(
    "Overall Performance",
    f"Cut Off Date: {CUT_OFF_DATE}"
)

# Add CSS for KPI cards with elegant borders and bold headers
st.markdown("""
<style>
.kpi-card {
    border: 1.5px solid #d9deef;
    border-radius: 10px;
    padding: 16px 12px;
    margin: 5px 0;
    background: linear-gradient(135deg, #fafbff 0%, #ffffff 100%);
    box-shadow: 0 1px 3px rgba(0, 7, 73, 0.06);
    transition: all 0.25s ease;
    height: 100%;
    position: relative;
}
.kpi-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: linear-gradient(90deg, #4F7FF2, #4E2B81, #B0228C);
    border-radius: 10px 10px 0 0;
    opacity: 0.85;
}
.kpi-card:hover {
    box-shadow: 0 4px 12px rgba(0, 7, 73, 0.12);
    border-color: #b8c2e6;
    transform: translateY(-1px);
}
.kpi-label {
    margin-bottom: 2px;
    color: #000749;
    font-size: 13px;
    text-align: center;
    font-weight: 700;
    letter-spacing: 0.5px;
    text-transform: uppercase;
}
.kpi-value {
    font-size: 24px;
    font-weight: 600;
    margin-top: 2px;
    text-align: center;
    color: #000749;
    letter-spacing: -0.5px;
}
</style>
""", unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="kpi-card">
        <p class="kpi-label">Views</p>
        <p class="kpi-value">{format_number(total_views)}</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="kpi-card">
        <p class="kpi-label">Reach</p>
        <p class="kpi-value">{format_number(total_reach)}</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="kpi-card">
        <p class="kpi-label">Engagement</p>
        <p class="kpi-value">{format_number(total_engagement)}</p>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="kpi-card">
        <p class="kpi-label">Spend</p>
        <p class="kpi-value">{format_currency(total_spend)}</p>
    </div>
    """, unsafe_allow_html=True)


# ============ KPI METRICS - ROW 2 ============
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="kpi-card">
        <p class="kpi-label">Total KOLs</p>
        <p class="kpi-value">{total_kols:,}</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="kpi-card">
        <p class="kpi-label">Total Posts</p>
        <p class="kpi-value">{total_posts:,}</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="kpi-card">
        <p class="kpi-label">ER</p>
        <p class="kpi-value">{format_percent(engagement_rate)}</p>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="kpi-card">
        <p class="kpi-label">Avg CPV</p>
        <p class="kpi-value">Rp {round(avg_cpv):,}</p>
    </div>
    """, unsafe_allow_html=True)


# ============ VISUALIZATIONS ============
section_header_with_divider("Visualizations")


# ============================================================
# SPEND BY MONTH
# ============================================================
st.markdown(f"""
<div style="text-align: center; font-size: 18px; font-weight: bold; color: {NAVY}; margin-bottom: 10px;">
    Spend by Month
</div>
""", unsafe_allow_html=True)


monthly_data = (
    filtered_df
    .groupby('Month')['Actual_Spends_IDR']
    .sum()
    .sort_index()
)


if not monthly_data.empty:

    monthly_data.index = monthly_data.index.strftime('%b-%y')

    chart = create_bar_chart(
        monthly_data,
        'Month',
        'Actual_Spends_IDR'
    )

    st.altair_chart(
        chart,
        use_container_width=True
    )

else:

    st.info(
        "No data available for Spend by Month"
    )


# ============================================================
# SPEND BY TIER - HORIZONTAL STACKED BAR
# ============================================================
st.markdown("<br>", unsafe_allow_html=True)

st.markdown(f"""
<div style="text-align: center; font-size: 18px; font-weight: bold; color: {NAVY}; margin-bottom: 10px;">
    Spend by Tier (Monthly)
</div>
""", unsafe_allow_html=True)


if (
    'Tier' in filtered_df.columns
    and 'Month' in filtered_df.columns
):

    tier_month_data = (
        filtered_df
        .groupby(
            ['Month', 'Tier'],
            as_index=False
        )['Actual_Spends_IDR']
        .sum()
    )

    # CALCULATE MONTHLY TOTAL
    month_totals = (
        tier_month_data
        .groupby('Month', as_index=False)['Actual_Spends_IDR']
        .sum()
    )

    month_totals.columns = [
        'Month',
        'Total_Spend'
    ]

    tier_month_data = tier_month_data.merge(
        month_totals,
        on='Month'
    )

    # CALCULATE PERCENTAGE
    tier_month_data['Percentage'] = (
        tier_month_data['Actual_Spends_IDR']
        / tier_month_data['Total_Spend']
        * 100
    )

    tier_month_data['Percentage'] = (
        tier_month_data['Percentage']
        .round(0)
        .fillna(0)  # guard against NaN from a 0-total group (0/0)
    )

    tier_month_data['Percentage_Label'] = (
        tier_month_data['Percentage']
        .astype(int)
        .astype(str)
        + '%'
    )

    # MONTH ORDER
    tier_month_data['Month_Str'] = (
        tier_month_data['Month']
        .dt.strftime('%b')
    )

    month_order = sorted(
        tier_month_data['Month'].unique()
    )

    month_order_str = [
        m.strftime('%b')
        for m in month_order
    ]


    if not tier_month_data.empty:

        # TIER ORDER
        existing_tiers = (
            tier_month_data['Tier']
            .dropna()
            .unique()
            .tolist()
        )

        tier_order = existing_tiers

        # FORCE CONSISTENT TIER ORDER
        tier_month_data['Tier'] = pd.Categorical(
            tier_month_data['Tier'],
            categories=tier_order,
            ordered=True
        )

        tier_month_data = (
            tier_month_data
            .sort_values(
                ['Month', 'Tier']
            )
            .reset_index(drop=True)
        )

        # CALCULATE EXACT SEGMENT POSITIONS
        tier_month_data['Segment_End'] = (
            tier_month_data
            .groupby(
                'Month',
                observed=True
            )['Actual_Spends_IDR']
            .cumsum()
        )

        tier_month_data['Segment_Start'] = (
            tier_month_data['Segment_End']
            - tier_month_data['Actual_Spends_IDR']
        )

        tier_month_data['Label_Position'] = (
            tier_month_data['Segment_Start']
            + (
                tier_month_data['Actual_Spends_IDR']
                / 2
            )
        )

        tier_month_data['Segment_Width'] = (
            tier_month_data['Segment_End']
            - tier_month_data['Segment_Start']
        )

        # COLORS
        tier_colors = [
            NAVY,
            BLUE,
            PURPLE,
            '#8b63d0',
            '#8aa4f7'
        ]

        while len(tier_colors) < len(tier_order):
            tier_colors.append('#e8e8e8')

        # RENDER (responsive HTML/CSS bars)
        render_stacked_bars(
            tier_month_data,
            'Tier',
            tier_order,
            tier_colors
        )

    else:

        st.info(
            "No data available for Spend by Tier"
        )

else:

    st.info(
        "Data not available for stacked chart"
    )


# ============================================================
# SPEND BY CATEGORY - HORIZONTAL STACKED BAR
# ============================================================
st.markdown("<br>", unsafe_allow_html=True)

st.markdown(f"""
<div style="text-align: center; font-size: 18px; font-weight: bold; color: {NAVY}; margin-bottom: 10px;">
    Spend by Category (Monthly)
</div>
""", unsafe_allow_html=True)


if (
    'Category' in filtered_df.columns
    and 'Month' in filtered_df.columns
):

    category_month_data = (
        filtered_df
        .groupby(
            ['Month', 'Category'],
            as_index=False
        )['Actual_Spends_IDR']
        .sum()
    )

    # CALCULATE MONTHLY TOTAL
    month_totals = (
        category_month_data
        .groupby('Month', as_index=False)['Actual_Spends_IDR']
        .sum()
    )

    month_totals.columns = [
        'Month',
        'Total_Spend'
    ]

    category_month_data = category_month_data.merge(
        month_totals,
        on='Month'
    )

    # CALCULATE PERCENTAGE
    category_month_data['Percentage'] = (
        category_month_data['Actual_Spends_IDR']
        / category_month_data['Total_Spend']
        * 100
    )

    category_month_data['Percentage'] = (
        category_month_data['Percentage']
        .round(0)
        .fillna(0)  # guard against NaN from a 0-total group (0/0)
    )

    category_month_data['Percentage_Label'] = (
        category_month_data['Percentage']
        .astype(int)
        .astype(str)
        + '%'
    )

    # MONTH ORDER
    category_month_data['Month_Str'] = (
        category_month_data['Month']
        .dt.strftime('%b')
    )

    month_order = sorted(
        category_month_data['Month'].unique()
    )

    month_order_str = [
        m.strftime('%b')
        for m in month_order
    ]


    if not category_month_data.empty:

        # CATEGORY ORDER
        preferred_category_order = [
            'Lifestyle',
            'Family',
            'Health',
            'Fashion',
            'Beauty',
            'Food',
            'Travel',
            'Fitness',
            'Entertainment',
            'Education',
            'Other'
        ]

        existing_categories = (
            category_month_data['Category']
            .dropna()
            .unique()
            .tolist()
        )

        category_order = [
            c
            for c in preferred_category_order
            if c in existing_categories
        ]

        for c in existing_categories:
            if c not in category_order:
                category_order.append(c)

        # FORCE CONSISTENT CATEGORY ORDER
        category_month_data['Category'] = pd.Categorical(
            category_month_data['Category'],
            categories=category_order,
            ordered=True
        )

        category_month_data = (
            category_month_data
            .sort_values(
                ['Month', 'Category']
            )
            .reset_index(drop=True)
        )

        # CALCULATE EXACT SEGMENT POSITIONS
        category_month_data['Segment_End'] = (
            category_month_data
            .groupby(
                'Month',
                observed=True
            )['Actual_Spends_IDR']
            .cumsum()
        )

        category_month_data['Segment_Start'] = (
            category_month_data['Segment_End']
            - category_month_data['Actual_Spends_IDR']
        )

        category_month_data['Label_Position'] = (
            category_month_data['Segment_Start']
            + (
                category_month_data['Actual_Spends_IDR']
                / 2
            )
        )

        category_month_data['Segment_Width'] = (
            category_month_data['Segment_End']
            - category_month_data['Segment_Start']
        )

        # COLORS
        category_colors = [
            NAVY,
            BLUE,
            PURPLE,
            '#2a3f9e',
            '#8b63d0',
            '#6c8cf5',
            '#3a2a8f',
            '#a98be0',
            '#8aa4f7',
            '#5a6fc4'
        ]

        while len(category_colors) < len(category_order):
            category_colors.append('#e8e8e8')

        # RENDER (responsive HTML/CSS bars)
        render_stacked_bars(
            category_month_data,
            'Category',
            category_order,
            category_colors
        )

    else:

        st.info(
            "No data available for Spend by Category"
        )

else:

    st.info(
        "Data not available for category chart"
    )


# ============================================================
# TOP PERFORMING KOLS
# ============================================================
section_header_with_divider(
    "Top 10 KOL Performance"
)


if 'KOL_Name' in filtered_df.columns:

    kol_agg = (
        filtered_df
        .groupby('KOL_Name')
        .agg({
            'ER': 'mean',
            'Followers_Number': 'max',
            'Actual_Spends_IDR': 'sum',
            'Tier': 'first'
        })
        .reset_index()
    )

    kol_agg['ER'] = (
        kol_agg['ER']
        .replace(
            [np.inf, -np.inf],
            np.nan
        )
        .fillna(0)
    )

    kol_agg = kol_agg.sort_values(
        'ER',
        ascending=False
    )

    top_kols = kol_agg.head(10).copy()

    top_kols['Rank'] = [
        '#' + str(i + 1)
        for i in range(len(top_kols))
    ]

    top_kols['KOL'] = top_kols['KOL_Name']

    top_kols['ER'] = (
        (top_kols['ER'] / 100)
        .apply(format_percent)
    )

    top_kols['Cost'] = (
        top_kols['Actual_Spends_IDR']
        .apply(lambda x: f"Rp {x:,.0f}" if pd.notna(x) else "Rp 0")
    )

    display_df = top_kols[
        [
            'Rank',
            'KOL',
            'Tier',
            'ER',
            'Cost'
        ]
    ]

    st.markdown("""
    <style>

    .dataframe-container {
        display: flex;
        justify-content: center;
        width: 100%;
    }

    .dataframe-container table {
        width: 80% !important;
        margin: 0 auto;
        border-collapse: collapse;
        font-family: inherit;
    }

    .dataframe-container thead tr th {
        text-align: center !important;
        background-color: #eef2fd;
        color: #000749;
        font-weight: bold;
        padding: 10px 15px;
        border-bottom: 2px solid #4F7FF2;
    }

    .dataframe-container tbody tr td {
        text-align: left !important;
        padding: 8px 15px;
        border-bottom: 1px solid #d9deef;
    }

    .dataframe-container tbody tr td:first-child {
        text-align: center !important;
    }

    </style>
    """, unsafe_allow_html=True)

    table_html = display_df.to_html(
        index=False,
        escape=False,
        classes='dataframe-container'
    )

    st.markdown(
        f'<div class="dataframe-container">'
        f'{table_html}'
        f'</div>',
        unsafe_allow_html=True
    )


# ============================================================
# KOL SEARCH FEATURE
# ============================================================
section_header_with_divider(
    "Search KOL Performance"
)


st.markdown("""
<div style="margin-bottom: 15px; color: #555; font-size: 14px;">
    Enter a KOL name to view their detailed performance metrics across all campaigns.
</div>
""", unsafe_allow_html=True)


# ============ HELPER FUNCTION TO FORMAT ER ============
def format_er_display(value):

    if pd.isna(value):
        return "0%"

    if value > 1:
        return format_percent(value / 100)

    else:
        return format_percent(value)


# ============ CREATE SEARCH INPUT ============
search_col1, search_col2 = st.columns([2, 1])


with search_col1:

    kol_search = st.text_input(
        "Enter KOL Name",
        placeholder="e.g., bschristy, _ninitata_, A'yun, or any KOL name",
        key="kol_search_input"
    )


with search_col2:

    st.write("")
    st.write("")

    search_button = st.button(
        "Search",
        use_container_width=True
    )


# ============ STYLES FOR THE KOL SEARCH TABLE ============
st.markdown("""
<style>
.table-scroll {
    width: 100%;
    overflow-x: auto;
    background: #ffffff;
    border: 1px solid #d9deef;
    border-radius: 12px;
    margin: 6px 0 14px 0;
}
.pro-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.table-scroll .pro-table th,
.table-scroll .pro-table td {
    border-top: none !important;
    border-left: none !important;
    border-right: none !important;
}
.pro-table thead th {
    background: #eef2fd; color: #000749; font-weight: 600;
    text-align: left; padding: 10px 14px; white-space: nowrap;
    border-bottom: 2px solid #4F7FF2 !important;
}
.pro-table tbody td {
    padding: 9px 14px; white-space: nowrap; color: #000749;
    border-bottom: 1px solid #d9deef !important;
}
.pro-table tbody tr:last-child td { border-bottom: none !important; }
.pro-table tbody tr:hover { background: #f6f8ff; }
</style>
""", unsafe_allow_html=True)


# ============================================================
# SHOW SEARCH RESULTS
# ============================================================
if kol_search or search_button:

    if kol_search.strip():

        search_term = kol_search.strip().lower()

        search_term = re.sub(
            r'^\d+\s+',
            '',
            search_term
        )


        if 'KOL_Name' in filtered_df.columns:

            search_df = filtered_df.copy()

            search_df['KOL_Name_Search'] = (
                search_df['KOL_Name']
                .str.lower()
            )

            matching_kols = search_df[
                search_df['KOL_Name_Search']
                .str.contains(
                    search_term,
                    na=False,
                    case=False
                )
            ]


            if not matching_kols.empty:

                unique_kols = (
                    matching_kols['KOL_Name']
                    .unique()
                )

                st.success(
                    f"✅ Found {len(unique_kols)} "
                    f"KOL(s) matching '{kol_search}'"
                )


                for kol_name in unique_kols:

                    kol_data = (
                        matching_kols[
                            matching_kols['KOL_Name']
                            == kol_name
                        ]
                        .copy()
                    )


                    with st.expander(
                        f"{kol_name}",
                        expanded=True
                    ):

                        display_kol = kol_data.copy()

                        # FORMAT NUMERIC COLUMNS
                        for col in [
                            'Views',
                            'Reach',
                            'Likes',
                            'Comments',
                            'Share',
                            'Followers_Number',
                            'Actual_Spends_IDR'
                        ]:

                            if col in display_kol.columns:

                                display_kol[col] = (
                                    display_kol[col]
                                    .apply(format_number)
                                )

                        # FORMAT ER / ER VIEWS / VR
                        for col in [
                            'ER',
                            'ER_Views',
                            'VR'
                        ]:

                            if col in display_kol.columns:

                                if display_kol[col].dtype == 'object':

                                    display_kol[col] = pd.to_numeric(
                                        display_kol[col]
                                        .astype(str)
                                        .str.replace('%', '')
                                        .str.replace(',', ''),
                                        errors='coerce'
                                    )

                                display_kol[col] = (
                                    display_kol[col]
                                    .apply(format_er_display)
                                )

                        # CALCULATE CPV
                        if 'CPV_Calculated' in display_kol.columns:

                            display_kol['CPV'] = (
                                display_kol['CPV_Calculated']
                                .apply(format_currency_short)
                            )

                        elif 'CPV_Rp' in display_kol.columns:

                            display_kol['CPV'] = (
                                display_kol['CPV_Rp']
                                .apply(format_currency_short)
                            )

                        # SELECT COLUMNS
                        display_columns = []

                        desired_order = [
                            'KOL_Name',
                            'Category',
                            'Product',
                            'Brands',
                            'Tier',
                            'Objective',
                            'Platform',
                            'Month',
                            'Actual_Spends_IDR',
                            'Views',
                            'ER',
                            'VR',
                            'Likes',
                            'CPV'
                        ]

                        for col in desired_order:

                            if col in display_kol.columns:

                                if col == 'CPV_Rp':
                                    continue

                                if col == 'CPV_Calculated':
                                    display_columns.append('CPV')

                                else:
                                    display_columns.append(col)

                        extra_columns = [
                            'Reach',
                            'Comments',
                            'Share',
                            'Followers_Number',
                            'ER_Views',
                            'Engagement'
                        ]

                        for col in extra_columns:

                            if (
                                col in display_kol.columns
                                and col not in display_columns
                            ):
                                display_columns.append(col)

                        display_columns = list(
                            dict.fromkeys(
                                display_columns
                            )
                        )

                        if not display_columns:

                            display_columns = [
                                'KOL_Name',
                                'Platform',
                                'Month',
                                'Actual_Spends_IDR',
                                'Views'
                            ]

                        display_df = (
                            display_kol[
                                display_columns
                            ]
                            .copy()
                        )

                        column_rename = {
                            'KOL_Name': 'KOL Name',
                            'Actual_Spends_IDR': 'Cost',
                            'Followers_Number': 'Followers',
                            'ER_Views': 'ER Views',
                            'Engagement': 'Engagement'
                        }

                        for old, new in column_rename.items():

                            if old in display_df.columns:

                                display_df = display_df.rename(
                                    columns={
                                        old: new
                                    }
                                )

                        # FORMAT MONTH
                        if (
                            'Month' in display_df.columns
                            and pd.api.types.is_datetime64_any_dtype(
                                display_df['Month']
                            )
                        ):

                            display_df['Month'] = (
                                display_df['Month']
                                .dt.strftime('%b-%y')
                            )

                        # DISPLAY TABLE
                        kol_table_html = display_df.to_html(
                            escape=False,
                            index=False,
                            classes='pro-table',
                            border=0
                        )

                        st.markdown(
                            f'<div class="table-scroll">{kol_table_html}</div>',
                            unsafe_allow_html=True
                        )

                        st.markdown("---")

                        st.markdown(
                            "**📈 Performance Summary**"
                        )

                        summary_col1, summary_col2, summary_col3, summary_col4 = st.columns(4)

                        with summary_col1:

                            total_posts_kol = len(kol_data)

                            st.metric(
                                "Total Posts",
                                total_posts_kol
                            )

                        with summary_col2:

                            total_views_kol = (
                                kol_data['Views'].sum()
                                if 'Views'
                                in kol_data.columns
                                else 0
                            )

                            st.metric(
                                "Total Views",
                                format_number(
                                    total_views_kol
                                )
                            )

                        with summary_col3:

                            total_spend_kol = (
                                kol_data['Actual_Spends_IDR'].sum()
                                if 'Actual_Spends_IDR'
                                in kol_data.columns
                                else 0
                            )

                            st.metric(
                                "Total Spend",
                                format_currency(
                                    total_spend_kol
                                )
                            )

                        with summary_col4:

                            if 'ER' in kol_data.columns:

                                er_values = (
                                    kol_data['ER']
                                    .dropna()
                                )

                                if len(er_values) > 0:

                                    avg_er = (
                                        er_values.mean()
                                        / 100
                                    )

                                    st.metric(
                                        "Avg ER",
                                        format_percent(
                                            avg_er
                                        )
                                    )

                                else:

                                    st.metric(
                                        "Avg ER",
                                        "N/A"
                                    )

                            else:

                                st.metric(
                                    "Avg ER",
                                    "N/A"
                                )


            else:

                st.warning(
                    f"❌ No KOL found matching "
                    f"'{kol_search}'. Please try a different name."
                )

                if 'KOL_Name' in filtered_df.columns:

                    all_kols = (
                        filtered_df['KOL_Name']
                        .unique()[:10]
                    )

                    all_kols = [
                        k
                        for k in all_kols
                        if k and not pd.isna(k)
                    ]

                    if len(all_kols) > 0:

                        st.markdown(
                            "**💡 Suggestions:**"
                        )

                        st.write(
                            ", ".join(
                                all_kols[:5]
                            )
                        )

                        if len(all_kols) > 5:

                            st.write(
                                f"... and "
                                f"{len(all_kols) - 5} more"
                            )

        else:

            st.warning(
                "KOL_Name column not found in the data."
            )

    else:

        st.info(
            "Please enter a KOL name to search."
        )

else:

    st.info(
        "Enter a KOL name above and click Search "
        "to view their performance details."
    )


# ============================================================
# CLEAR SEARCH
# ============================================================
if kol_search:

    if st.button("Clear Search"):
        st.rerun()


# ============================================================
# KEY INSIGHTS (FUTURE PROJECT)
# ============================================================
section_header_with_divider("Key Insights")
