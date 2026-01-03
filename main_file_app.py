import streamlit as st
import pandas as pd
from jobspy import scrape_jobs
import plotly.express as px
import plotly.graph_objects as go
from fpdf import FPDF
from datetime import datetime
import io
import PyPDF2
import streamlit.components.v1 as components

# --- 1. CONFIGURATION & THEME ---
st.set_page_config(layout="wide", page_title="Career Hub Dual Pro", page_icon="🚀")

# CSS Injector for Dynamic Theming
def set_theme(is_finance):
    if is_finance:
        # Finance: Blue/Orange Gradient
        grad = "linear-gradient(90deg, #1f77b4 0%, #ff7f0e 100%)"
        accent = "#1f77b4"
    else:
        # Comm: Purple/Pink Gradient
        grad = "linear-gradient(90deg, #6a0dad 0%, #ff69b4 100%)"
        accent = "#6a0dad"
        
    st.markdown(f"""
    <style>
        .stAppHeader {{ background-color: transparent; }}
        .main-header {{
            background: {grad};
            padding: 20px;
            border-radius: 10px;
            color: white;
            text-align: center;
            font-family: 'Helvetica', sans-serif;
            margin-bottom: 25px;
        }}
        .metric-card {{
            background-color: #f0f2f6;
            border-left: 5px solid {accent};
            padding: 15px;
            border-radius: 5px;
            text-align: center;
            color: #333333; /* Noir/Gris foncé forcé pour visibilité */
        }}
        .metric-card h3 {{
            color: #555555;
            font-size: 1rem;
            margin: 0;
        }}
        .metric-card h2 {{
            color: #000000;
            font-size: 1.8rem;
            margin: 5px 0 0 0;
        }}
    </style>
    """, unsafe_allow_html=True)
    return grad

# --- 2. DATASETS (Specific User Data) ---

# FINANCE PRO DATA
FIN_ROLES = [
    'Analyste LCB-FT', 'Quant Risk Analyst', 'Auditeur Finance', 'Portfolio Analyst', 
    'Compliance Officer', 'Risk Manager', 'Analyste Crédit', 'Analyste ESG Quant', 
    'Contrôleur Gestion Finance', 'Consultant Finance Stratégie',
    'Auditeur Conformité', 'Analyste Transactionnel', 'Risk Controller', 
    'KYC Specialist', 'Regulatory Reporting Analyst'
]
FIN_SALARY = {
    "Big4 (Audit)": {"EY": 44, "KPMG": 46, "PwC": 45, "Deloitte": 48},
    "Banques": {"BNP Paribas": 45, "Société Générale": 44, "Crédit Agricole": 43, "Banque de France": 42},
    "Fintech": {"Yomoni": 42, "Nalo": 41, "Ramify": 40},
    "Asset Mgmt": {"Amundi": 46, "OFI Invest": 44, "Carmignac": 45, "BNP AM": 47}
}
FIN_SKILLS = {"Python": 90, "AML/LCB-FT": 95, "AMF Regs": 85, "Excel/VBA": 80, "MiFID II": 75, "Risk Mgmt": 85, "SQL": 60, "Bloomberg": 70}
FIN_QUESTIONS = [
    "Quels sont les indices d'une opération de blanchiment (Red Flags) ?",
    "Expliquez le concept de la VaR (Value at Risk) à un non-initié.",
    "Comment gérez-vous une alerte KYC sur une PPE ?",
    "Quelles sont les implications de MiFID II pour la conformité ?",
    "Comment utilisez-vous Python pour l'analyse de risque ?",
    "Décrivez le cycle de reporting réglementaire (SURFI/COREP).",
    "Différence entre Audit Interne et Contrôle Permanent ?",
    "Comment valoriser un produit dérivé complexe ?",
    "Votre réaction face à un trader qui refuse de justifier une transaction ?",
    "Quels sont les enjeux actuels de la finance durable (SFDR) ?"
]

