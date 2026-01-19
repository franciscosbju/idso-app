import hashlib
import base64
import json
from io import BytesIO
from zipfile import ZipFile, ZIP_DEFLATED
from datetime import datetime, date

import pandas as pd
import plotly.express as px
import streamlit as st

# ======================================================
# CARREGAMENTO DA FONTE (AJUSTE NECESSÁRIO)
# ======================================================
def load_font_base64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

brighter_base64 = load_font_base64("fonts/Brighter-Regular.otf")

# ======================================================
# CONFIGURAÇÕES
# ======================================================
APP_TITLE = "Indicadores de Desempenho da Segurança Operacional – IDSO"
ACCENT = "#96CE00"  # cor institucional

st.set_page_config(page_title="IDSO • Painel", layout="wide")

# ======================================================
# CSS – LAYOUT “LIMPO” (SEM SOBRA DE SIDEBAR) + ESTILO BONITO
# ======================================================
st.markdown(
    f"""
    <style>

    /* ======================================================
       FONTE BRIGHTER (AJUSTE ÚNICO)
       ====================================================== */
    @font-face {{
        font-family: 'Brighter';
        src: url(data:font/opentype;base64,{brighter_base64}) format('opentype');
        font-weight: normal;
        font-style: normal;
    }}

    html, body, [class*="css"] {{
        font-family: 'Brighter', Arial, sans-serif !important;
    }}

    /* ======================================================
       AJUSTE DA FONTE DO FILE UPLOADER (REMOVE CURSIVA)
       ====================================================== */
    [data-testid="stFileUploader"] *,   
    [data-testid="stFileUploader"] * {{
        font-family: system-ui, -apple-system, BlinkMacSystemFont,
                    "Segoe UI", Roboto, Helvetica, Arial, sans-serif !important;
        font-style: normal !important;
        font-weight: normal !important;
    }}

    /* Remove qualquer “sobra” da sidebar */
    [data-testid="stSidebar"] {{
        display: none !important;
        width: 0 !important;
        min-width: 0 !important;
        max-width: 0 !important;
    }}
    section[data-testid="stSidebarContent"] {{
        display: none !important;
    }}

    /* Remove header/footer do Streamlit */
    header, footer {{ visibility: hidden; height: 0px; }}

    /* Ajusta container principal */
    div.block-container {{
        padding-top: 1.0rem;
        padding-left: 2.0rem;
        padding-right: 2.0rem;
        max-width: 1500px;
    }}

    /* Chips (multiselect) */
    [data-baseweb="tag"] {{
        background-color: {ACCENT} !important;
        color: #ffffff !important;
        border-radius: 999px !important;
        font-weight: 900 !important;
        border: 1px solid rgba(0,0,0,0.12) !important;
    }}
    [data-baseweb="tag"] svg {{ color: #ffffff !important; }}

    /* Cards KPI */
    .kpi-card {{
        background-color:#f2f3f5;
        padding:16px;
        border-radius:16px;
        text-align:center;
        border: 1px solid rgba(0,0,0,0.07);
        box-shadow: 0 6px 16px rgba(0,0,0,0.06);
    }}
    .kpi-title {{
        font-size:16px;
        font-weight:900;
        margin-bottom:6px;
        color:#1a2732;
    }}
    .kpi-value {{
        font-size:34px;
        font-weight:1000;
        line-height:1.1;
    }}
    .kpi-sub {{
        font-size:13px;
        margin-top:6px;
        font-weight:800;
        color:#5b6b7b;
    }}

    /* Banner estatístico */
    .stat-banner {{
        background: linear-gradient(90deg, #233243 0%, #2c3e50 55%, #233243 100%);
        color: white;
        padding: 14px 18px;
        border-radius: 16px;
        border: 1px solid rgba(255,255,255,0.10);
        margin-top: 8px;
        margin-bottom: 14px;
        box-shadow: 0 8px 18px rgba(0,0,0,0.12);
    }}
    .stat-title {{
        text-align:center;
        font-weight:1000;
        letter-spacing: 0.5px;
        margin-bottom: 10px;
        font-size: 18px;
    }}
    .stat-line {{
        text-align:center;
        font-weight:900;
        font-size: 16px;
        line-height: 1.6;
        white-space: pre-wrap;
    }}
    .up {{ color: {ACCENT}; font-weight: 1000; }}
    .down {{ color: #ff5a5f; font-weight: 1000; }}
    .flat {{ color: #d0d7de; font-weight: 1000; }}

    /* Pendências com pisca */
    @keyframes blinkRed {{
        0%   {{ box-shadow: 0 0 0 rgba(255,0,0,0.0); background:#ffe9ea; }}
        50%  {{ box-shadow: 0 0 18px rgba(255,0,0,0.35); background:#ffd6d9; }}
        100% {{ box-shadow: 0 0 0 rgba(255,0,0,0.0); background:#ffe9ea; }}
    }}
    .pending-card {{
        border-radius:16px;
        border: 1px solid rgba(155,28,28,0.20);
        padding: 12px 14px;
        animation: blinkRed 1.2s infinite;
        margin-bottom: 10px;
        box-shadow: 0 8px 18px rgba(0,0,0,0.08);
    }}

    .pending-title {{
    text-align: center;
    font-weight: 1000;
    font-size: 18px;
    color: #ff5a5f;
    margin-bottom: 6px;
    }}

    /* ======================================================
       RANKING – TOP EVENTOS POR INDICADOR (MINI CARDS)
       ====================================================== */
    .rank-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
        gap: 14px;
        margin-top: 12px;
        margin-bottom: 20px;
    }}

    .rank-card-mini {{
        background: #f8f9fb;
        border: 2px solid {ACCENT};
        border-radius: 14px;
        padding: 12px 10px;
        text-align: center;
        box-shadow: 0 4px 10px rgba(0,0,0,0.06);
    }}

    .rank-pos {{
        font-size: 11px;
        font-weight: 900;
        color: #6b7c93;
    }}

    .rank-aero {{
        font-size: 17px;
        font-weight: 1000;
        margin-top: 4px;
        color: #1a2732;
        letter-spacing: 0.4px;
    }}

    .rank-value {{
        font-size: 22px;
        font-weight: 1000;
        margin-top: 6px;
        color: #1a2732;
        line-height: 1.1;
    }}

    .rank-label {{
        font-size: 11px;
        font-weight: 900;
        color: #6b7c93;
    }}

    /* ======================================================
       🔥 INCLUSÕES — DESTAQUES DE RANKING
       ====================================================== */

    .rank-top-1 {{
        background: linear-gradient(135deg, #fff4cc, #ffe08a);
        border: 3px solid #d4af37 !important;
        box-shadow: 0 6px 20px rgba(212,175,55,0.45);
    }}

    .rank-top-3 {{
        border-width: 3px !important;
    }}

    .rank-ind-RI {{ border-color: #ff6b6b !important; }}
    .rank-ind-FOD {{ border-color: #ff9f43 !important; }}
    .rank-ind-COLISAO {{ border-color: #1dd1a1 !important; }}
    .rank-ind-FAUNA {{ border-color: #54a0ff !important; }}
    .rank-ind-OUTROS {{ border-color: #8395a7 !important; }}

    /* ======================================================
       🔰 TÍTULO PRINCIPAL DO APP (INCLUSÃO)
       ====================================================== */
    .app-title {{
        text-align: center;
        color: #96CE00;
        font-size: 40px;
        font-weight: 1000;
        margin-bottom: 6px;
    }}

    .app-subtitle {{
        text-align: center;
        color: #96CE00;
        font-size: 60px;
        font-weight: 400;
        letter-spacing: 0.6px;
        margin-top: 0px;
        margin-bottom: 24px;
        font-family: "Brighter", "Brighter Regular", Arial, sans-serif;
    }}

    /* ======================================================
   🔽 AJUSTE REAL DO TEXTO DOS EXPANDERS (FUNCIONA)
   ====================================================== */
    div[data-testid="stExpander"] div[data-testid="stMarkdownContainer"] p {{
        font-size: 18px !important;   /* 🔥 AGORA FUNCIONA */
        font-weight: 1000 !important;
        color: #1a2732 !important;
        margin: 0 !important;
    }}

    /* ======================================================
    🎯 METAS — GRID ELEGANTE (IGUAL AO RANKING)
    ====================================================== */

    .metas-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
        gap: 18px;
        margin-top: 14px;
        margin-bottom: 28px;
    }}

    .meta-card {{
        background: #f8f9fb;
        border-radius: 18px;
        padding: 18px 16px;
        border: 2px solid rgba(0,0,0,0.06);
        box-shadow: 0 6px 16px rgba(0,0,0,0.06);
        text-align: center;
        position: relative;
    }}

    .meta-title {{
        font-size: 16px;
        font-weight: 1000;
        color: #1a2732;
        margin-bottom: 6px;
    }}

    .meta-aero {{
        font-size: 12px;
        font-weight: 900;
        color: #6b7c93;
        letter-spacing: 0.3px;
        margin-bottom: 10px;
    }}

    .meta-value {{
        font-size: 40px;
        font-weight: 1000;
        line-height: 1.1;
        margin-bottom: 6px;
    }}

    .meta-sub {{
        font-size: 13px;
        font-weight: 900;
        color: #5b6b7b;
    }}

    /* Selo de status */
    .meta-badge {{
        position: absolute;
        top: 12px;
        right: 14px;
        font-size: 11px;
        font-weight: 1000;
        padding: 4px 10px;
        border-radius: 999px;
    }}

    .meta-ok {{
        background: #e8f6d8;
        color: #5ca000;
    }}

    .meta-warn {{
        background: #fff3cd;
        color: #b78103;
    }}

    .meta-bad {{
        background: #ffe2e5;
        color: #c62828;
    }}

    </style>
    """,
    unsafe_allow_html=True
)

