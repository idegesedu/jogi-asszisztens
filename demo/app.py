"""
Jogi Asszisztens Demo - Streamlit UI
Befektetői bemutató verzió - Továbbfejlesztett Frontend
"""

import streamlit as st
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Import custom modules
from rag_engine import LegalRAGEngine
from lawyer_recommender import LawyerRecommender
from geolocation import (
    get_user_location_from_ip,
    parse_location_input,
    get_location_display_name
)
from document_processor import PDFProcessor, OfficialLetterInterpreter
import anthropic

# Page config
st.set_page_config(
    page_title="Jogi Asszisztens MI - Demo",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 1rem;
    }
    .subheader {
        font-size: 1.2rem;
        color: #64748B;
        text-align: center;
        margin-bottom: 2rem;
    }
    .disclaimer {
        background-color: #FEF3C7;
        border-left: 4px solid #F59E0B;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 5px;
    }
    .centered-input {
        max-width: 800px;
        margin: 0 auto;
    }
    .summary-box {
        background-color: #EFF6FF;
        border-left: 4px solid #3B82F6;
        padding: 1.5rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    .urgency-high {
        background-color: #FEE2E2;
        border-left: 4px solid #EF4444;
        padding: 1rem;
        border-radius: 5px;
    }
    .urgency-medium {
        background-color: #FEF3C7;
        border-left: 4px solid #F59E0B;
        padding: 1rem;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

def init_session_state():
    """Initialize Streamlit session state variables"""
    if 'initialized' not in st.session_state:
        st.session_state.initialized = True
        st.session_state.rag_engine = None
        st.session_state.lawyer_recommender = None
        st.session_state.pdf_processor = None
        st.session_state.letter_interpreter = None

        # Chat state
        st.session_state.chat_history = []
        st.session_state.show_lawyer_request = False
        st.session_state.user_location = None
        st.session_state.detected_category = None
        st.session_state.last_answer = None

        # PDF state
        st.session_state.pdf_file = None
        st.session_state.pdf_analysis = None
        st.session_state.pdf_chat_history = []

        # Letter state
        st.session_state.letter_text = None
        st.session_state.letter_analysis = None
        st.session_state.letter_chat_history = []


def initialize_engines():
    """Initialize RAG, Lawyer Recommender, and Document Processors"""
    # Check for API key
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")

    if not api_key:
        st.error("API kulcs nem található! Állítsd be az OPENAI_API_KEY vagy ANTHROPIC_API_KEY környezeti változót.")
        st.stop()

    # Determine provider
    provider = "openai" if os.getenv("OPENAI_API_KEY") else "anthropic"

    # Initialize RAG Engine
    if st.session_state.rag_engine is None:
        with st.spinner("RAG Engine inicializálása..."):
            st.session_state.rag_engine = LegalRAGEngine(
                laws_dir="data/laws",
                chroma_persist_dir="data/chroma_db",
                llm_provider=provider,
                api_key=api_key
            )
            st.session_state.rag_engine.load_and_index_laws(force_reload=False)

    # Initialize Lawyer Recommender
    if st.session_state.lawyer_recommender is None:
        st.session_state.lawyer_recommender = LawyerRecommender("data/lawyers.json")

    # Initialize Document Processors (for Anthropic only currently)
    if provider == "anthropic":
        if st.session_state.pdf_processor is None:
            anthropic_client = anthropic.Anthropic(api_key=api_key)
            st.session_state.pdf_processor = PDFProcessor(llm_client=anthropic_client)
            st.session_state.letter_interpreter = OfficialLetterInterpreter(llm_client=anthropic_client)


# ============================================================================
# HEADER & SIDEBAR
# ============================================================================

def display_header():
    """Display app header"""
    st.markdown('<div class="main-header">⚖️ Jogi Asszisztens MI</div>', unsafe_allow_html=True)
    st.markdown('<div class="subheader">Folyamatosan tanuló mesterséges intelligencia magyar jogi ügyekben</div>', unsafe_allow_html=True)

    # Disclaimer
    st.markdown("""
    <div class="disclaimer">
        <strong>⚠️ FONTOS FIGYELMEZTETÉS</strong><br>
        Ez az alkalmazás NEM nyújt jogi tanácsot. Az itt található információk általános tájékoztató jellegűek,
        és nem helyettesítik a szakképzett ügyvéd tanácsát. Minden jogi ügy egyedi, ezért konkrét esetben
        mindig forduljon szakemberhez.
    </div>
    """, unsafe_allow_html=True)


def display_sidebar():
    """Display sidebar with controls and info"""
    with st.sidebar:
        st.title("📋 Kezelőpult")

        # Chat History Management
        st.markdown("### 📝 Beszélgetés Kezelés")
        chat_count = len(st.session_state.chat_history)
        st.caption(f"Jelenlegi üzenetek: {chat_count}")

        if st.button("🗑️ Új Beszélgetés", use_container_width=True, type="primary"):
            if chat_count > 0:
                if st.button("⚠️ Biztos törli?", use_container_width=True):
                    st.session_state.chat_history = []
                    st.session_state.show_lawyer_request = False
                    st.session_state.user_location = None
                    st.session_state.detected_category = None
                    st.session_state.last_answer = None
                    st.success("✓ Beszélgetés törölve")
                    st.rerun()
            else:
                st.info("Nincs mit törölni")

        st.markdown("---")

        # Info section
        st.markdown("### ℹ️ Tudnivalók")
        st.markdown("""
        **Ez egy demo alkalmazás** magyar törvényekhez.

        **Funkciók:**
        - 💬 RAG-alapú válaszok
        - 📄 PDF elemzés
        - 📧 Levél értelmezés
        - 👨‍⚖️ Ügyvéd ajánlás
        """)

        st.markdown("---")

        # Statistics
        st.markdown("### 📊 Statisztikák")
        st.markdown(f"""
        - 📚 **6 törvény** az adatbázisban
        - 🏢 **18 ügyvédi iroda** Budapesten
        - 🤖 **Claude AI** motor
        """)

        st.markdown("---")

        # Lawyer help section
        st.markdown("### 👨‍⚖️ Ügyvédi Segítség")
        st.markdown("Személyes konzultációt keres?")
        if st.button("Ügyvéd keresése", use_container_width=True):
            st.session_state.show_lawyer_request = True
            st.rerun()


# ============================================================================
# TAB 1: CHAT ASSISTANT
# ============================================================================

def render_chat_tab():
    """Render the main chat assistant tab"""
    st.markdown("### 💬 Hogyan segíthetek?")
    st.write("Írja le jogi kérdését vagy problémáját, és én megpróbálok segíteni a magyar jogszabályok alapján!")

    # Display chat history
    for message in st.session_state.chat_history:
        with st.chat_message(message['role']):
            st.write(message['content'])

    # Chat input (centered using columns)
    col1, col2, col3 = st.columns([1, 6, 1])
    with col2:
        user_query = st.chat_input("Például: 'Jogellenes a felmondásom? Nem kaptam végkielégítést.'")

    if user_query:
        handle_chat_query(user_query)
        st.rerun()

    # Lawyer recommendation flow
    if st.session_state.show_lawyer_request and not st.session_state.get('show_lawyer_location'):
        display_lawyer_request_prompt()

    if st.session_state.get('show_lawyer_location'):
        if not st.session_state.user_location:
            display_location_request()
        else:
            display_lawyer_recommendations()

            if st.button("🔄 Új kérdés", use_container_width=True):
                st.session_state.show_lawyer_request = False
                st.session_state.show_lawyer_location = False
                st.session_state.user_location = None
                st.rerun()


def handle_chat_query(query: str):
    """Handle user legal question"""
    st.session_state.chat_history.append({"role": "user", "content": query})

    with st.spinner("Válasz generálása... (RAG + LLM)"):
        result = st.session_state.rag_engine.answer_query(query, n_results=5)

    st.session_state.last_answer = result
    st.session_state.detected_category = result['detected_category']
    st.session_state.chat_history.append({"role": "assistant", "content": result['answer']})
    st.session_state.show_lawyer_request = True


def display_lawyer_request_prompt():
    """Display opt-in lawyer recommendation prompt"""
    st.markdown("---")
    st.markdown("### 💼 Ügyvédi Segítség")
    st.info("Szeretne ügyvédi segítséget ehhez az esethez? Ajánlhatunk szakosodott ügyvédeket a közelében.")

    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("✅ Igen, keresek ügyvédet", use_container_width=True, type="primary"):
            st.session_state.show_lawyer_location = True
            st.rerun()

    with col2:
        if st.button("❌ Nem, köszönöm", use_container_width=True):
            st.session_state.show_lawyer_request = False
            st.rerun()


def display_location_request():
    """Display location input for lawyer recommendations"""
    st.markdown("---")
    st.markdown("### 📍 Tartózkodási Hely")
    st.write("A legközelebbi ügyvédek megtalálásához szükségünk van a tartózkodási helyére.")

    col1, col2 = st.columns([2, 1])

    with col1:
        location_input = st.text_input(
            "Város vagy kerület:",
            placeholder="pl. Budapest V. kerület, Debrecen, stb.",
            help="Írja be a várost vagy Budapest esetén a kerületet"
        )

    with col2:
        auto_detect = st.button("🌍 Automatikus", use_container_width=True)

    if auto_detect:
        with st.spinner("Helymeghatározás..."):
            st.session_state.user_location = get_user_location_from_ip()
        st.success(f"Észlelt hely: {get_location_display_name(st.session_state.user_location)}")
        st.rerun()

    if location_input:
        st.session_state.user_location = parse_location_input(location_input)
        st.success(f"Kiválasztott hely: {get_location_display_name(st.session_state.user_location)}")
        st.rerun()


def display_lawyer_recommendations():
    """Display lawyer recommendations"""
    if not st.session_state.user_location:
        return

    st.markdown("---")
    st.markdown("### 🏢 Ajánlott Ügyvédek")

    location_name = get_location_display_name(st.session_state.user_location)
    category = st.session_state.detected_category or "általános"
    category_display = st.session_state.lawyer_recommender.get_category_display_name(category)

    st.write(f"**Terület:** {category_display}")
    st.write(f"**Helyszín:** {location_name}")

    with st.spinner("Ügyvédek keresése..."):
        recommendations = st.session_state.lawyer_recommender.recommend_lawyers(
            user_location=st.session_state.user_location,
            legal_category=category,
            max_distance_km=50.0,
            top_n=5
        )

    if not recommendations:
        no_results_msg = st.session_state.lawyer_recommender.get_no_results_message(
            category_display,
            st.session_state.user_location
        )
        st.warning(no_results_msg)
        return

    st.success(f"Találtunk {len(recommendations)} ügyvédet az Ön közelében:")

    for i, rec in enumerate(recommendations, 1):
        lawyer = rec['lawyer']
        distance = rec['distance_km']

        with st.expander(f"**{i}. {lawyer['name']}** - {distance} km", expanded=(i==1)):
            col1, col2 = st.columns([2, 1])

            with col1:
                st.markdown(f"**📍 Cím:**")
                st.write(f"{lawyer['location']['address']}, {lawyer['location']['district']}")

                st.markdown(f"**💼 Szakosodás:**")
                st.write(", ".join(lawyer['specialization'][:4]))

                st.markdown(f"**⭐ Értékelés:**")
                st.write(f"{lawyer['rating']}/5.0 ({lawyer['reviews_count']} értékelés)")

            with col2:
                st.markdown(f"**📞 Telefon:**")
                st.write(lawyer['contact']['phone'])

                st.markdown(f"**✉️ Email:**")
                st.write(lawyer['contact']['email'])

                st.markdown(f"**💰 Konzultáció:**")
                st.write(lawyer['consultation_fee'])

                st.markdown(f"**🕐 Válaszidő:**")
                st.write(lawyer['response_time'])

            st.markdown(f"[🗺️ Megnyitás Google Maps-ben]({lawyer['contact']['google_maps_url']})")

            if lawyer['partnership_tier'] == 'premium':
                st.info("⭐ **Prémium Partner Ügyvéd**")

            st.caption(f"Relevancia pontszám: {rec['relevance_score']:.2f}")


# ============================================================================
# TAB 2: PDF ANALYZER
# ============================================================================

def render_pdf_tab():
    """Render the PDF analyzer tab"""
    st.markdown("### 📄 PDF Dokumentum Elemző")
    st.write("Töltsön fel egy PDF dokumentumot (szerződés, jogi irat), és az AI elemzi azt.")

    if not st.session_state.pdf_processor:
        st.warning("⚠️ PDF elemzés csak Anthropic API kulccsal érhető el. Állítsa be az ANTHROPIC_API_KEY környezeti változót.")
        return

    # File uploader
    uploaded_file = st.file_uploader(
        "📤 Töltsön fel egy PDF dokumentumot",
        type=["pdf"],
        accept_multiple_files=False,
        help="Maximum 10 MB méretű PDF fájl. Támogatott: szerződések, határozatok, jogi iratok."
    )

    if uploaded_file:
        st.session_state.pdf_file = uploaded_file

        # Display file info
        file_size_mb = uploaded_file.size / (1024 * 1024)
        st.info(f"📄 **Feltöltött fájl:** {uploaded_file.name} ({file_size_mb:.2f} MB)")

        # Analysis type selector
        analysis_type = st.radio(
            "Válassza ki az elemzés típusát:",
            options=[
                "Általános elemzés",
                "Szerződés elemzés (kötelezettségek kiemelése)",
                "Jogi dokumentum összegzés"
            ],
            help="Az AI az Ön által választott szempontok szerint elemzi a dokumentumot"
        )

        # Optional question
        user_question = st.text_input(
            "Konkrét kérdés a dokumentumról (opcionális):",
            placeholder="pl. 'Mikor jár le ez a szerződés?'"
        )

        # Analyze button
        if st.button("✓ Elemzés indítása", type="primary", use_container_width=True):
            # Save to temp file
            temp_pdf_path = f"temp_{uploaded_file.name}"
            with open(temp_pdf_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            try:
                with st.spinner("PDF elemzése folyamatban... Ez eltarthat néhány percig."):
                    result = st.session_state.pdf_processor.analyze_document(
                        temp_pdf_path,
                        user_question=user_question if user_question else None
                    )
                st.session_state.pdf_analysis = result

                # Clean up temp file
                os.remove(temp_pdf_path)

                st.success("✓ Elemzés kész!")
                st.rerun()

            except Exception as e:
                st.error(f"Hiba az elemzés során: {str(e)}")
                if os.path.exists(temp_pdf_path):
                    os.remove(temp_pdf_path)

    # Display analysis results
    if st.session_state.pdf_analysis:
        result = st.session_state.pdf_analysis

        st.markdown("---")
        st.markdown("## 🔍 Elemzés Eredménye")

        # Summary (always visible)
        with st.expander("🤖 AI Összegzés", expanded=True):
            st.markdown("### Összefoglaló")
            st.write(result.summary)

            if result.detailed_analysis:
                st.markdown("### Részletes Elemzés")
                st.write(result.detailed_analysis)

        # Key points
        if result.key_points:
            with st.expander("🔑 Kulcsfontosságú Pontok", expanded=True):
                for point in result.key_points:
                    st.markdown(f"- {point}")

        # Deadlines
        if result.deadlines:
            with st.expander("⏰ Határidők és Fontos Dátumok"):
                for deadline in result.deadlines:
                    st.warning(f"⏰ {deadline}")

        # Obligations
        if result.obligations:
            with st.expander("📋 Kötelezettségek"):
                for obligation in result.obligations:
                    st.markdown(f"- {obligation}")

        # Rights
        if result.rights:
            with st.expander("⚖️ Jogok"):
                for right in result.rights:
                    st.markdown(f"- {right}")

        # Next steps
        if result.next_steps:
            with st.expander("👉 Ajánlott Következő Lépések"):
                for step in result.next_steps:
                    st.markdown(f"{step}")

        # Document preview
        with st.expander("📄 Dokumentum Előnézet (első 1000 karakter)"):
            st.text_area(
                "",
                value=result.raw_text[:1000] + "..." if len(result.raw_text) > 1000 else result.raw_text,
                height=200,
                disabled=True
            )

        st.markdown("---")

        # PDF-specific chat
        st.markdown("### 💬 Kérdezzen a dokumentumról")
        pdf_question = st.chat_input("Tegyen fel kérdést erről a dokumentumról...")

        if pdf_question:
            st.session_state.pdf_chat_history.append({"role": "user", "content": pdf_question})

            # Re-analyze with specific question
            temp_pdf_path = f"temp_{st.session_state.pdf_file.name}"
            with open(temp_pdf_path, "wb") as f:
                f.write(st.session_state.pdf_file.getbuffer())

            with st.spinner("Válasz generálása..."):
                answer_result = st.session_state.pdf_processor.analyze_document(
                    temp_pdf_path,
                    user_question=pdf_question
                )

            os.remove(temp_pdf_path)

            st.session_state.pdf_chat_history.append({
                "role": "assistant",
                "content": answer_result.detailed_analysis or answer_result.summary
            })
            st.rerun()

        # Display PDF chat history
        for msg in st.session_state.pdf_chat_history:
            with st.chat_message(msg['role']):
                st.write(msg['content'])

        # Reset button
        if st.button("🗑️ Új Dokumentum Feltöltése", use_container_width=True):
            st.session_state.pdf_file = None
            st.session_state.pdf_analysis = None
            st.session_state.pdf_chat_history = []
            st.rerun()


# ============================================================================
# TAB 3: OFFICIAL LETTER INTERPRETER
# ============================================================================

def render_letter_tab():
    """Render the official letter interpreter tab"""
    st.markdown("### 📧 Hivatalos Levél Értelmező")
    st.write("Illessze be vagy töltsön fel egy hivatalos levelet, és az AI köznyelvűen elmagyarázza.")

    if not st.session_state.letter_interpreter:
        st.warning("⚠️ Levél értelmezés csak Anthropic API kulccsal érhető el. Állítsa be az ANTHROPIC_API_KEY környezeti változót.")
        return

    # Input method selector
    input_method = st.radio(
        "Válassza ki a beviteli módot:",
        options=["📝 Szöveg beillesztése", "📤 Fájl feltöltése"],
        horizontal=True
    )

    letter_text = None

    if input_method == "📝 Szöveg beillesztése":
        letter_text = st.text_area(
            "Illessze be a hivatalos levél szövegét:",
            height=250,
            placeholder="Illessze be ide a levél teljes szövegét...\n\nPélda:\nTisztelt Címzett!\n\nTájékoztatjuk, hogy...",
            help="Másolja be a teljes levél tartalmát a legjobb eredményért"
        )

    else:  # File upload
        uploaded_file = st.file_uploader(
            "Töltsön fel dokumentumot:",
            type=["pdf", "txt", "docx"],
            help="PDF, TXT vagy DOCX formátumú levelek"
        )

        if uploaded_file:
            # Save to temp file
            temp_file_path = f"temp_{uploaded_file.name}"
            with open(temp_file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            st.info(f"📄 **Feltöltött fájl:** {uploaded_file.name}")

    # Letter type selector (optional)
    letter_type = st.selectbox(
        "Levél típusa (segíti az elemzést):",
        options=[
            "-- Válasszon (opcionális) --",
            "⚖️ Bírósági értesítés/idézés",
            "🏛️ Hatósági levél",
            "💼 Munkaügyi értesítés",
            "💰 Adóügyi levél",
            "📋 Egyéb hivatalos levél"
        ]
    )

    # Interpret button
    if st.button("✓ Értelmezés indítása", type="primary", use_container_width=True):
        if not letter_text and not uploaded_file:
            st.error("Kérjük, adjon meg levél szöveget vagy töltsön fel fájlt!")
        else:
            try:
                with st.spinner("Levél elemzése folyamatban..."):
                    if letter_text:
                        result = st.session_state.letter_interpreter.interpret_letter(letter_text)
                    else:
                        result = st.session_state.letter_interpreter.interpret_from_file(temp_file_path)
                        os.remove(temp_file_path)

                st.session_state.letter_analysis = result
                st.session_state.letter_text = letter_text or uploaded_file.name

                st.success("✓ Értelmezés kész!")
                st.rerun()

            except Exception as e:
                st.error(f"Hiba az értelmezés során: {str(e)}")
                if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
                    os.remove(temp_file_path)

    # Display interpretation results
    if st.session_state.letter_analysis:
        result = st.session_state.letter_analysis

        st.markdown("---")
        st.markdown("## 📧 Levél Értelmezése")

        # Main summary box (always visible, prominent)
        st.markdown('<div class="summary-box">', unsafe_allow_html=True)
        st.markdown("### 🔍 Közérthető Összefoglaló")

        st.markdown("#### Mi a levél lényege")
        st.info(result.plain_language_summary)

        # Urgency indicator
        urgency_colors = {
            "alacsony": "🟢",
            "közepes": "🟡",
            "magas": "🟠",
            "kritikus": "🔴"
        }
        urgency_icon = urgency_colors.get(result.urgency_level.lower(), "⚪")
        st.markdown(f"**Sürgősség:** {urgency_icon} {result.urgency_level.upper()}")

        # Important dates
        if result.important_dates:
            st.markdown("#### Fontos határidők")
            for date in result.important_dates:
                st.error(f"⏰ {date}")

        # Your obligations
        if result.your_obligations:
            st.markdown("#### Mit kell tennie")
            for i, obligation in enumerate(result.your_obligations, 1):
                st.markdown(f"✓ {i}. {obligation}")

        # Consequences warning
        if result.detailed_explanation:
            st.markdown("#### Következmények, ha nem tesz lépést")
            st.warning(f"⚠️ {result.detailed_explanation[:200]}...")

        st.markdown('</div>', unsafe_allow_html=True)

        # Additional details in expanders
        with st.expander("📄 Eredeti levél szövege"):
            st.text_area("", value=result.raw_text, height=200, disabled=True)

        with st.expander("⚖️ Az Ön jogai"):
            if result.your_rights:
                for right in result.your_rights:
                    st.markdown(f"- {right}")
            else:
                st.write("Nincsenek kiemelten megnevezett jogok a levélben.")

        with st.expander("📋 Ajánlott lépések"):
            if result.recommended_actions:
                for action in result.recommended_actions:
                    st.markdown(f"- {action}")
            else:
                st.write("Nincsenek specifikus ajánlott lépések.")

        with st.expander("🔬 Részletes magyarázat"):
            st.write(result.detailed_explanation)

        st.markdown("---")

        # Letter-specific chat
        st.markdown("### 💬 Kérdezzen a levélről")
        letter_question = st.chat_input("Tegyen fel kérdést erről a levélről...")

        if letter_question:
            st.session_state.letter_chat_history.append({"role": "user", "content": letter_question})

            # Generate contextual answer
            with st.spinner("Válasz generálása..."):
                # Use RAG engine to answer based on letter context
                context_query = f"Levél kontextus: {result.plain_language_summary}\n\nKérdés: {letter_question}"
                rag_result = st.session_state.rag_engine.answer_query(context_query, n_results=3)

            st.session_state.letter_chat_history.append({
                "role": "assistant",
                "content": rag_result['answer']
            })
            st.rerun()

        # Display letter chat history
        for msg in st.session_state.letter_chat_history:
            with st.chat_message(msg['role']):
                st.write(msg['content'])

        # Reset button
        if st.button("🗑️ Új Levél Értelmezése", use_container_width=True):
            st.session_state.letter_text = None
            st.session_state.letter_analysis = None
            st.session_state.letter_chat_history = []
            st.rerun()


# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    """Main app logic"""
    # Initialize
    init_session_state()
    display_header()
    display_sidebar()

    # Initialize engines
    try:
        initialize_engines()
    except Exception as e:
        st.error(f"Inicializálási hiba: {e}")
        st.stop()

    # Tab navigation
    tab1, tab2, tab3 = st.tabs([
        "💬 Chat Asszisztens",
        "📄 PDF Elemző",
        "📧 Hivatalos Levél Értelmező"
    ])

    with tab1:
        render_chat_tab()

    with tab2:
        render_pdf_tab()

    with tab3:
        render_letter_tab()


if __name__ == "__main__":
    main()
