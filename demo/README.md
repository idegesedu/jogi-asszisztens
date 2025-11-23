# Jogi Asszisztens MI - Befektetői Demo

Egy önálló, folyamatosan tanuló jogi mesterséges intelligencia alkalmazás demonstrációja.

## 🎯 Funkciók

- **RAG-alapú válaszok**: Magyar törvények citálása és kontextuális válaszok
- **Esetazonosítás**: Automatikus jogi kategória felismerés
- **Ügyvéd-ajánlás**: Lokáció-alapú, opt-in rendszerű szakértő ajánlás
- **6 törvény adatbázis**: BTK, Ptk, Be, Rtv, Fogyasztóvédelem, Alaptörvény

## 📋 Követelmények

- Python 3.9+
- OpenAI vagy Anthropic API kulcs

## 🚀 Telepítés

### 1. Python környezet

```bash
# Virtual environment létrehozása
python -m venv venv

# Aktiválás (Windows)
venv\Scripts\activate

# Aktiválás (Mac/Linux)
source venv/bin/activate
```

### 2. Függőségek telepítése

```bash
pip install -r requirements.txt
```

### 3. API kulcs beállítása

Hozz létre egy `.env` fájlt a `demo/` mappában:

```
# OpenAI (ajánlott)
OPENAI_API_KEY=your-openai-api-key-here

# VAGY Anthropic
# ANTHROPIC_API_KEY=your-anthropic-api-key-here
```

**API kulcsok beszerzése:**
- OpenAI: https://platform.openai.com/api-keys
- Anthropic: https://console.anthropic.com/

## ▶️ Futtatás

```bash
cd demo
streamlit run app.py
```

Az alkalmazás elindul a böngészőben: `http://localhost:8501`

## 📁 Projekt Struktúra

```
demo/
├── app.py                    # Streamlit UI (fő alkalmazás)
├── rag_engine.py            # RAG motor (ChromaDB + LLM)
├── lawyer_recommender.py    # Ügyvéd ajánló rendszer
├── geolocation.py          # Lokáció kezelés
├── requirements.txt         # Python függőségek
├── data/
│   ├── laws/               # Törvények (Markdown)
│   │   ├── BTK_clean.md
│   │   ├── Ptk_clean.md
│   │   ├── Be_clean.md
│   │   ├── Rtv_clean.md
│   │   ├── Fgy_tv_clean.md
│   │   └── alaptörvény.md
│   ├── lawyers.json        # Mock ügyvédi adatbázis
│   └── chroma_db/          # Vector DB (automatikusan generálódik)
└── README.md
```

## 🎬 Demo Használat

### 1. Első indítás

Az első indításkor az alkalmazás:
- Betölti a törvényeket
- Generál embedding-eket (2-3 perc)
- Létrehozza a ChromaDB adatbázist

### 2. Kérdés feltevése

Példa kérdések:
- "Jogellenes a felmondásom? Nem kaptam végkielégítést."
- "Reklamálni szeretnék egy hibás terméket. Mik a jogaim?"
- "Mikor jár jótállás és mikor garancia?"

### 3. Ügyvéd-ajánlás

- A válasz után megjelenik: "Szeretne ügyvédi segítséget?"
- Ha **Igen**: megadhatja a lokációt (automatikus vagy manuális)
- Az alkalmazás ajánl 3-5 közeli szakosodott ügyvédet

## 🧪 Teszt Adatok

### Mock Ügyvédek
- 18 budapesti ügyvédi iroda
- Valósághű adatok: név, cím, telefon, értékelés, árak
- Különböző szakosodások: munkajog, fogyasztóvédelem, családjog

### Törvények
- **BTK**: Büntető Törvénykönyv (520 KB)
- **Ptk**: Polgári Törvénykönyv (1.2 MB)
- **Be**: Büntetőeljárási törvény (1.3 MB)
- **Rtv**: Rendőrségi törvény (368 KB)
- **Fgy.tv**: Fogyasztóvédelmi törvény (204 KB)
- **Alaptörvény**: Magyarország Alaptörvénye (134 KB)

## ⚠️ Disclaimer

Ez egy **befektetői demo verzió** demonstrációs célokra.

**NEM production-ready**:
- Mock ügyvédi adatok
- Nincs user authentication
- Nincs persistence (chat history nem mentődik)
- Korlátozott error handling
- Nincsenek analytics

**A teljes verzióhoz szükséges:**
- Valódi ügyvédi integráció
- User account rendszer
- Feedback loop implementáció
- Admin dashboard
- Production deployment (Kubernetes)

## 🔧 Troubleshooting

### "ChromaDB version mismatch" hiba

```bash
pip install --upgrade chromadb
```

### "API key not found" hiba

Ellenőrizd, hogy:
1. Van `.env` fájl a `demo/` mappában
2. Az API kulcs helyes
3. A Python environment aktiválva van

### "No module named 'sentence_transformers'" hiba

```bash
pip install sentence-transformers
```

### Lassú első indítás

Normális! Az első indításkor:
- 6 törvényt dolgoz fel (~3.6 MB)
- Generál embedding-eket
- Indexel ChromaDB-be

Második indítástól gyors lesz (cached).

## 📊 Teljesítmény

- **Első indítás**: 2-3 perc (indexing)
- **Válaszidő**: 3-5 másodperc (RAG + LLM)
- **Memória**: ~500 MB (ChromaDB + models)
- **Disk**: ~1 GB (models + vector DB)

## 📞 Support

Kérdések vagy hibák esetén:
- Email: [your-email@example.com]
- GitHub Issues: [repo-link]

## 📄 Licenc

Ez a demo kód demonstration purposes only.

---

**Készítette**: Jogi Asszisztens Csapat
**Verzió**: 1.0 (Befektetői Demo)
**Dátum**: 2025. november