# COMMUNICATION PRO DATA
COMM_ROLES = [
    'Chargé Communication', 'Press Officer', 'Content Manager', 'Community Manager', 
    'Relations Publiques', 'Rédacteur Web', 'Coordinateur Événementiel', 
    'Responsable Réseaux Sociaux', 'Chargé de Contenu', 'Producteur Podcast'
]
COMM_SALARY = {
    "Agences": {"Publicis": 40, "Havas": 39, "BETC": 41, "TBWA": 40},
    "Entreprises": {"LVMH": 44, "TotalEnergies": 42, "SNCF": 40, "Veolia": 41},
    "Startups": {"Contentsquare": 38, "Mirakl": 39, "BackMarket": 37, "Payfit": 38},
    "Médias": {"TF1": 41, "Radio France": 40, "Le Monde": 39, "Mediapart": 38}
}
COMM_SKILLS = {"Storytelling": 95, "Canva/Figma": 80, "LinkedIn": 90, "Podcast Prod": 85, "SEO": 75, "Wordpress": 70, "Relations Presse": 85, "Adobe Suite": 60}
COMM_QUESTIONS = [
    "Comment mesurer le ROI d'une campagne de communication ?",
    "Quelle stratégie pour gérer un bad buzz sur Twitter ?",
    "Pitcher un sujet complexe pour un communiqué de presse.",
    "Comment adapter le ton d'une marque sur LinkedIn vs TikTok ?",
    "Quelles sont les étapes de production d'un podcast corporate ?",
    "Différence entre Brand Content et Publicité ?",
    "Comment optimiser le référencement (SEO) d'un article ?",
    "Gérer une interview avec un journaliste hostile.",
    "Quels outils utilisez-vous pour la veille médiatique ?",
    "Comment communiquez-vous une mauvaise nouvelle en interne ?"
]

# --- 3. UTILS & EXPORT ---
def safe_text(text):
    """Encodes text to latin-1, replacing incompatible characters (like emojis) with '?'"""
    return text.encode('latin-1', 'replace').decode('latin-1')

def create_pdf(profile_name, roles, market_skills, user_skills, interview_score, cv_text=""):
    pdf = FPDF()
    pdf.add_page()
    
    # Header
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, safe_text(f"Career Hub Pro 2026 - {profile_name}"), ln=True, align='C')
    pdf.ln(10)
    
    # Stats Summary
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, safe_text(f"Interview Readiness Score: {interview_score}/10"), ln=True)
    pdf.ln(5)

    # Roles
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, safe_text("Target Roles:"), ln=True)
    pdf.set_font("Arial", '', 10)
    for r in roles[:5]:
        pdf.cell(0, 8, safe_text(f"- {r}"), ln=True)
    pdf.ln(5)
    
    # Comparative Skills
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, safe_text("Skills Assessment (Market vs You):"), ln=True)
    pdf.set_font("Arial", '', 10)
    
    for s, target_v in list(market_skills.items())[:8]:
        user_v = user_skills.get(s, 0)
        gap = user_v - target_v
        gap_str = f"({'+' if gap >=0 else ''}{gap}%)"
        pdf.cell(0, 8, safe_text(f"- {s}: Range {target_v}% | You {user_v}% {gap_str}"), ln=True)
        
    # CV Section
    if cv_text:
        pdf.ln(10)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, safe_text("Uploaded CV Excerpt:"), ln=True)
        pdf.set_font("Arial", '', 9)
        clean_cv = safe_text(cv_text[:2000] + ("..." if len(cv_text) > 2000 else ""))
        pdf.multi_cell(0, 5, clean_cv)
        
    return pdf.output(dest='S').encode('latin-1')

def scrape_strict(role, loc, weeks):
    # EXTENDED NEGATIVE KEYWORDS
    # We filter out Internships AND irrelevant industries (Parfum, Cosmetics for Analyst roles, IT devs)
    negative_kw = [
        # Contract Types
        "stage", "internship", "alternance", "apprenti", "apprentissage", "stagiaire", "interim", "seasonal",
        # Irrelevant Roles/Industries for these profiles
        "parfum", "cosmetic", "beauty", "sensoriel", "sensory", "olfactif", # User specific request
        "vendeur", "sales associate", "conseiller de vente", "magasin", "boutique", # Retail
        "chauffeur", "livreur", "ouvrier", "technicien de maintenance", # Blue collar
        "medecin", "infirmier", "sante", "biologiste", # Medical
        "architecte", "btp", "chantier", # Construction
        # IT strict (unless it matches Quant which is preserved by positive matches usually, but let's be safe)
        "technicien support", "helpdesk", "cobol", "java developer", "full stack" 
    ]
    
    try:
        hours = weeks * 168
        jobs = scrape_jobs(
            site_name=["linkedin", "indeed", "glassdoor"],
            search_term=role,
            location=loc,
            results_wanted=20, # Higher count to allow filtering
            hours_old=hours,
            country_indeed='france',
            job_type="fulltime"
        )
        if jobs.empty: return pd.DataFrame()
        
        # Filter Logic
        clean_jobs = jobs[~jobs['title'].str.lower().str.contains('|'.join(negative_kw), na=False)]
        return clean_jobs
    except:
        return pd.DataFrame()