# ======================================================
# MAPAS / CONSTANTES
# ======================================================
RENAME = {
    "AEROPORTO": "aeroporto",
    "ANO": "ano",
    "MÊS": "mes",
    "Nº DE EVENTOS": "eventos",
    "MOVIMENTAÇÃO (P + D)": "mov",
    "OrdemMes": "ordem_mes",
    "OrdemAno": "ordem_ano",
    "Indicador": "indicador",
    "Criado": "criado_em",
    "Criado por": "criado_por",
}

MESES_MAP = {
    "JANEIRO": 1, "FEVEREIRO": 2, "MARÇO": 3, "MARCO": 3, "ABRIL": 4, "MAIO": 5, "JUNHO": 6,
    "JULHO": 7, "AGOSTO": 8, "SETEMBRO": 9, "OUTUBRO": 10, "NOVEMBRO": 11, "DEZEMBRO": 12
}
MESES_ABREV = {1:"Jan",2:"Fev",3:"Mar",4:"Abr",5:"Mai",6:"Jun",7:"Jul",8:"Ago",9:"Set",10:"Out",11:"Nov",12:"Dez"}
ORDEM_MESES_ABREV = ["Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"]

# ======================================================
# FUNÇÕES UTILITÁRIAS
# ======================================================
def fmt_int(x):
    try:
        return f"{int(x):,}".replace(",", ".")
    except Exception:
        return "0"

def fmt_pct(x, digits=0):
    try:
        return f"{x*100:+.{digits}f}%"
    except Exception:
        return "—"

def card_html(titulo, valor, cor_valor="#333", subtitulo=None, icon=None):
    ic = f"{icon} " if icon else ""
    sub = f'<div class="kpi-sub">{subtitulo}</div>' if subtitulo else ""
    return f"""
    <div class="kpi-card">
        <div class="kpi-title">{ic}{titulo}</div>
        <div class="kpi-value" style="color:{cor_valor};">{valor}</div>
        {sub}
    </div>
    """

def df_to_excel_bytes(sheets: dict) -> bytes:
    out = BytesIO()
    with pd.ExcelWriter(out, engine="openpyxl") as writer:
        for name, df_ in sheets.items():
            df_.to_excel(writer, index=False, sheet_name=str(name)[:31])
    return out.getvalue()

def make_zip(files):
    bio = BytesIO()
    with ZipFile(bio, "w", compression=ZIP_DEFLATED) as zf:
        for name, content in files:
            zf.writestr(name, content)
    return bio.getvalue()

@st.cache_data(show_spinner=False)
def read_excel_and_hash(file_bytes: bytes):
    sha = hashlib.sha256(file_bytes).hexdigest()
    df = pd.read_excel(BytesIO(file_bytes))
    return df, sha

def prepare_idso(df_raw: pd.DataFrame) -> pd.DataFrame:
    df = df_raw.rename(columns=RENAME).copy()

    for c in ["aeroporto", "indicador", "mes", "ano", "eventos", "mov"]:
        if c not in df.columns:
            df[c] = pd.NA

    df["aeroporto"] = df["aeroporto"].astype(str).str.strip().str.upper()
    df["indicador"] = df["indicador"].astype(str).str.strip()
    df["mes"] = df["mes"].astype(str).str.strip()

    df["ano"] = pd.to_numeric(df["ano"], errors="coerce").astype("Int64")
    df["eventos"] = pd.to_numeric(df["eventos"], errors="coerce").fillna(0).astype(int)
    df["mov"] = pd.to_numeric(df["mov"], errors="coerce").fillna(0).astype(int)

    df["ordem_mes"] = pd.to_numeric(df.get("ordem_mes", pd.NA), errors="coerce").astype("Int64")
    mes_upper = df["mes"].astype(str).str.upper().str.strip()
    mes_from_name = mes_upper.map(MESES_MAP).astype("Int64")
    invalid = (df["ordem_mes"].isna()) | (~df["ordem_mes"].between(1, 12))
    df.loc[invalid, "ordem_mes"] = mes_from_name[invalid]

    df = df[df["ordem_mes"].between(1, 12, inclusive="both")].copy()
    df["mes_abrev"] = df["ordem_mes"].map(MESES_ABREV)

    if "criado_em" in df.columns:
        df["criado_em"] = pd.to_datetime(df["criado_em"], errors="coerce")

    df["chave"] = (
        df["aeroporto"].astype(str) + "|" +
        df["ano"].astype(str) + "|" +
        df["ordem_mes"].astype(str) + "|" +
        df["indicador"].astype(str)
    )
    return df

def apply_filters(df: pd.DataFrame, sel_aero, sel_ano, sel_ind, sel_mes_abrev):
    d = df.copy()
    if sel_aero: d = d[d["aeroporto"].isin(sel_aero)]
    if sel_ano: d = d[d["ano"].isin(sel_ano)]
    if sel_ind: d = d[d["indicador"].isin(sel_ind)]
    if sel_mes_abrev: d = d[d["mes_abrev"].isin(sel_mes_abrev)]
    return d

def prev_month(today: date):
    if today.month == 1:
        return today.year - 1, 12
    return today.year, today.month - 1

def due_date_for_period(today: date):
    return date(today.year, today.month, 10)

def period_to_int(y: int, m: int) -> int:
    return y * 100 + m

def int_to_period(p: int):
    return p // 100, p % 100

def add_months(y: int, m: int, delta: int):
    for _ in range(delta):
        m += 1
        if m == 13:
            m = 1
            y += 1
    return y, m

def calc_pending_by_airport(df_all: pd.DataFrame, today: date):
    req_y, req_m = prev_month(today)
    required = period_to_int(req_y, req_m)
    due = due_date_for_period(today)

    rows = []
    base = df_all.dropna(subset=["ano", "ordem_mes"]).copy()
    if base.empty:
        return pd.DataFrame(columns=[
            "aeroporto","required_period","required_ano","required_mes","required_mes_abrev",
            "due_date","days_from_due","is_overdue","is_ok","missing_months","last_period"
        ]), required, due

    for aero, g in base.groupby("aeroporto"):
        g = g.copy()
        g["period"] = g["ano"].astype(int) * 100 + g["ordem_mes"].astype(int)
        last_period = int(g["period"].max())
        ok = last_period >= required

        missing_months = 0
        if not ok:
            ly, lm = int_to_period(last_period)
            diff = 0
            cy, cm = ly, lm
            while period_to_int(cy, cm) < required and diff < 60:
                cy, cm = add_months(cy, cm, 1)
                diff += 1
            missing_months = diff

        days = (today - due).days
        rows.append({
            "aeroporto": aero,
            "required_period": required,
            "required_ano": req_y,
            "required_mes": req_m,
            "required_mes_abrev": MESES_ABREV.get(req_m, str(req_m)),
            "due_date": due.isoformat(),
            "days_from_due": int(days),
            "is_overdue": bool(today > due),
            "is_ok": bool(ok),
            "missing_months": int(missing_months),
            "last_period": int(last_period),
        })
    return pd.DataFrame(rows), required, due

def stat_banner_mov_years(df_f: pd.DataFrame):
    if df_f.empty:
        return ""

    # 🔹 remove duplicidade de movimentação por indicador
    base = (
        df_f
        .drop_duplicates(subset=["aeroporto", "ano", "ordem_mes"])
        .copy()
    )

    byy = (
        base
        .groupby("ano", as_index=False)["mov"]
        .sum()
        .sort_values("ano", ascending=False)
    )

    byy["prev"] = byy["mov"].shift(-1)

    parts = []
    for _, r in byy.iterrows():
        ano = int(r["ano"])
        mov = int(r["mov"])

        if pd.notna(r["prev"]) and int(r["prev"]) != 0:
            pct = (mov / int(r["prev"])) - 1
            if pct > 0:
                arrow = f'<span class="up">(+{abs(pct)*100:.0f}% ↑)</span>'
            elif pct < 0:
                arrow = f'<span class="down">(-{abs(pct)*100:.0f}% ↓)</span>'
            else:
                arrow = f'<span class="flat">(0% •)</span>'
        else:
            arrow = ""

        parts.append(f"{ano}: {fmt_int(mov)} {arrow}")

    line = " | ".join(parts)

    return f"""
    <div class="stat-banner">
        <div class="stat-title">COMPARATIVO ESTATÍSTICO – MOVIMENTAÇÕES</div>
        <div class="stat-line">{line}</div>
    </div>
    """

