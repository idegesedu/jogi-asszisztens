import streamlit as st
import os
from pathlib import Path
from dotenv import load_dotenv  # 

load_dotenv()  #

# Import custom modules
from rag_engine import LegalRAGEngine
...

"""
Jogi Asszisztens Demo - Streamlit UI
Befektetői bemutató verzió
"""

import streamlit as st
import os
from pathlib import Path

# Import custom modules
from rag_engine import LegalRAGEngine
from lawyer_recommender import LawyerRecommender
from geolocation import (
    get_user_location_from_ip,
    parse_location_input,
    get_location_display_name,
    get_default_location
)

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
    .lawyer-card {
        border: 2px solid #E2E8F0;
        border-radius: 10px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        background-color: #F8FAFC;
    }
    .disclaimer {
        background-color: #FEF3C7;
        border-left: 4px solid #F59E0B;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 5px;
    }
    .chat-message {
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 10px;
    }
    .user-message {
        background-color: #DBEAFE;
        text-align: right;
    }
    .assistant-message {
        background-color: #F3F4F6;
    }
</style>
""", unsafe_allow_html=True)


# Initialize session state
def init_session_state():
    """Initialize Streamlit session state variables"""
    if 'initialized' not in st.session_state:
        st.session_state.initialized = True
        st.session_state.rag_engine = None
        st.session_state.lawyer_recommender = None
        st.session_state.chat_history = []
        st.session_state.show_lawyer_request = False
        st.session_state.user_location = None
        st.session_state.detected_category = None
        st.session_state.last_answer = None


def initialize_engines():
    """Initialize RAG and Lawyer Recommender (cached)"""
    if st.session_state.rag_engine is None:
        with st.spinner("RAG Engine inicializálása..."):
            # Check for API key
            api_key = os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")

            if not api_key:
                st.error("API kulcs nem található! Állítsd be az OPENAI_API_KEY vagy ANTHROPIC_API_KEY környezeti változót.")
                st.stop()

            # Determine provider
            provider = "openai" if os.getenv("OPENAI_API_KEY") else "anthropic"

            st.session_state.rag_engine = LegalRAGEngine(
                laws_dir="data/laws",
                chroma_persist_dir="data/chroma_db",
                llm_provider=provider,
                api_key=api_key
            )

            # Load and index laws (first time only)
            st.session_state.rag_engine.load_and_index_laws(force_reload=False)

    if st.session_state.lawyer_recommender is None:
        st.session_state.lawyer_recommender = LawyerRecommender("data/lawyers.json")


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
    """Display sidebar with info and stats"""
    with st.sidebar:
        st.title("📊 Demo Információk")

        st.markdown("### 🎯 Funkciók")
        st.markdown("""
        - ✅ **RAG-alapú válaszok**: Magyar törvényekből citál
        - ✅ **Esetazonosítás**: Automatikus kategorizálás
        - ✅ **Ügyvéd-ajánlás**: Lokáció-alapú, opt-in
        - ✅ **6 törvény**: BTK, Ptk, Be, Rtv, Fgy.tv, Alaptörvény
        """)

        st.markdown("### 📚 Elérhető Jogi Területek")
        st.markdown("""
        - 💼 Munkajog (felmondás, végkielégítés)
        - 🛒 Fogyasztóvédelem (reklamáció, jótállás)
        - 👨‍👩‍👧 Családjog
        - 🏠 Ingatlanjog
        - ⚖️ Büntetőjog
        """)

        st.markdown("### 🏢 Mock Ügyvédi Adatbázis")
        if st.session_state.lawyer_recommender:
            lawyer_count = len(st.session_state.lawyer_recommender.lawyers)
            st.info(f"{lawyer_count} budapesti ügyvédi iroda")

        st.markdown("---")
        st.markdown("### 🚀 Befektetői Demo")
        st.markdown("Verzió: 1.0")
        st.markdown("Dátum: 2025. november")


def display_chat_history():
    """Display chat history"""
    for message in st.session_state.chat_history:
        if message['role'] == 'user':
            st.markdown(f'<div class="chat-message user-message">👤 **Ön:** {message["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="chat-message assistant-message">🤖 **Asszisztens:**\n\n{message["content"]}</div>', unsafe_allow_html=True)


def handle_user_query(query: str):
    """Handle user legal question"""
    # Add user message to history
    st.session_state.chat_history.append({
        "role": "user",
        "content": query
    })

    # Get RAG answer
    with st.spinner("Válasz generálása... (RAG + LLM)"):
        result = st.session_state.rag_engine.answer_query(query, n_results=5)

    # Store result
    st.session_state.last_answer = result
    st.session_state.detected_category = result['detected_category']

    # Add assistant message to history
    st.session_state.chat_history.append({
        "role": "assistant",
        "content": result['answer']
    })

    # Show lawyer request button
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

    # Auto-detect option
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
    """Display lawyer recommendations based on location and category"""
    if not st.session_state.user_location:
        return

    st.markdown("---")
    st.markdown("### 🏢 Ajánlott Ügyvédek")

    location_name = get_location_display_name(st.session_state.user_location)
    category = st.session_state.detected_category or "általános"
    category_display = st.session_state.lawyer_recommender.get_category_display_name(category)

    st.write(f"**Terület:** {category_display}")
    st.write(f"**Helyszín:** {location_name}")

    # Get recommendations
    with st.spinner("Ügyvédek keresése..."):
        recommendations = st.session_state.lawyer_recommender.recommend_lawyers(
            user_location=st.session_state.user_location,
            legal_category=category,
            max_distance_km=50.0,
            top_n=5
        )

    if not recommendations:
        # No results message
        no_results_msg = st.session_state.lawyer_recommender.get_no_results_message(
            category_display,
            st.session_state.user_location
        )
        st.warning(no_results_msg)
        return

    # Display recommendations
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

            # Google Maps link
            st.markdown(f"[🗺️ Megnyitás Google Maps-ben]({lawyer['contact']['google_maps_url']})")

            if lawyer['partnership_tier'] == 'premium':
                st.info("⭐ **Prémium Partner Ügyvéd**")

            # Relevance score (for demo purposes)
            st.caption(f"Relevancia pontszám: {rec['relevance_score']:.2f} (távolság + értékelés + szakosodás)")


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

    # Main chat interface
    st.markdown("### 💬 Hogyan segíthetek?")
    st.write("Írja le jogi kérdését vagy problémáját, és én megpróbálok segíteni a magyar jogszabályok alapján!")

    # Chat history
    display_chat_history()

    # User input
    user_query = st.chat_input("Például: 'Jogellenes a felmondásom? Nem kaptam végkielégítést.'")

    if user_query:
        handle_user_query(user_query)
        st.rerun()

    # Lawyer recommendation flow
    if st.session_state.show_lawyer_request and not st.session_state.get('show_lawyer_location'):
        display_lawyer_request_prompt()

    if st.session_state.get('show_lawyer_location'):
        if not st.session_state.user_location:
            display_location_request()
        else:
            display_lawyer_recommendations()

            # Option to reset
            if st.button("🔄 Új kérdés", use_container_width=True):
                st.session_state.show_lawyer_request = False
                st.session_state.show_lawyer_location = False
                st.session_state.user_location = None
                st.rerun()


if __name__ == "__main__":
    main()