# --- 4. MAIN APP LOGIC ---

# >>> SELECTEUR PRINCIPAL <<<
st.sidebar.markdown("## 👤 SÉLECTEUR DE PROFIL")
profile = st.sidebar.radio(
    "Mode",
    ["🚀 Finance Pro", "📢 Communication Pro"],
    label_visibility="collapsed"
)

is_finance = "Finance" in profile
set_theme(is_finance)

# >>> CLOCK & DATE (Dynamic via JS) <<<
clock_html = """
<!DOCTYPE html>
<html>
<head>
<script>
function updateClock() {
    const now = new Date();
    const options = { day: 'numeric', month: 'long', year: 'numeric', hour: '2-digit', minute: '2-digit' };
    let timeString = now.toLocaleDateString('fr-FR', options).replace(',', ' |');
    document.getElementById('clock').innerText = "📅 " + timeString;
}
setInterval(updateClock, 1000);
window.onload = updateClock;
</script>
</head>
<body style="margin:0; background-color: transparent;">
    <div style='background-color: rgba(255,255,255,0.1); padding: 10px; border-radius: 5px; text-align: center; font-family: sans-serif; color: inherit;'>
        <span id="clock" style='font-size: 1.2em; font-weight: bold;'>Loading...</span>
    </div>
</body>
</html>
"""
st.sidebar.markdown("<br>", unsafe_allow_html=True) # Spacer
with st.sidebar:
    components.html(clock_html, height=60, scrolling=False)

# HEADER
st.markdown(f"<div class='main-header'><h1>{profile} Dashboard</h1><p>Master 2 Quantitative Finance vs Journaliste/Podcast Pro</p></div>", unsafe_allow_html=True)

# DATA LOADING
if is_finance:
    roles = FIN_ROLES
    salaries = FIN_SALARY
    skills = FIN_SKILLS
    questions = FIN_QUESTIONS
    theme_color = "#1f77b4"
else:
    roles = COMM_ROLES
    salaries = COMM_SALARY
    skills = COMM_SKILLS
    questions = COMM_QUESTIONS
    theme_color = "#6a0dad"

# SESSION STATE INIT (Crucial for interactivity)
if 'user_skills' not in st.session_state:
    st.session_state.user_skills = skills.copy() # Start with Market defaults
if 'interview_scores' not in st.session_state:
    st.session_state.interview_scores = {} # Store scores per question

# TABS
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 KPI & Market", "🔍 Job Search", "🧠 Interview Coach", "📈 Skills Matrix", "📄 Export & CV"])

with tab1:
    # 2. DASHBOARD KPI
    avg_interview_score = 0
    if st.session_state.interview_scores:
        avg_interview_score = sum(st.session_state.interview_scores.values()) / len(st.session_state.interview_scores)
    
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown("<div class='metric-card'><h3>CDI Ciblés</h3><h2>Paris/IDF</h2></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='metric-card'><h3>Salaire Moyen</h3><h2>{'45k€' if is_finance else '40k€'}</h2></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='metric-card'><h3>Interview Score</h3><h2>{avg_interview_score:.1f}/10</h2></div>", unsafe_allow_html=True)
    c4.markdown("<div class='metric-card'><h3>Entreprises Trackées</h3><h2>20</h2></div>", unsafe_allow_html=True)
    
    st.divider()
    
    # 4. SALARY RADAR
    st.subheader(f"💰 Radar des Salaires ({'Finance' if is_finance else 'Communication'})")
    salary_list = []
    for category, companies in salaries.items():
        for comp, sal in companies.items():
            salary_list.append({"Category": category, "Company": comp, "Salary (k€)": sal})
    df_sal = pd.DataFrame(salary_list)
    fig = px.bar(
        df_sal, x="Company", y="Salary (k€)", color="Category", 
        title=f"Salaire Junior Est. ({profile})", text_auto=True,
        color_discrete_sequence=px.colors.qualitative.Prism if not is_finance else px.colors.qualitative.D3
    )
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("🔍 Recherche CDI Strict (Paris/IDF)")
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1: selected_role = st.selectbox("Choisir le poste", roles)
    with c2: weeks = st.slider("Publié depuis (semaines)", 1, 5, 2)
    with c3: loc = st.text_input("Localisation", "Paris, France")
    
    if st.button("Lancer Recherche", type="primary"):
        with st.spinner(f"Chasse sur {weeks} semaines pour {selected_role}..."):
            df_jobs = scrape_strict(selected_role, loc, weeks)
            if not df_jobs.empty:
                st.success(f"{len(df_jobs)} CDI trouvés !")
                st.data_editor(
                    df_jobs[['title', 'company', 'location', 'date_posted', 'job_url']],
                    column_config={"job_url": st.column_config.LinkColumn("Postuler")},
                    use_container_width=True
                )
            else:
                st.warning("Aucun résultat strict trouvé.")

