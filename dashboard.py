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

/* Hide deploy button, main menu, toolbar actions, decoration and viewer badge,
   but NOT the toolbar container itself (the sidebar re-open button lives there) */
.stAppDeployButton,
[data-testid="stAppDeployButton"],
[data-testid="stMainMenu"],
[data-testid="stToolbarActions"],
#MainMenu,
footer,
div[data-testid="stDecoration"],
div[data-testid="stStatusWidget"],
div[class*="viewerBadge"],
a[class*="viewerBadge"],
.viewerBadge_container__r5tak,
.styles_viewerBadge__CvC9N {
    display: none !important;
    visibility: hidden !important;
}

/* Keep the header + toolbar container and the sidebar toggle visible */
header[data-testid="stHeader"] {
    background: transparent !important;
}

div[data-testid="stToolbar"] {
    display: flex !important;
    visibility: visible !important;
    background: transparent !important;
}

[data-testid="stExpandSidebarButton"],
[data-testid="stSidebarCollapsedControl"],
[data-testid="collapsedControl"] {
    display: flex !important;
    visibility: visible !important;
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

# >>> PASTE YOUR EXISTING BASE64 LOGO STRING BETWEEN THE PARENTHESES BELOW <<<
LOGO_B64 = (
    ""
)


def get_logo():
    if os.path.exists(LOGO_PATH):
        return LOGO_PATH
    if not LOGO_B64:
        return None
    return base64.b64decode(LOGO_B64)


# ============ CUT OFF DATE (edit this each month) ============
CUT_OFF_DATE = "31 September"

# ============ LOGO (SIDEBAR + COLLAPSED STATE, CLICKABLE) ============
LOGO_LINK = "https://omc-scj-analytics-hub.netlify.app/"

_logo = get_logo()
if _logo is not None:
    try:
        # `size` needs a recent Streamlit; fall back if it isn't supported
        st.logo(_logo, icon_image=_logo, link=LOGO_LINK, size="large")
    except TypeError:
        st.logo(_logo, icon_image=_logo, link=LOGO_LINK)

# ============ SIDEBAR TITLE ============
with st.sidebar:
    st.markdown(f"""
    <div style="text-align: center; color: {NAVY}; font-size: 18px; font-weight: bold; margin-bottom: 20px;">
        Baygon LE Content Dashboard
    </div>
    """, unsafe_allow_html=True)

    st.divider()


# ============ LOAD DATA ============
# Name of the data file (must sit in the same folder as this script).
DATA_FILE = 'Baygon LE - Report Dashboard - KOL Data Input.csv'


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


# ============ CLEAN CREATOR TYPE ============
# Match the header case-insensitively ("Creator Type", "Creator type", ...)
for _c in list(df.columns):
    if _c.lower() == 'creator_type' and _c != 'Creator_Type':
        df = df.rename(columns={_c: 'Creator_Type'})

if 'Creator_Type' in df.columns:
    df['Creator_Type'] = (
        df['Creator_Type']
        .astype(str)
        .str.strip()
        .replace({'nan': np.nan, 'None': np.nan, '': np.nan})
    )


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


# ============ SIDEBAR FILTERS (MONTH + TIER + CREATOR TYPE) ============
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
    for k in ('month_filter', 'tier_filter', 'creator_filter'):
        st.session_state[k] = [SELECT_ALL]
        st.session_state[k + '_prev'] = [SELECT_ALL]


for _k in ('month_filter', 'tier_filter', 'creator_filter'):
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


    # ============ FILTER BY CREATOR TYPE ============
    if 'Creator_Type' in df.columns:

        sorted_creator_types = sorted(
            df['Creator_Type']
            .dropna()
            .unique()
            .tolist()
        )

        st.multiselect(
            "Select Creator Types",
            options=[SELECT_ALL] + sorted_creator_types,
            key='creator_filter',
            on_change=normalize_multiselect,
            args=('creator_filter', sorted_creator_types)
        )

        selected_creator_types = st.session_state['creator_filter']

        if SELECT_ALL not in selected_creator_types:
            filtered_df = filtered_df[
                filtered_df['Creator_Type'].isin(selected_creator_types)
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
def create_bar_chart(data, x_col, y_col, color=None, value_format=',.0f', y_title=None):

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
                format=value_format,
                title=y_title or y_col
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
            format=value_format
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


# ============ VIEW RATE (Views / Followers Number) ============
# Same approach as ER: sum of views / sum of followers
if (
    'Followers_Number' in filtered_df.columns
    and 'Views' in filtered_df.columns
    and filtered_df['Followers_Number'].sum() > 0
):
    view_rate = filtered_df['Views'].sum() / filtered_df['Followers_Number'].sum()
else:
    view_rate = 0


avg_cpv = (
    filtered_df['Actual_Spends_IDR'].sum() / filtered_df['Views'].sum()
    if 'Actual_Spends_IDR' in filtered_df.columns
    and 'Views' in filtered_df.columns
    and filtered_df['Views'].sum() > 0
    else 0
)


# ============ KPI METRICS ============
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


def kpi_card(label, value):
    return f"""
    <div class="kpi-card">
        <p class="kpi-label">{label}</p>
        <p class="kpi-value">{value}</p>
    </div>
    """


# ---- Row 1: Total KOLs | Total Posts ----
c1, c2 = st.columns(2)
c1.markdown(kpi_card("Total KOLs", f"{total_kols:,}"), unsafe_allow_html=True)
c2.markdown(kpi_card("Total Posts", f"{total_posts:,}"), unsafe_allow_html=True)

# ---- Row 2: Reach | Views | Engagement | Budget Spent ----
c1, c2, c3, c4 = st.columns(4)
c1.markdown(kpi_card("Reach", format_number(total_reach)), unsafe_allow_html=True)
c2.markdown(kpi_card("Views", format_number(total_views)), unsafe_allow_html=True)
c3.markdown(kpi_card("Engagement", format_number(total_engagement)), unsafe_allow_html=True)
c4.markdown(kpi_card("Budget Spent", format_currency(total_spend)), unsafe_allow_html=True)

# ---- Row 3: View Rate (%) | Engagement Rate (%) | CPV ----
c1, c2, c3 = st.columns(3)
c1.markdown(kpi_card("View Rate (%)", f"{view_rate * 100:.2f}%"), unsafe_allow_html=True)
c2.markdown(kpi_card("Engagement Rate (%)", format_percent(engagement_rate)), unsafe_allow_html=True)
c3.markdown(kpi_card("CPV", f"Rp {round(avg_cpv):,}"), unsafe_allow_html=True)


# ============ VISUALIZATIONS ============
section_header_with_divider("Monthly Performance")


# ============================================================
# SPEND BY MONTH
# ============================================================
METRIC_OPTIONS = ['Spend', 'Views', '# of KOLs', '# of Posts', 'VR', 'ER']

METRIC_TITLES = {
    'Spend': 'Spend by Month',
    'Views': 'Views by Month',
    '# of KOLs': '# of KOLs by Month',
    '# of Posts': '# of Posts by Month',
    'VR': 'View Rate (VR) by Month',
    'ER': 'Engagement Rate (ER) by Month'
}

# Count / amount metrics are drawn as grouped bars, % metrics as lines
LINE_METRICS = ['VR', 'ER']

METRIC_COLORS = {
    'Spend': NAVY,
    'Views': BLUE,
    '# of KOLs': PURPLE,
    '# of Posts': '#6fcfe0',
    'VR': MAGENTA,
    'ER': '#12a594'
}

MAX_METRICS = 3


def compute_monthly_metric(data, metric):
    """Value of the chosen metric for each Month (None if a needed column is missing).

    VR and ER are follower-weighted averages for the month
    (sum of views or engagement / sum of followers), the same formula as
    the KPI cards, so a single-month view matches the cards exactly.
    """
    g = data.groupby('Month')

    def safe_ratio(num, den):
        return (num / den).replace([np.inf, -np.inf], np.nan).fillna(0)

    if metric == 'Spend':
        if 'Actual_Spends_IDR' not in data.columns:
            return None
        return g['Actual_Spends_IDR'].sum()

    if metric == 'Views':
        if 'Views' not in data.columns:
            return None
        return g['Views'].sum()

    if metric == '# of KOLs':
        if 'KOL_Name' not in data.columns:
            return None
        key = (
            data['KOL_Name']
            .astype(str)
            .str.strip()
            .str.replace(r'\s+', ' ', regex=True)
            .str.lower()
        )
        return key.groupby(data['Month']).nunique()

    if metric == '# of Posts':
        return g.size()

    if metric == 'VR':
        if not {'Views', 'Followers_Number'}.issubset(data.columns):
            return None
        return safe_ratio(g['Views'].sum(), g['Followers_Number'].sum())

    if metric == 'ER':
        if not {'Likes', 'Comments', 'Share', 'Followers_Number'}.issubset(data.columns):
            return None
        engagement = g['Likes'].sum() + g['Comments'].sum() + g['Share'].sum()
        return safe_ratio(engagement, g['Followers_Number'].sum())

    return None


def create_multi_metric_chart(long_df, month_order, metric_order):
    """Grouped bars (counts / amounts) + lines (% metrics) in one chart.

    The y axis is hidden: each metric is drawn on its own 0-to-peak scale
    (the 'Scaled' column), and the real value is shown as a label and in
    the tooltip. This keeps metrics with very different sizes readable.
    """
    n_bars = sum(1 for m in metric_order if m not in LINE_METRICS)

    if len(metric_order) == 1:
        label_size = 13
    elif n_bars <= 2:
        label_size = 11
    else:
        label_size = 10

    color_scale = alt.Scale(
        domain=metric_order,
        range=[METRIC_COLORS[m] for m in metric_order]
    )

    x_month = alt.X(
        'Month:O',
        sort=month_order,
        axis=alt.Axis(labels=True, title=None, labelAngle=0)
    )
    y_scaled = alt.Y(
        'Scaled:Q',
        axis=None,
        scale=alt.Scale(domain=[0, 1.15])
    )
    color_legend = alt.Color(
        'Metric:N',
        scale=color_scale,
        legend=alt.Legend(
            title=None,
            orient='top',
            labelFontSize=12,
            labelFont='Poppins',
            symbolType='circle'
        )
    )
    color_plain = alt.Color('Metric:N', scale=color_scale, legend=None)
    tooltip = [
        alt.Tooltip('Month:O', title='Month'),
        alt.Tooltip('Metric:N', title='Metric'),
        alt.Tooltip('Label:N', title='Value')
    ]

    bar_df = long_df[long_df['Kind'] == 'bar']
    line_df = long_df[long_df['Kind'] == 'line']

    layers = []

    if not bar_df.empty:
        bar_metrics = [m for m in metric_order if m not in LINE_METRICS]
        offset = alt.XOffset('Metric:N', sort=bar_metrics)

        layers.append(
            alt.Chart(bar_df).mark_bar(
                cornerRadiusTopLeft=4,
                cornerRadiusTopRight=4
            ).encode(
                x=x_month,
                xOffset=offset,
                y=y_scaled,
                color=color_legend,
                tooltip=tooltip
            )
        )

        layers.append(
            alt.Chart(bar_df).mark_text(
                align='center',
                baseline='bottom',
                dy=-6,
                fontSize=label_size,
                fontWeight='bold',
                font='Poppins',
                color=NAVY
            ).encode(
                x=x_month,
                xOffset=offset,
                y=y_scaled,
                text='Label:N'
            )
        )

    if not line_df.empty:
        layers.append(
            alt.Chart(line_df).mark_line(
                strokeWidth=3,
                point=alt.OverlayMarkDef(filled=True, size=70)
            ).encode(
                x=x_month,
                y=y_scaled,
                color=color_legend,
                tooltip=tooltip
            )
        )

        layers.append(
            alt.Chart(line_df).mark_text(
                align='center',
                baseline='bottom',
                dy=-12,
                fontSize=label_size,
                fontWeight='bold',
                font='Poppins'
            ).encode(
                x=x_month,
                y=y_scaled,
                text='Label:N',
                color=color_plain
            )
        )

    return alt.layer(*layers).properties(
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


# ---- Which metrics may be combined -------------------------------------
# Metrics that share a unit share one scale, so they stay comparable:
#   money = Spend | views = Views | count = # of KOLs + # of Posts | rate = VR + ER
# A chart may hold at most ONE bar group (money / views / count) plus the
# % lines, and at most MAX_METRICS metrics in total.
METRIC_SCALE_GROUP = {
    'Spend': 'money',
    'Views': 'views',
    '# of KOLs': 'count',
    '# of Posts': 'count',
    'VR': 'rate',
    'ER': 'rate'
}


def is_valid_metric_combo(metrics):
    if len(metrics) > MAX_METRICS:
        return False

    bar_groups = {
        METRIC_SCALE_GROUP[m]
        for m in metrics
        if m not in LINE_METRICS
    }

    return len(bar_groups) <= 1


def metric_state_key(metric):
    return f"metric_cb_{METRIC_OPTIONS.index(metric)}"


# Default selection on first load: Spend only
if 'metric_defaults_set' not in st.session_state:
    for _m in METRIC_OPTIONS:
        st.session_state[metric_state_key(_m)] = (_m == 'Spend')
    st.session_state['metric_defaults_set'] = True

current_metrics = [
    m for m in METRIC_OPTIONS
    if st.session_state.get(metric_state_key(m))
]

st.markdown("**Select metrics**")
st.caption(
    "Greyed-out metrics can't be combined with your current selection "
    f"(max {MAX_METRICS})."
)

metric_cols = st.columns(len(METRIC_OPTIONS))

for _col, _m in zip(metric_cols, METRIC_OPTIONS):
    with _col:
        st.checkbox(
            _m,
            key=metric_state_key(_m),
            disabled=(
                _m not in current_metrics
                and not is_valid_metric_combo(current_metrics + [_m])
            )
        )

ordered_metrics = [
    m for m in METRIC_OPTIONS
    if st.session_state.get(metric_state_key(m))
]

if not ordered_metrics:

    st.info("Select at least one metric to display the chart.")

else:

    if len(ordered_metrics) == 1:
        chart_title = METRIC_TITLES[ordered_metrics[0]]
    else:
        chart_title = ", ".join(ordered_metrics) + " by Month"

    st.markdown(f"""
    <div style="text-align: center; font-size: 18px; font-weight: bold; color: {NAVY}; margin-bottom: 10px;">
        {chart_title}
    </div>
    """, unsafe_allow_html=True)

    series_by_metric = {}

    for metric in ordered_metrics:

        series = compute_monthly_metric(filtered_df, metric)

        if series is not None and not series.empty:
            series_by_metric[metric] = series.sort_index()

    # One peak per scale group (metrics in the same group share a scale)
    group_peak = {}

    for metric, series in series_by_metric.items():
        grp = METRIC_SCALE_GROUP[metric]
        group_peak[grp] = max(group_peak.get(grp, 0), series.max())

    frames = []
    month_dates = set()

    for metric, series in series_by_metric.items():

        month_dates.update(series.index)

        is_line = metric in LINE_METRICS
        peak = group_peak[METRIC_SCALE_GROUP[metric]]

        # Bars use up to 80% of the height and lines up to 95%, so line
        # labels are less likely to collide with bar labels.
        top = 0.95 if is_line else 0.80
        scaled = (series / peak * top) if peak and peak > 0 else series * 0

        if is_line:
            labels = series.apply(lambda v: f"{v * 100:.2f}%")
        elif len(ordered_metrics) == 1:
            labels = series.apply(lambda v: f"{v:,.0f}")
        else:
            labels = series.apply(format_number)

        frames.append(pd.DataFrame({
            'Month': series.index.strftime('%b-%y'),
            'Metric': metric,
            'Kind': 'line' if is_line else 'bar',
            'Value': series.values,
            'Scaled': scaled.values,
            'Label': labels.values
        }))

    if frames:

        long_df = pd.concat(frames, ignore_index=True)

        month_order = [
            pd.Timestamp(d).strftime('%b-%y')
            for d in sorted(month_dates)
        ]

        chart = create_multi_metric_chart(
            long_df,
            month_order,
            [m for m in ordered_metrics if m in set(long_df['Metric'])]
        )

        st.altair_chart(
            chart,
            use_container_width=True
        )

        if len(set(METRIC_SCALE_GROUP[m] for m in series_by_metric)) > 1:
            st.caption(
                "Bars and lines are drawn on separate scales, so compare bar "
                "heights with other bars and the line with its own trend. "
                "Hover for exact values."
            )

    else:

        st.info("No data available for the selected metrics")


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
                            'Followers_Number'
                        ]:

                            if col in display_kol.columns:

                                display_kol[col] = (
                                    display_kol[col]
                                    .apply(format_number)
                                )

                        # FORMAT COST (Rp prefix, like CPV)
                        if 'Actual_Spends_IDR' in display_kol.columns:

                            display_kol['Actual_Spends_IDR'] = (
                                display_kol['Actual_Spends_IDR']
                                .apply(format_currency)
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


# ============================================================
# FULL DATA TABLE
# ============================================================
section_header_with_divider("Full Data Table")

st.markdown("""
<style>
.scrollable-table {
    width: 100%;
    overflow-x: auto;
    display: block;
    margin-bottom: 10px;
    background: #ffffff;
    border: 1px solid #d9deef;
    border-radius: 12px;
}
.scrollable-table table {
    width: 100%;
    border-collapse: collapse;
    font-size: 13px;
}
.scrollable-table th, .scrollable-table td {
    padding: 9px 14px;
    border-bottom: 1px solid #d9deef;
    white-space: nowrap;
    color: #000749;
    text-align: left;
}
.scrollable-table th {
    background-color: #eef2fd;
    font-weight: 600;
    border-bottom: 2px solid #4F7FF2;
}
.scrollable-table tbody tr:hover { background: #f6f8ff; }
</style>
""", unsafe_allow_html=True)


if 'rows_to_show' not in st.session_state:
    st.session_state.rows_to_show = 10


display_full_df = filtered_df.copy()

# Drop helper / junk columns
display_full_df = display_full_df.loc[
    :,
    ~display_full_df.columns.str.startswith('Unnamed')
]
display_full_df = display_full_df.drop(
    columns=['KOL_Name_Original', 'KOL_Name_Search'],
    errors='ignore'
)

# Format numeric columns
for col in [
    'Views',
    'Reach',
    'Likes',
    'Comments',
    'Share',
    'Followers_Number'
]:
    if col in display_full_df.columns:
        display_full_df[col] = display_full_df[col].apply(format_number)

# Format cost (Rp prefix, like CPV)
if 'Actual_Spends_IDR' in display_full_df.columns:
    display_full_df['Actual_Spends_IDR'] = (
        display_full_df['Actual_Spends_IDR'].apply(format_currency)
    )

# Format percent columns (same scale handling as the KOL search table)
for col in ['ER', 'ER_Views', 'VR']:
    if col in display_full_df.columns:
        display_full_df[col] = display_full_df[col].apply(format_er_display)

# Format CPV
if 'CPV_Calculated' in display_full_df.columns:
    display_full_df['CPV_Calculated'] = (
        display_full_df['CPV_Calculated']
        .apply(format_currency_short)
    )

# Format month
if (
    'Month' in display_full_df.columns
    and pd.api.types.is_datetime64_any_dtype(display_full_df['Month'])
):
    display_full_df['Month'] = display_full_df['Month'].dt.strftime('%b-%y')

# Friendlier column headers
display_full_df = display_full_df.rename(columns={
    'KOL_Name': 'KOL Name',
    'Actual_Spends_IDR': 'Cost',
    'Followers_Number': 'Followers',
    'ER_Views': 'ER Views',
    'CPV_Calculated': 'CPV'
})


total_rows = len(display_full_df)
show_rows = min(st.session_state.rows_to_show, total_rows)
display_df_limited = display_full_df.head(show_rows)


# Scrollable table
st.markdown(
    f'<div class="scrollable-table">'
    f'{display_df_limited.to_html(escape=True, index=False, border=0)}'
    f'</div>',
    unsafe_allow_html=True
)


# Load more button
if total_rows > st.session_state.rows_to_show:
    lm1, lm2, lm3 = st.columns([1, 2, 1])

    with lm2:
        if st.button(
            f"Load More ({show_rows} of {total_rows:,} shown)",
            use_container_width=True
        ):
            st.session_state.rows_to_show += 10
            st.rerun()
else:
    st.caption(f"Showing all {total_rows:,} rows")