def stat_banner_years(df_f: pd.DataFrame):
    if df_f.empty:
        return ""
    byy = df_f.groupby("ano", as_index=False)["eventos"].sum().sort_values("ano", ascending=False)
    byy["prev"] = byy["eventos"].shift(-1)
    parts = []
    for _, r in byy.iterrows():
        ano = int(r["ano"]); ev = int(r["eventos"])
        if pd.notna(r["prev"]) and int(r["prev"]) != 0:
            pct = (ev / int(r["prev"])) - 1
            if pct > 0:
                arrow = f'<span class="up">(+{abs(pct)*100:.0f}% ↑)</span>'
            elif pct < 0:
                arrow = f'<span class="down">(-{abs(pct)*100:.0f}% ↓)</span>'
            else:
                arrow = f'<span class="flat">(0% •)</span>'
        else:
            arrow = ""
        parts.append(f"{ano}: {fmt_int(ev)} {arrow}")
    line = " | ".join(parts)
    return f"""
    <div class="stat-banner">
        <div class="stat-title">COMPARATIVO ESTATÍSTICO – EVENTOS IDSO</div>
        <div class="stat-line">{line}</div>
    </div>
    """

# ======================================================
# TÍTULO + UPLOAD
# ======================================================
title_placeholder = st.empty()
title_placeholder.markdown(
    f"""
    <h1 class='app-title'>{APP_TITLE}</h1>
    <div class='app-subtitle'>Safety Corporativo</div>
    <div class='app-sub'>Carregue um arquivo XLSX para iniciar</div>
    """,
    unsafe_allow_html=True
)

st.markdown("<div class='upload-wrap'>", unsafe_allow_html=True)

uploaded = st.file_uploader(
    "📤 Enviar arquivo IDSO (.xlsx)",
    type=["xlsx"],
    key="uploader_idso"   # 🔥 ESSENCIAL
)

st.markdown("</div>", unsafe_allow_html=True)

def load_data():

    # 🔥 CASO 1 — ARQUIVO REMOVIDO (clicou no ❌)
    if uploaded is None:

        # limpa tudo
        for k in ["ano_sel", "mes_sel", "aero_sel", "ind_sel"]:
            st.session_state[k] = ["Todos"]

        # remove hash anterior
        st.session_state.pop("file_sha", None)

        st.warning("⬆️ Envie o arquivo IDSO (.xlsx) para iniciar.")
        st.stop()

    # 🔥 CASO 2 — ARQUIVO PRESENTE
    b = uploaded.getvalue() if hasattr(uploaded, "getvalue") else uploaded.read()
    raw, sha = read_excel_and_hash(b)

    # primeiro carregamento
    if "file_sha" not in st.session_state:
        st.session_state.file_sha = sha

        # garante estado inicial limpo
        for k in ["ano_sel", "mes_sel", "aero_sel", "ind_sel"]:
            st.session_state[k] = ["Todos"]

    # trocou o arquivo
    elif st.session_state.file_sha != sha:
        st.session_state.file_sha = sha

        for k in ["ano_sel", "mes_sel", "aero_sel", "ind_sel"]:
            st.session_state[k] = ["Todos"]

        st.rerun()

    return raw, sha, uploaded.name

    st.warning("⬆️ Envie o arquivo IDSO (.xlsx) para iniciar.")
    st.stop()

raw_df, sha, source_name = load_data()
df = prepare_idso(raw_df)

today = date.today()
pend_df, required_period, due = calc_pending_by_airport(df, today)

title_placeholder.markdown(
    f"""
    <h1 class='app-title'>{APP_TITLE}</h1>
    <div class='app-subtitle'>Safety Corporativa</div>
    <div class='app-sub'>
        Fonte: <b>{source_name}</b> • Hash:
        <code style='color:{ACCENT}; font-weight:1000;'>{sha[:12]}</code>
    </div>
    """,
    unsafe_allow_html=True
)

# ======================================================
# FILTROS DE ANÁLISE – CONTROLE TOTAL (POWER BI STYLE)
# ======================================================

# ---------- opções base ----------
aero_base = sorted(df["aeroporto"].dropna().unique().tolist())

ano_base = sorted(
    [int(x) for x in df["ano"].dropna().unique().tolist()],
    reverse=True
)

ind_base = sorted(df["indicador"].dropna().unique().tolist())

mes_exist = (
    df[["ordem_mes", "mes_abrev"]]
    .dropna()
    .drop_duplicates()
    .sort_values("ordem_mes")
)

mes_base = [m for m in ORDEM_MESES_ABREV if m in mes_exist["mes_abrev"].tolist()]

# ---------- opções com "Todos" ----------
aero_opts = ["Todos"] + aero_base
ano_opts  = ["Todos"] + ano_base
mes_opts  = ["Todos"] + mes_base
ind_opts  = ["Todos"] + ind_base

# 🔥 PASSO 3 — BLINDAGEM
def sanitize_multiselect(key, options):
    current = st.session_state.get(key, [])
    if not current or any(v not in options for v in current):
        st.session_state[key] = ["Todos"]
        return
    if "Todos" in current and len(current) > 1:
        st.session_state[key] = [v for v in current if v != "Todos"]

sanitize_multiselect("ano_sel", ano_opts)
sanitize_multiselect("mes_sel", mes_opts)
sanitize_multiselect("aero_sel", aero_opts)
sanitize_multiselect("ind_sel", ind_opts)