with tab3:
    st.subheader("🎤 Entraînement Technique & Situationnel")
    st.caption("Votre performance aux questions est enregistrée (Score Interviews).")
    
    q_idx = st.number_input("Question N°", 1, len(questions), 1) - 1
    current_q = questions[q_idx]
    
    st.markdown(f"### ❓ {current_q}")
    
    with st.expander("📝 Rédiger ma réponse", expanded=True):
        st.text_area("Votre pitch...", height=150, key=f"ans_{q_idx}")
    
    c_score, c_reveal = st.columns([1, 2])
    with c_score:
        score = st.slider(f"Auto-évaluation Q{q_idx+1}", 0, 10, st.session_state.interview_scores.get(current_q, 5), key=f"score_{q_idx}")
        st.session_state.interview_scores[current_q] = score
        
    with c_reveal:
        if st.button("💡 Voir indice réponse"):
            if is_finance:
                st.info("💡 Astuce : Structurez avec 'Contexte Réglementaire > Analyse Technique > Résultat'. Citez Tracfin/AMF.")
            else:
                st.info("💡 Astuce : Structurez avec 'Cible > Message > Canal > KPI'. Soyez créatif mais orienté résultats.")

with tab4:
    st.subheader("🧠 Matrice de Compétences : Marché vs Réalité")
    
    col_edit, col_chart = st.columns([1, 2])
    
    with col_edit:
        st.markdown("### 🎚️ Mes Niveaux (0-100%)")
        for skill_name, default_val in skills.items():
            # Init manually if not exists for fail-safety
            if skill_name not in st.session_state.user_skills:
                st.session_state.user_skills[skill_name] = default_val
            
            # Update session state with slider
            new_val = st.slider(skill_name, 0, 100, st.session_state.user_skills[skill_name], key=f"skill_{skill_name}")
            st.session_state.user_skills[skill_name] = new_val
            
    with col_chart:
        # Prepare Data for Comparative Radar
        categories = list(skills.keys())
        market_values = list(skills.values())
        user_values = [st.session_state.user_skills.get(k, 50) for k in categories]
        
        fig = go.Figure()
        
        # Trace 1: Market
        fig.add_trace(go.Scatterpolar(
            r=market_values, theta=categories, fill='toself', name='Attente Marché',
            line_color='gray', opacity=0.4
        ))
        
        # Trace 2: User
        fig.add_trace(go.Scatterpolar(
            r=user_values, theta=categories, fill='toself', name='Mon Profil',
            line_color=theme_color
        ))
        
        fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=True, title="Gap Analysis")
        st.plotly_chart(fig, use_container_width=True)

with tab5:
    st.subheader("📄 Export & CV")
    st.write("Générez un rapport PDF comparatif incluant vos scores d'entretien et votre CV.")
    
    uploaded_file = st.file_uploader("📂 Uploader votre CV (PDF)", type="pdf")
    extracted_cv_text = ""
    if uploaded_file:
        try:
            reader = PyPDF2.PdfReader(uploaded_file)
            for page in reader.pages: extracted_cv_text += page.extract_text() or ""
            st.success(f"CV analysé.")
        except: st.error("Erreur lecture PDF")
    
    # Calculate avg interview score for PDF
    final_score = 0
    if st.session_state.interview_scores:
        final_score = sum(st.session_state.interview_scores.values()) / len(st.session_state.interview_scores)

    if st.button("⬇️ Générer PDF Complet"):
        pdf_bytes = create_pdf(profile, roles, skills, st.session_state.user_skills, round(final_score, 1), extracted_cv_text)
        st.download_button("Télécharger Rapport PDF", data=pdf_bytes, file_name="Career_Hub_Pro_2026.pdf", mime="application/pdf")