# ---------- init session_state ----------
for k, v in {
    "ano_sel": ["Todos"],
    "mes_sel": ["Todos"],
    "aero_sel": ["Todos"],
    "ind_sel": ["Todos"],
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ======================================================
# FUNÇÕES DE NORMALIZAÇÃO (ANTI-VAZIO + ORDENAÇÃO)
# ======================================================

def normalize_ano():
    v = st.session_state.ano_sel

    # clicou no X → volta para Todos
    if not v:
        st.session_state.ano_sel = ["Todos"]
        return

    # se selecionou outro junto com Todos → remove Todos
    if "Todos" in v and len(v) > 1:
        v = [x for x in v if x != "Todos"]

    # se sobrou só Todos
    if v == ["Todos"]:
        st.session_state.ano_sel = ["Todos"]
    else:
        st.session_state.ano_sel = sorted(v, reverse=True)


def normalize_mes():
    v = st.session_state.mes_sel

    if not v:
        st.session_state.mes_sel = ["Todos"]
        return

    if "Todos" in v and len(v) > 1:
        v = [x for x in v if x != "Todos"]

    if v == ["Todos"]:
        st.session_state.mes_sel = ["Todos"]
    else:
        st.session_state.mes_sel = [m for m in ORDEM_MESES_ABREV if m in v]


def normalize_aero():
    v = st.session_state.aero_sel

    if not v:
        st.session_state.aero_sel = ["Todos"]
        return

    if "Todos" in v and len(v) > 1:
        v = [x for x in v if x != "Todos"]

    if v == ["Todos"]:
        st.session_state.aero_sel = ["Todos"]
    else:
        st.session_state.aero_sel = sorted(v)


def normalize_ind():
    v = st.session_state.ind_sel

    if not v:
        st.session_state.ind_sel = ["Todos"]
        return

    if "Todos" in v and len(v) > 1:
        v = [x for x in v if x != "Todos"]

    if v == ["Todos"]:
        st.session_state.ind_sel = ["Todos"]
    else:
        st.session_state.ind_sel = sorted(v)

# ======================================================
# UI
# ======================================================

st.markdown("## 🎛️ Filtros de Análise")

st.multiselect(
    "📅 Ano",
    options=ano_opts,
    key="ano_sel",
    on_change=normalize_ano
)

st.multiselect(
    "🗓️ Mês",
    options=mes_opts,
    key="mes_sel",
    on_change=normalize_mes
)

st.multiselect(
    "🛫 Aeroporto",
    options=aero_opts,
    key="aero_sel",
    on_change=normalize_aero
)

st.multiselect(
    "📌 Indicador",
    options=ind_opts,
    key="ind_sel",
    on_change=normalize_ind
)

st.markdown("---")

# ======================================================
# APLICA FILTROS (REMOVE "TODOS")
# ======================================================

sel_ano  = ano_base  if st.session_state.ano_sel  == ["Todos"] else st.session_state.ano_sel
sel_mes  = mes_base  if st.session_state.mes_sel  == ["Todos"] else st.session_state.mes_sel
sel_aero = aero_base if st.session_state.aero_sel == ["Todos"] else st.session_state.aero_sel
sel_ind  = ind_base  if st.session_state.ind_sel  == ["Todos"] else st.session_state.ind_sel

df_f = apply_filters(
    df,
    sel_aero,
    sel_ano,
    sel_ind,
    sel_mes
)

# ======================================================
# KPIs + BASE MENSAL
# ======================================================
total_rows = len(df_f)
total_eventos = int(df_f["eventos"].sum()) if total_rows else 0

mov_month = df_f.groupby(["aeroporto","ano","ordem_mes"], as_index=False)["mov"].max() if total_rows else pd.DataFrame(columns=["mov"])
total_mov = int(mov_month["mov"].sum()) if len(mov_month) else 0

indicadores_ativos = int(df_f["indicador"].nunique()) if total_rows else 0
aero_ativos = int(df_f["aeroporto"].nunique()) if total_rows else 0

monthly = (
    df_f.groupby(["aeroporto","ano","ordem_mes","mes_abrev"], as_index=False)
    .agg(eventos=("eventos","sum"), mov=("mov","max"))
    .sort_values(["aeroporto","ordem_mes","ano"])
) if total_rows else pd.DataFrame(columns=["aeroporto","ano","ordem_mes","mes_abrev","eventos","mov"])

c1, c2, c3, c4 = st.columns(4)
with c1: st.markdown(card_html("Aeroportos", fmt_int(aero_ativos), icon="🛫"), unsafe_allow_html=True)
with c2: st.markdown(card_html("Indicadores", fmt_int(indicadores_ativos), icon="📌"), unsafe_allow_html=True)
with c3: st.markdown(card_html("Eventos", fmt_int(total_eventos), icon="🚩"), unsafe_allow_html=True)
with c4:
    st.markdown(card_html("Movimentações", fmt_int(total_mov), icon="🧮", cor_valor=ACCENT, subtitulo="(soma mensal por aeroporto)"), unsafe_allow_html=True)

st.markdown(stat_banner_mov_years(df_f), unsafe_allow_html=True)
st.markdown(stat_banner_years(df_f), unsafe_allow_html=True)

# ======================================================
# TABS
# ======================================================
tab1, tab2, tab4, tab3 = st.tabs(["⏱️ Pendências IDSO", "📊 Análises & Gráficos", "📋 Comparativos & Metas", "📦 Exportações"])

with tab1:
    st.markdown("### ⏱️ Pendências de lançamento do IDSO (prazo: dia 10)")
    st.caption("Período exigido = mês anterior ao mês atual. Prazo = dia 10 do mês atual.")

    pend_view = pend_df[pend_df["aeroporto"].isin(sel_aero)].copy() if not pend_df.empty else pend_df.copy()
    pend_only = pend_view[pend_view["is_ok"] == False].sort_values(["missing_months","aeroporto"], ascending=[False, True]) if not pend_view.empty else pend_view

    a, b, c = st.columns(3)
    req_month = int(str(required_period)[-2:])
    req_year = int(str(required_period)[:4])

    with a:
        st.markdown(
            card_html(
                "Aeroportos pendentes",
                fmt_int(len(pend_only)),
                cor_valor=("#ff5a5f" if len(pend_only) else ACCENT),
                icon="🔴",
                subtitulo=f"Período exigido: {MESES_ABREV.get(req_month,str(req_month))}/{req_year}"
            ),
            unsafe_allow_html=True
        )
    with b: st.markdown(card_html("Data de hoje", today.strftime("%d/%m/%Y"), icon="📅"), unsafe_allow_html=True)
    with c: st.markdown(card_html("Prazo", due.strftime("%d/%m/%Y"), icon="⏳"), unsafe_allow_html=True)

    st.markdown("---")

    if pend_only.empty:
        st.success("✅ Nenhum aeroporto pendente no momento (com os filtros atuais).")
    else:
        cols = st.columns(3)
        i = 0
        for _, r in pend_only.iterrows():
            aero = r["aeroporto"]
            req_txt = f"{r['required_mes_abrev']}/{r['required_ano']}"
            missing = int(r["missing_months"]) if int(r["missing_months"]) else 1

            if r["is_overdue"]:
                atraso = int(r["days_from_due"])
                days_txt = f"⏱️ Atraso: <b>{atraso} dia(s)</b>"
                badge = '<span class="badge red">PENDENTE</span>'
            else:
                faltam = abs(int(r["days_from_due"]))
                days_txt = f"⏱️ Vence em: <b>{faltam} dia(s)</b>"
                badge = '<span class="badge red">PRAZO ABERTO</span>'

            more = f"• Meses em atraso: <b>{missing}</b>" if missing > 1 else "• Aguardando registro do período exigido"
            html = f"""
            <div class="pending-card">
              <div class="pending-title">{aero}</div>
              <div style="text-align:center;">{badge}</div>
              <div class="pending-sub">Período exigido: <b>{req_txt}</b></div>
              <div class="pending-days">{days_txt}<br/>{more}</div>
            </div>
            """
            with cols[i % 3]:
                st.markdown(html, unsafe_allow_html=True)
            i += 1

with tab2:
    st.markdown("### 📊 Análises & Gráficos")
    st.caption("Use os filtros para mudar o recorte. Sem tabelas na tela.")

    if df_f.empty:
        st.info("Sem dados com os filtros atuais.")
    else:
        m = monthly.copy()
        m["mes_abrev"] = pd.Categorical(
            m["mes_abrev"],
            categories=ORDEM_MESES_ABREV,
            ordered=True
        )
        m = m.sort_values(["aeroporto", "ano", "mes_abrev"])

        # ------------------------------------------------------
        # 1) Séries de Eventos por Mês (por ano) — LINHA
        # ------------------------------------------------------
        st.markdown("#### 1) Eventos por mês (por ano)")

        ser = (
            df_f
            .groupby(["ano", "ordem_mes", "mes_abrev"], as_index=False)["eventos"]
            .sum()
            .sort_values(["ano", "ordem_mes"])
        )
        ser["mes_abrev"] = pd.Categorical(
            ser["mes_abrev"],
            categories=ORDEM_MESES_ABREV,
            ordered=True
        )

        # ----- cores dinâmicas por ANO -----
        anos_disp = sorted(ser["ano"].unique().tolist())

        if "color_map_anos" not in st.session_state:
            base_colors = [
                "#1f77b4",
                "#ff7f0e",
                "#2ca02c",
                "#d62728",
                "#9467bd",
                "#17becf"
            ]
            st.session_state.color_map_anos = {
                ano: base_colors[i % len(base_colors)]
                for i, ano in enumerate(anos_disp)
            }

        with st.expander("🎨 Ajustar cores das linhas (anos)", expanded=False):
            cols = st.columns(3)
            for i, ano in enumerate(anos_disp):
                with cols[i % 3]:
                    st.session_state.color_map_anos[ano] = st.color_picker(
                        label=f"Ano {ano}",
                        value=st.session_state.color_map_anos[ano],
                        key=f"color_ano_{ano}"
                    )

        titulo_ind = (
        "Todos os Indicadores"
        if st.session_state.ind_sel == ["Todos"]
        else ", ".join(st.session_state.ind_sel)
        )

        fig1 = px.line(
            ser,
            x="mes_abrev",
            y="eventos",
            color="ano",
            markers=True,
            text=ser["eventos"].map(fmt_int),
            color_discrete_map=st.session_state.color_map_anos
        )

        fig1.update_traces(
            textposition="top center",
            marker=dict(size=10),
            line=dict(width=3),
            textfont=dict(
                color="#1A1A1A",
                size=14,
                family="Arial Black"
            )
        )

        fig1.update_layout(
            title=titulo_ind,
            xaxis_title=None,
            yaxis_title=None,
            legend_title_text=None,
            xaxis=dict(showgrid=False, zeroline=False),
            yaxis=dict(showgrid=False, zeroline=False),
            margin=dict(l=10, r=10, t=55, b=10),
        )

        st.plotly_chart(fig1, use_container_width=True)

        # ------------------------------------------------------
        # 2) Participação por indicador
        # ------------------------------------------------------
        st.markdown("#### 2) Participação por indicador")

        ind_sum = (
            df_f
            .groupby("indicador", as_index=False)["eventos"]
            .sum()
            .sort_values("eventos", ascending=False)
            .head(12)
        )

        # quebra de texto para rótulos longos
        def quebra_texto(s, max_len=18):
            palavras = s.split()
            linhas = []
            atual = ""
            for p in palavras:
                if len(atual) + len(p) <= max_len:
                    atual = (atual + " " + p).strip()
                else:
                    linhas.append(atual)
                    atual = p
            if atual:
                linhas.append(atual)
            return "<br>".join(linhas)

        ind_sum["indicador_fmt"] = ind_sum["indicador"].apply(quebra_texto)

        # -----------------------------
        # controle de largura dinâmica
        # -----------------------------
        n_barras = len(ind_sum)
        bar_width = 0.6 if n_barras > 1 else 0.35  # ← ocupa mais espaço quando só 1

        # -----------------------------
        # lógica de rótulo interno/externo
        # -----------------------------
        max_val = ind_sum["eventos"].max()

        def label_position(v):
            return "inside" if v >= max_val * 0.25 else "outside"

        def label_color(v):
            return "white" if v >= max_val * 0.25 else "#333"

        ind_sum["label_pos"] = ind_sum["eventos"].apply(label_position)
        ind_sum["label_color"] = ind_sum["eventos"].apply(label_color)

        fig2 = px.bar(
            ind_sum,
            x="indicador_fmt",
            y="eventos",
            text=ind_sum["eventos"].map(fmt_int),
        )

        fig2.update_traces(
            marker_color=ACCENT,
            width=bar_width,
            textfont=dict(
                size=14,
                family="Arial Black"
            )
        )

        # aplica posição e cor manualmente (100% confiável)
        for i, row in ind_sum.iterrows():
            fig2.data[0].textposition = ind_sum["label_pos"].tolist()
            fig2.data[0].textfont.color = ind_sum["label_color"].tolist()

        fig2.update_layout(
            xaxis_title=None,
            yaxis_title=None,
            showlegend=False,
            xaxis=dict(
                showgrid=False,
                zeroline=False,
                tickangle=0,
                tickfont=dict(size=12)
            ),
            yaxis=dict(
                showgrid=False,
                zeroline=False
            ),
            margin=dict(l=10, r=10, t=20, b=40)
        )

        st.plotly_chart(fig2, use_container_width=True)

        # ------------------------------------------------------
        # 3) Total de eventos por ano (barras verdes + rótulo branco)
        # ------------------------------------------------------
        st.markdown("#### 3) Total de eventos por ano")

        byy = (
            df_f
            .groupby("ano", as_index=False)["eventos"]
            .sum()
            .sort_values("ano", ascending=False)  # ← ORDEM 2025 → 2020
        )

        byy["ano"] = byy["ano"].astype(int)

        fig3 = px.bar(
            byy,
            x="ano",
            y="eventos",
            text=byy["eventos"].map(fmt_int)
        )

        fig3.update_traces(
            marker_color=ACCENT,
            textposition="inside",
            textfont=dict(color="white", size=18, family="Arial Black"),
        )

        fig3.update_layout(
            xaxis_title=None,
            yaxis_title=None,
            showlegend=False,
            xaxis=dict(
                type="category",
                categoryorder="array",                # ← força ordem manual
                categoryarray=byy["ano"].tolist(),    # ← exatamente como o dataframe
                showgrid=False,
                zeroline=False,
            ),
            yaxis=dict(showgrid=False, zeroline=False),
            margin=dict(l=10, r=10, t=15, b=10),
        )

        st.plotly_chart(fig3, use_container_width=True)

        # ======================================================
        # FUNÇÃO AUXILIAR – CLASSE CSS POR INDICADOR
        # ======================================================
        def classe_indicador(nome):
            nome = nome.upper()
            if "RI" in nome:
                return "rank-ind-RI"
            if "FOD" in nome:
                return "rank-ind-FOD"
            if "COL" in nome:
                return "rank-ind-COLISAO"
            if "FAUNA" in nome:
                return "rank-ind-FAUNA"
            return "rank-ind-OUTROS"

        # ------------------------------------------------------
        # 4) Top eventos por indicador (ranking por aeroporto)
        # ------------------------------------------------------
        st.markdown("#### 4) Top eventos por indicador (ranking por aeroporto)")

        # 🔀 Seletor do modo de ranking
        modo_rank = st.radio(
            "🔀 Modo de Ranking",
            options=["Indicador por Eventos", "Indicador por Índice"],
            horizontal=True,
            index=0
        )

        # ==============================
        # ORDEM FIXA DOS INDICADORES
        # ==============================
        ordem_fixa_indicadores = [
            "Incursão em Pista",
            "Colisões Entre Aeronaves e Veículos, Equipamentos, Estrutura",
            "Colisão entre Veículos, Equipamentos, Estruturas",
            "F.O.D",
            "Colisão com Aves",
            "Excursão de Pista",
            "RELPREV",
        ]

        # ==============================
        # BASE DE CÁLCULO DO RANKING
        # ==============================
        if modo_rank == "Indicador por Eventos":

            rank_df = (
                df_f
                .groupby(["indicador", "aeroporto"], as_index=False)["eventos"]
                .sum()
            )

            rank_df["valor_rank"] = rank_df["eventos"]

        else:
            base_idx = (
                df_f
                .groupby(["indicador", "aeroporto", "ano", "ordem_mes"], as_index=False)
                .agg(
                    eventos=("eventos", "sum"),
                    mov=("mov", "max")
                )
            )

            rank_df = (
                base_idx
                .groupby(["indicador", "aeroporto"], as_index=False)
                .agg(
                    eventos=("eventos", "sum"),
                    mov=("mov", "sum")
                )
            )

            rank_df["valor_rank"] = (
                rank_df["eventos"] * 100 / rank_df["mov"]
            ).fillna(0)

        # ==============================
        # EXIBIÇÃO
        # ==============================
        if rank_df.empty:
            st.info("Nenhum dado disponível para o ranking.")
        else:
            # 🔒 garante somente indicadores existentes, mantendo a ordem fixa
            indicadores_ordem = [
                i for i in ordem_fixa_indicadores
                if i in rank_df["indicador"].unique()
            ]

            for indicador in indicadores_ordem:

                sub = (
                    rank_df[rank_df["indicador"] == indicador]
                    .sort_values("valor_rank", ascending=False)
                    .head(17)
                    .reset_index(drop=True)
                )

                classe_ind = classe_indicador(indicador)

                with st.expander(f"📌 {indicador}", expanded=False):

                    html_cards = '<div class="rank-grid">'

                    for pos, row in sub.iterrows():

                        classes = ["rank-card-mini", classe_ind]

                        if pos == 0:
                            classes.append("rank-top-1")
                        elif pos in [1, 2]:
                            classes.append("rank-top-3")

                        if modo_rank == "Indicador por Eventos":
                            valor_html = f"""
                                <div class="rank-value">{fmt_int(row["eventos"])}</div>
                                <div class="rank-label">eventos</div>
                            """
                        else:
                            valor_fmt = f"{row['valor_rank']:.4f}".replace(".", ",")
                            valor_html = f"""
                                <div class="rank-value">{valor_fmt}</div>
                                <div class="rank-label">índice</div>
                            """

                        html_cards += (
                            f'<div class="{" ".join(classes)}">'
                            f'<div class="rank-pos">#{pos + 1}</div>'
                            f'<div class="rank-aero">{row["aeroporto"]}</div>'
                            f'{valor_html}'
                            '</div>'
                        )

                    html_cards += "</div>"

                    st.markdown(html_cards, unsafe_allow_html=True)

        # ------------------------------------------------------
        # 5) Gráfico por Indicador
        # ------------------------------------------------------

        def label_filtro(ano_sel, mes_sel):
            # ANO
            if ano_sel == ["Todos"]:
                ano_txt = "ANO TODOS"
            else:
                ano_txt = "Ano " + ", ".join(map(str, ano_sel))

            # MÊS
            if mes_sel == ["Todos"]:
                mes_txt = "MÊS TODOS"
            else:
                mes_txt = "Mês " + ", ".join(mes_sel)

            return f"{ano_txt} – {mes_txt}"
        
        # 🔤 monta texto de ANO / MÊS selecionados
        titulo_filtros = label_filtro(
            st.session_state.ano_sel,
            st.session_state.mes_sel
        )

        if modo_rank == "Indicador por Eventos":

            st.markdown(
                f"#### Gráfico de Eventos por Indicador — {titulo_filtros}"
            )

            for indicador in indicadores_ordem:

                sub_evt = (
                    df_f[df_f["indicador"] == indicador]
                    .groupby("aeroporto", as_index=False)
                    .agg(
                        eventos=("eventos", "sum"),
                        mov=("mov", "sum")
                    )
                    .sort_values("aeroporto")  # 🔠 ordem alfabética
                    .reset_index(drop=True)
                )

                if sub_evt.empty:
                    continue

                # 🔤 eixo X com aeroporto + movimentação
                sub_evt["label_x"] = (
                    sub_evt["aeroporto"]
                    + "<br><span style='font-size:11px'>"
                    + sub_evt["mov"].map(fmt_int)
                    + "</span>"
                )

                with st.expander(f"📌 {indicador}", expanded=True):

                    fig_evt = px.bar(
                        sub_evt,
                        x="label_x",
                        y="eventos",
                        text=sub_evt["eventos"].map(fmt_int),
                    )

                    # 🔧 limite superior com folga (EVITA CORTE)
                    y_max = sub_evt["eventos"].max()
                    y_lim = y_max * 1.25 if y_max > 0 else 1

                    fig_evt.update_traces(
                        marker_color="#96CE00",
                        textposition="outside",
                        cliponaxis=False,
                        textfont=dict(
                            color="#000000",
                            size=13,
                            family="Arial Black"
                        )
                    )

                    fig_evt.update_layout(
                        showlegend=False,

                        xaxis_title=None,
                        yaxis_title=None,

                        xaxis=dict(
                            showgrid=False,
                            zeroline=False,
                            tickfont=dict(
                                color="#000000",
                                size=13,
                                family="Arial Black"
                            )
                        ),
                        yaxis=dict(
                            showgrid=False,
                            zeroline=False,
                            range=[0, y_lim],
                            tickfont=dict(
                                color="#000000",
                                size=13,
                                family="Arial Black"
                            )
                        ),

                        uniformtext_minsize=12,
                        uniformtext_mode="show",

                        margin=dict(
                            l=40,
                            r=30,
                            t=80,
                            b=100
                        ),
                        height=420,
                    )

                    st.plotly_chart(
                        fig_evt,
                        use_container_width=True,
                        key=f"evt_{modo_rank}_{indicador}"
                    )
        # ------------------------------------------------------
        # 5) Gráfico de Índice por Indicador (LINHA)
        # ------------------------------------------------------
        elif modo_rank == "Indicador por Índice":

            st.markdown(
                f"#### 5) Gráfico de Índice por Indicador — {titulo_filtros}"
            )

            for indicador in indicadores_ordem:

                sub = (
                    rank_df[rank_df["indicador"] == indicador]
                    .sort_values("aeroporto")
                    .reset_index(drop=True)
                )

                if sub.empty:
                    continue

                # 🔥 VERIFICA SE TODOS OS VALORES SÃO ZERO
                todos_zero = (sub["valor_rank"].abs().sum() == 0)

                with st.expander(f"📌 {indicador}", expanded=True):

                    fig_idx = px.line(
                        sub,
                        x="aeroporto",
                        y="valor_rank",
                        markers=True,
                        text=sub["valor_rank"].apply(
                            lambda x: f"{x:.3f}".replace(".", ",")
                        ),
                    )

                    fig_idx.update_traces(
                        textposition="top center",
                        marker=dict(size=10),
                        line=dict(width=3, color="#96CE00"),
                        textfont=dict(
                            color="#000000",
                            size=13,
                            family="Arial Black"
                        )
                    )

                    fig_idx.update_layout(
                        xaxis_title=None,
                        yaxis_title=None,
                        showlegend=False,

                        xaxis=dict(
                            showgrid=False,
                            zeroline=False,
                            tickfont=dict(
                                color="#000000",
                                size=13,
                                family="Arial Black"
                            )
                        ),

                        yaxis=dict(
                            showgrid=False,
                            zeroline=False,

                            # 🔥 SE TUDO FOR ZERO → MOSTRA SÓ O 0
                            tickmode="array" if todos_zero else "auto",
                            tickvals=[0] if todos_zero else None,
                            range=[-0.05, 0.05] if todos_zero else None,

                            tickfont=dict(
                                color="#000000",
                                size=13,
                                family="Arial Black"
                            )
                        ),

                        margin=dict(l=40, r=30, t=30, b=60),
                        height=420,
                    )

                    st.plotly_chart(
                        fig_idx,
                        use_container_width=True,
                        key=f"graf_idx_{modo_rank}_{indicador}"
                    )

with tab4:
    st.markdown("### 📋 Comparativos & Metas")
    st.caption("Painel consolidado e comparativo entre aeroportos. Use os filtros globais para definir o recorte (Ano/Mês/Indicador).")

    if df_f.empty:
        st.info("Sem dados com os filtros atuais.")
    else:
        # ------------------------------------------------------
        # 5) Comparativo de Aeroportos (Eventos x Índice)
        # ------------------------------------------------------
        st.markdown("#### 5) Comparativo de Aeroportos")

        # 🔀 Modo de comparação
        modo_cmp = st.radio(
            "🔀 Modo de Comparação",
            options=["Comparar por Eventos", "Comparar por Índice"],
            horizontal=True,
            index=0,
            key="modo_cmp_tab5"
        )

        comp_aero_opts = sorted(df["aeroporto"].dropna().unique().tolist())

        if len(comp_aero_opts) >= 2:

            ca1, ca2 = st.columns(2)
            with ca1:
                aero_a = st.selectbox(
                    "Aeroporto A",
                    options=comp_aero_opts,
                    index=0,
                    key="cmp_aero_a_tab5"
                )
            with ca2:
                idx_b = 1 if comp_aero_opts[0] != comp_aero_opts[1] else 0
                aero_b = st.selectbox(
                    "Aeroporto B",
                    options=comp_aero_opts,
                    index=idx_b,
                    key="cmp_aero_b_tab5"
                )

            base_cmp = df.copy()
            if sel_ano:
                base_cmp = base_cmp[base_cmp["ano"].isin(sel_ano)]
            if sel_mes:
                base_cmp = base_cmp[base_cmp["mes_abrev"].isin(sel_mes)]
            if sel_ind:
                base_cmp = base_cmp[base_cmp["indicador"].isin(sel_ind)]

            # ======================================================
            # BASE POR EVENTOS
            # ======================================================
            if modo_cmp == "Comparar por Eventos":

                cmp = (
                    base_cmp[base_cmp["aeroporto"].isin([aero_a, aero_b])]
                    .groupby(["aeroporto", "ordem_mes", "mes_abrev"], as_index=False)["eventos"]
                    .sum()
                )

                cmp["valor"] = cmp["eventos"]
                eixo_y = "valor"
                label_y = "eventos"
                texto = cmp["valor"].map(fmt_int)

            # ======================================================
            # BASE POR ÍNDICE (EVENTOS * 100 / MOV)
            # ======================================================
            else:
                base_idx = (
                    base_cmp[base_cmp["aeroporto"].isin([aero_a, aero_b])]
                    .groupby(["aeroporto", "ordem_mes", "mes_abrev", "ano"], as_index=False)
                    .agg(
                        eventos=("eventos", "sum"),
                        mov=("mov", "max")
                    )
                )

                cmp = (
                    base_idx
                    .groupby(["aeroporto", "ordem_mes", "mes_abrev"], as_index=False)
                    .agg(
                        eventos=("eventos", "sum"),
                        mov=("mov", "sum")
                    )
                )

                cmp["valor"] = (cmp["eventos"] * 100 / cmp["mov"]).fillna(0)
                eixo_y = "valor"
                label_y = "índice"
                texto = cmp["valor"].apply(lambda x: f"{x:.3f}".replace(".", ","))

            # ======================================================
            # ORDENAÇÃO DE MESES
            # ======================================================
            cmp["mes_abrev"] = pd.Categorical(
                cmp["mes_abrev"],
                categories=ORDEM_MESES_ABREV,
                ordered=True
            )
            cmp = cmp.sort_values(["ordem_mes", "aeroporto"])

            # ======================================================
            # GRÁFICO
            # ======================================================
            color_map = {aero_a: ACCENT, aero_b: "#2BB7FF"}

            fig_cmp = px.bar(
                cmp,
                x="mes_abrev",
                y=eixo_y,
                color="aeroporto",
                text=texto,
                color_discrete_map=color_map,
            )

            # 🔹 lógica de rótulos
            for trace in fig_cmp.data:
                valores = list(trace.y)
                max_val = max(valores) if valores else 0

                pos, cor = [], []
                for v in valores:
                    if v >= max_val * 0.25:
                        pos.append("inside")
                        cor.append("white")
                    else:
                        pos.append("outside")
                        cor.append("#333")

                trace.textposition = pos
                trace.textangle = 0              # 🔥 força horizontal
                trace.textfont = dict(
                    color=cor,
                    size=11,                     # 🔽 menor (ajuste se quiser)
                    family="Arial Black"
                )

            fig_cmp.update_layout(
                barmode="group",
                xaxis_title=None,
                yaxis_title=None,
                legend_title_text=None,
                xaxis=dict(showgrid=False, zeroline=False),
                yaxis=dict(showgrid=False, zeroline=False),
                margin=dict(l=10, r=10, t=15, b=10),
            )

            st.plotly_chart(
                fig_cmp,
                use_container_width=True,
                key=f"cmp_{modo_cmp}_{aero_a}_{aero_b}"
            )

            # ======================================================
            # KPIs
            # ======================================================
            total_a = cmp.loc[cmp["aeroporto"] == aero_a, "valor"].sum()
            total_b = cmp.loc[cmp["aeroporto"] == aero_b, "valor"].sum()

            pct_var = (total_a - total_b) / total_b if total_b > 0 else 0

            def fmt_pct_cmp(v):
                return f"{v*100:+.2f}%".replace(".", ",")

            def fmt_val(v):
                if modo_cmp == "Comparar por Eventos":
                    return fmt_int(v)
                else:
                    return f"{v:.3f}".replace(".", ",")

            cor_a = color_map.get(aero_a, "#1a2732")
            cor_b = color_map.get(aero_b, "#1a2732")

            k1, k2, k3 = st.columns(3)

            with k1:
                st.markdown(
                    f"""
                    <div class="kpi-card">
                        <div class="kpi-title" style="color:{cor_a};">{aero_a}</div>
                        <div class="kpi-value" style="color:{cor_a};">{fmt_val(total_a)}</div>
                        <div class="kpi-sub">{label_y}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            with k2:
                cor_var = "up" if pct_var > 0 else "down" if pct_var < 0 else "flat"
                st.markdown(
                    f"""
                    <div class="kpi-card">
                        <div class="kpi-title">Variação A × B</div>
                        <div class="kpi-value {cor_var}">{fmt_pct_cmp(pct_var)}</div>
                        <div class="kpi-sub">{aero_a} vs {aero_b}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            with k3:
                st.markdown(
                    f"""
                    <div class="kpi-card">
                        <div class="kpi-title" style="color:{cor_b};">{aero_b}</div>
                        <div class="kpi-value" style="color:{cor_b};">{fmt_val(total_b)}</div>
                        <div class="kpi-sub">{label_y}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            # ⬅️ AQUI O BLOCO ACABOU (coluna 0)

            st.markdown("---")
            st.markdown("### 🎯 6) Acompanhamento de Metas")

            METAS = {
                "SBJU": {
                "Incursão em Pista": 3,
                "Excursão de Pista": 1,
                "Colisões Entre Aeronaves e Veículos, Equipamentos, Estrutura": 2,
                "Colisão entre Veículos, Equipamentos, Estruturas": 5,
                "F.O.D": 7,
                "Colisão com Aves": 40,
                "RELPREV": 15,
            },

            "SBCG": {
                "Incursão em Pista": 4,
                "Excursão de Pista": 1,
                "Colisões Entre Aeronaves e Veículos, Equipamentos, Estrutura": 3,
                "Colisão entre Veículos, Equipamentos, Estruturas": 5,
                "F.O.D": 10,
                "Colisão com Aves": 50,
                "RELPREV": 30,
            },

            "SBCJ": {
                "Incursão em Pista": 2,
                "Excursão de Pista": 1,
                "Colisões Entre Aeronaves e Veículos, Equipamentos, Estrutura": 1,
                "Colisão entre Veículos, Equipamentos, Estruturas": 3,
                "F.O.D": 10,
                "Colisão com Aves": 30,
                "RELPREV": 20,
            },

            "SBCR": {
                "Incursão em Pista": 2,
                "Excursão de Pista": 1,
                "Colisões Entre Aeronaves e Veículos, Equipamentos, Estrutura": 1,
                "Colisão entre Veículos, Equipamentos, Estruturas": 3,
                "F.O.D": 10,
                "Colisão com Aves": 30,
                "RELPREV": 20,
            },

            "SBHT": {
                "Incursão em Pista": 2,
                "Excursão de Pista": 1,
                "Colisões Entre Aeronaves e Veículos, Equipamentos, Estrutura": 1,
                "Colisão entre Veículos, Equipamentos, Estruturas": 3,
                "F.O.D": 10,
                "Colisão com Aves": 25,
                "RELPREV": 20,
            },

            "SBJP": {
                "Incursão em Pista": 5,
                "Excursão de Pista": 1,
                "Colisões Entre Aeronaves e Veículos, Equipamentos, Estrutura": 3,
                "Colisão entre Veículos, Equipamentos, Estruturas": 5,
                "F.O.D": 10,
                "Colisão com Aves": 50,
                "RELPREV": 35,
            },

            "SBKG": {
                "Incursão em Pista": 3,
                "Excursão de Pista": 1,
                "Colisões Entre Aeronaves e Veículos, Equipamentos, Estrutura": 2,
                "Colisão entre Veículos, Equipamentos, Estruturas": 5,
                "F.O.D": 5,
                "Colisão com Aves": 30,
                "RELPREV": 15,
            },

            "SBMA": {
                "Incursão em Pista": 3,
                "Excursão de Pista": 1,
                "Colisões Entre Aeronaves e Veículos, Equipamentos, Estrutura": 3,
                "Colisão entre Veículos, Equipamentos, Estruturas": 5,
                "F.O.D": 10,
                "Colisão com Aves": 30,
                "RELPREV": 20,
            },

            "SBMK": {
                "Incursão em Pista": 3,
                "Excursão de Pista": 1,
                "Colisões Entre Aeronaves e Veículos, Equipamentos, Estrutura": 3,
                "Colisão entre Veículos, Equipamentos, Estruturas": 5,
                "F.O.D": 10,
                "Colisão com Aves": 30,
                "RELPREV": 20,
            },

            "SBMO": {
                "Incursão em Pista": 5,
                "Excursão de Pista": 0,
                "Colisões Entre Aeronaves e Veículos, Equipamentos, Estrutura": 2,
                "Colisão entre Veículos, Equipamentos, Estruturas": 3,
                "F.O.D": 8,
                "Colisão com Aves": 50,
                "RELPREV": 55,
            },

            "SBPP": {
                "Incursão em Pista": 2,
                "Excursão de Pista": 1,
                "Colisões Entre Aeronaves e Veículos, Equipamentos, Estrutura": 1,
                "Colisão entre Veículos, Equipamentos, Estruturas": 3,
                "F.O.D": 10,
                "Colisão com Aves": 30,
                "RELPREV": 20,
            },

            "SBRF": {
                "Incursão em Pista": 7,
                "Excursão de Pista": 1,
                "Colisões Entre Aeronaves e Veículos, Equipamentos, Estrutura": 5,
                "Colisão entre Veículos, Equipamentos, Estruturas": 12,
                "F.O.D": 15,
                "Colisão com Aves": 144,
                "RELPREV": 150,
            },

            "SBSN": {
                "Incursão em Pista": 3,
                "Excursão de Pista": 1,
                "Colisões Entre Aeronaves e Veículos, Equipamentos, Estrutura": 3,
                "Colisão entre Veículos, Equipamentos, Estruturas": 5,
                "F.O.D": 10,
                "Colisão com Aves": 30,
                "RELPREV": 31,
            },

            "SBSP": {
                "Incursão em Pista": 4,
                "Excursão de Pista": 1,
                "Colisões Entre Aeronaves e Veículos, Equipamentos, Estrutura": 6,
                "Colisão entre Veículos, Equipamentos, Estruturas": 50,
                "F.O.D": 67,
                "Colisão com Aves": 52,
                "RELPREV": 300,
            },

            "SBUL": {
                "Incursão em Pista": 4,
                "Excursão de Pista": 1,
                "Colisões Entre Aeronaves e Veículos, Equipamentos, Estrutura": 3,
                "Colisão entre Veículos, Equipamentos, Estruturas": 5,
                "F.O.D": 10,
                "Colisão com Aves": 50,
                "RELPREV": 30,
            },

            "SBUR": {
                "Incursão em Pista": 2,
                "Excursão de Pista": 1,
                "Colisões Entre Aeronaves e Veículos, Equipamentos, Estrutura": 1,
                "Colisão entre Veículos, Equipamentos, Estruturas": 3,
                "F.O.D": 10,
                "Colisão com Aves": 30,
                "RELPREV": 20,
            },

            "SBAR": {
                "Incursão em Pista": 5,
                "Excursão de Pista": 1,
                "Colisões Entre Aeronaves e Veículos, Equipamentos, Estrutura": 3,
                "Colisão entre Veículos, Equipamentos, Estruturas": 5,
                "F.O.D": 10,
                "Colisão com Aves": 40,
                "RELPREV": 30,
            },
            }

            import streamlit.components.v1 as components

            # ======================================================
            # 🎯 ACOMPANHAMENTO DE METAS — GRID ELEGANTE (HTML REAL)
            # ======================================================

            def meta_card_kpi(indicador, aeroporto_label, valor, meta):

                pct = (valor / meta) if meta > 0 else 0
                pct_pct = pct * 100
                pct_bar = min(pct_pct, 150)

                nome_ind = indicador.upper()

                # 🔵 REGRA ESPECIAL — RELPREV (quanto MAIOR, melhor)
                if "RELPREV" in nome_ind:
                    bar_color = "#96CE00" if valor >= meta else "#ff5a5f"

                # 🔴 REGRA PADRÃO — DEMAIS INDICADORES (quanto MENOR, melhor)
                else:
                    if pct < 0.8:
                        bar_color = "#96CE00"
                    elif pct < 1:
                        bar_color = "#ffb703"
                    else:
                        bar_color = "#ff5a5f"

                return f"""
                <div class="meta-card">
                    <div class="meta-title">{indicador}</div>
                    <div class="meta-aero">{aeroporto_label}</div>

                    <div class="meta-value" style="color:{bar_color};">
                        {fmt_int(valor)}
                    </div>

                    <div class="meta-sub">
                        Meta: {fmt_int(meta)}
                    </div>

                    <div class="meta-bar">
                        <div class="meta-bar-fill"
                            style="width:{pct_bar:.1f}%; background:{bar_color};">
                        </div>
                    </div>

                    <div class="meta-pct">
                        {pct_pct:.1f}% da meta
                    </div>
                </div>
                """

            # ======================================================
            # 📌 ORDEM FIXA (NUNCA MUDA)
            # ======================================================
            ordem_indicadores = [
                "Incursão em Pista",
                "Colisões Entre Aeronaves e Veículos, Equipamentos, Estrutura",
                "Colisão entre Veículos, Equipamentos, Estruturas",
                "F.O.D",
                "Colisão com Aves",
                "Excursão de Pista",
                "RELPREV",
            ]

            # ======================================================
            # 🔎 INDICADORES A EXIBIR (RESPEITA FILTRO E ORDEM)
            # ======================================================
            if st.session_state.ind_sel == ["Todos"]:
                indicadores_grid = ordem_indicadores
            else:
                indicadores_grid = [
                    ind for ind in ordem_indicadores
                    if ind in st.session_state.ind_sel
                ]

            # ======================================================
            # 🧱 MONTA HTML
            # ======================================================
            html_cards = '<div class="metas-grid">'

            # ======================================================
            # CASO 1 — TODOS OS AEROPORTOS
            # ======================================================
            if st.session_state.aero_sel == ["Todos"]:

                aeroporto_label = "Todos os Aeroportos"

                for ind in indicadores_grid:

                    valor_total = (
                        df_f[df_f["indicador"] == ind]["eventos"].sum()
                        if not df_f.empty else 0
                    )

                    meta_total = sum(metas.get(ind, 0) for metas in METAS.values())

                    if meta_total == 0:
                        continue

                    html_cards += meta_card_kpi(
                        indicador=ind,
                        aeroporto_label=aeroporto_label,
                        valor=int(valor_total),
                        meta=int(meta_total),
                    )

            # ======================================================
            # CASO 2 — AEROPORTO ESPECÍFICO
            # ======================================================
            else:
                aeroporto = st.session_state.aero_sel[0]
                aeroporto_label = aeroporto

                for ind in indicadores_grid:

                    if ind not in METAS.get(aeroporto, {}):
                        continue

                    valor_total = (
                        df_f[
                            (df_f["aeroporto"] == aeroporto) &
                            (df_f["indicador"] == ind)
                        ]["eventos"].sum()
                        if not df_f.empty else 0
                    )

                    meta_valor = METAS[aeroporto][ind]

                    html_cards += meta_card_kpi(
                        indicador=ind,
                        aeroporto_label=aeroporto_label,
                        valor=int(valor_total),
                        meta=int(meta_valor),
                    )

            html_cards += "</div>"

            # ======================================================
            # 🎨 RENDERIZAÇÃO FINAL
            # ======================================================
            components.html(
            f"""
            <div style="width:100%; overflow: visible;">
                <style>
                    .metas-grid {{
                        display: grid;
                        grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
                        gap: 18px;
                        margin-top: 16px;
                        margin-bottom: 28px;
                    }}

                    .meta-card {{
                        background: #f8f9fb;
                        border: 2px solid rgba(0,0,0,0.08);
                        border-radius: 16px;
                        padding: 16px 14px;
                        text-align: center;
                        box-shadow: 0 6px 16px rgba(0,0,0,0.06);
                        display: flex;
                        flex-direction: column;
                        gap: 6px;
                    }}

                    .meta-title {{
                        font-size: 16px;
                        font-weight: 1000;
                        color: #1a2732;
                        min-height: 56px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        text-align: center;
                    }}

                    .meta-aero {{
                        font-size: 11px;
                        font-weight: 900;
                        color: #6b7c93;
                        text-transform: uppercase;
                        letter-spacing: 0.4px;
                    }}

                    .meta-value {{
                        font-size: 42px;
                        font-weight: 1000;
                        min-height: 48px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                    }}

                    .meta-sub {{
                        font-size: 16px;
                        font-weight: 1000;
                        color: #5b6b7b;
                    }}

                    .meta-bar {{
                        background: #e5e7eb;
                        border-radius: 999px;
                        height: 10px;
                        overflow: hidden;
                    }}

                    .meta-bar-fill {{
                        height: 100%;
                        border-radius: 999px;
                        transition: width 0.6s ease;
                    }}

                    .meta-pct {{
                        font-size: 14px;
                        font-weight: 1000;
                        color: #1a2732;
                    }}
                </style>

                {html_cards}
            </div>
            """,
            height=620,
            scrolling=False
            )
        
        # ======================================================
        # 🎯 STATUS DAS METAS POR AEROPORTO (BLOCO SEPARADO)
        # ======================================================

        # ⚠️ CASO 1 — ANO = TODOS
        if st.session_state.ano_sel == ["Todos"]:

            st.info("⚠️ Favor selecionar o **Ano** para visualizar o status das metas.")

        # ✅ CASO 2 — UM ÚNICO ANO SELECIONADO
        elif (
            len(st.session_state.ano_sel) == 1
            and not df.empty
        ):

            ano_ref = st.session_state.ano_sel[0]

            st.markdown("### 🎯 Status das Metas por Aeroporto")
            st.caption(f"Avaliação consolidada • Ano {ano_ref}")

            # ======================================================
            # 🔎 BASE PARA STATUS
            # - respeita ANO
            # ======================================================
            df_base_status = df[df["ano"] == ano_ref]

            # ======================================================
            # 🔎 DEFINE INDICADORES A AVALIAR
            # ======================================================
            if st.session_state.ind_sel == ["Todos"]:
                indicadores_status = None
            else:
                indicadores_status = st.session_state.ind_sel

            # ======================================================
            # 🔎 DEFINE AEROPORTOS A AVALIAR  ✅ NOVO
            # ======================================================
            if st.session_state.aero_sel == ["Todos"]:
                aeroportos_status = METAS.keys()
            else:
                aeroportos_status = st.session_state.aero_sel

            atingiram = []
            nao_atingiram = []

            # ======================================================
            # 🔄 LOOP POR AEROPORTO (RESPEITA FILTRO)
            # ======================================================
            for aeroporto in aeroportos_status:

                if aeroporto not in METAS:
                    continue

                metas_aero = METAS[aeroporto]

                df_aero = df_base_status[df_base_status["aeroporto"] == aeroporto]
                if df_aero.empty:
                    continue

                ok = True

                # ======================================================
                # 🔄 LOOP POR INDICADOR
                # ======================================================
                for indicador, meta in metas_aero.items():

                    # ⛔ RESPEITA FILTRO DE INDICADOR
                    if indicadores_status is not None and indicador not in indicadores_status:
                        continue

                    valor = df_aero[df_aero["indicador"] == indicador]["eventos"].sum()

                    if meta == 0:
                        continue

                    # 🔵 REGRA ESPECIAL — RELPREV
                    if "RELPREV" in indicador.upper():
                        if valor < meta:
                            ok = False
                            break
                    # 🔴 REGRA PADRÃO — demais indicadores
                    else:
                        if valor > meta:
                            ok = False
                            break

                if ok:
                    atingiram.append(aeroporto)
                else:
                    nao_atingiram.append(aeroporto)

            # ======================================================
            # 🎨 FUNÇÃO DE RENDERIZAÇÃO
            # ======================================================
            def bloco_aero(lista, titulo, cor_borda, cor_fundo):

                if not lista:
                    return ""

                cards = ""
                for aero in sorted(lista):
                    cards += f"""
                    <div class="status-card" style="
                        border: 2px solid {cor_borda};
                        background: {cor_fundo};
                    ">
                        <div class="status-aero">{aero}</div>
                    </div>
                    """

                return f"""
                <div class="status-group">
                    <div class="status-title">{titulo}</div>
                    <div class="status-grid">
                        {cards}
                    </div>
                </div>
                """

            # ======================================================
            # 🖼️ HTML FINAL
            # ======================================================
            status_html = f"""
            <style>
                .status-group {{
                    margin-top: 18px;
                    margin-bottom: 28px;
                }}

                .status-title {{
                    font-size: 18px;
                    font-weight: 1000;
                    color: #1a2732;
                    margin-bottom: 10px;
                }}

                .status-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
                    gap: 12px;
                }}

                .status-card {{
                    border-radius: 14px;
                    padding: 14px 10px;
                    text-align: center;
                    font-weight: 1000;
                    box-shadow: 0 4px 10px rgba(0,0,0,0.06);
                }}

                .status-aero {{
                    font-size: 16px;
                    letter-spacing: 0.5px;
                }}
            </style>

            {bloco_aero(atingiram, "🟢 Aeroportos que atingiram as metas", "#96CE00", "#f1f8e9")}
            {bloco_aero(nao_atingiram, "🔴 Aeroportos que não atingiram as metas", "#ff5a5f", "#fdecea")}
            """

            components.html(
                f"""
                <div style="width:100%; overflow: visible;">
                    {status_html}
                </div>
                """,
                height=360,
                scrolling=False
            )

with tab3:
    st.markdown("### 📦 Exportações")
    st.caption("Relatório XLSX + pacote ZIP (inclui pendências e metadados).")

    sheets = {
        "RAW_FILTRADO": df_f.drop(columns=["chave"], errors="ignore"),
        "EVENTOS_MENSAL_AEROPORTO": monthly,
        "TOTAL_EVENTOS_ANO": df_f.groupby("ano", as_index=False)["eventos"].sum().sort_values("ano"),
        "TOTAL_EVENTOS_INDICADOR": df_f.groupby("indicador", as_index=False)["eventos"].sum().sort_values("eventos", ascending=False),
    }
    xlsx_bytes = df_to_excel_bytes(sheets)

    st.download_button(
        "⬇️ Baixar relatório XLSX (filtros aplicados)",
        data=xlsx_bytes,
        file_name="IDSO_Relatorio.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    meta = {
        "generated_at_utc": datetime.utcnow().isoformat() + "Z",
        "today_local": today.isoformat(),
        "source_name": source_name,
        "hash_sha256": sha,
        "filters": {"aeroporto": sel_aero, "ano": sel_ano, "indicador": sel_ind, "mes": sel_mes},
        "rule": {"due_day": 10, "required_period": int(required_period), "due_date": due.isoformat()},
        "counts": {
            "rows_filtered": int(len(df_f)),
            "eventos_filtered": int(total_eventos),
            "mov_filtered_sum_by_month": int(total_mov),
        }
    }

    pend_export = pend_df.copy()
    if not pend_export.empty:
        pend_export["required_period_txt"] = pend_export["required_mes_abrev"].astype(str) + "/" + pend_export["required_ano"].astype(str)
        pend_export = pend_export.sort_values(["is_ok","aeroporto"])

    zip_bytes = make_zip([
        ("metadata.json", json.dumps(meta, ensure_ascii=False, indent=2).encode("utf-8")),
        ("IDSO_Relatorio.xlsx", xlsx_bytes),
        ("Pendencias_IDSO.xlsx", df_to_excel_bytes({"PENDENCIAS": pend_export})),
    ])

    st.download_button(
        "📦 Baixar pacote ZIP (XLSX + pendências + metadados)",
        data=zip_bytes,
        file_name="IDSO_Pacote.zip",
        mime="application/zip"
    )
