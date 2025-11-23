# Dokumentum Feldolgozó Modul - Használati Útmutató

## Áttekintés

A `document_processor.py` modul két fő funkciót biztosít:

1. **PDFProcessor** - PDF dokumentumok elemzése és AI-alapú értelmezése
2. **OfficialLetterInterpreter** - Hivatalos levelek köznyelvű magyarázata

## Telepítés

```bash
# Telepítsd a szükséges csomagokat
pip install -r requirements.txt

# Vagy manuálisan:
pip install pdfplumber python-docx anthropic
```

## Környezeti Változók

```bash
# .env fájl vagy környezeti változó
export ANTHROPIC_API_KEY="your-anthropic-api-key"
```

## 1. PDF Processzor Használata

### Alapvető Használat

```python
from demo.document_processor import PDFProcessor
import anthropic
import os

# Anthropic kliens inicializálása
api_key = os.getenv("ANTHROPIC_API_KEY")
client = anthropic.Anthropic(api_key=api_key)

# PDF processzor létrehozása
processor = PDFProcessor(llm_client=client)

# PDF elemzése
result = processor.analyze_document("szerződés.pdf")

# Eredmények
print(f"Dokumentum típus: {result.document_type}")
print(f"Összefoglaló: {result.summary}")
print("\nKulcs pontok:")
for point in result.key_points:
    print(f"  - {point}")

print("\nHatáridők:")
for deadline in result.deadlines:
    print(f"  - {deadline}")
```

### PDF Elemzése Konkrét Kérdéssel

```python
# Konkrét kérdés a dokumentumról
result = processor.analyze_document(
    "munkaszerződés.pdf",
    user_question="Mikor jár le ez a szerződés és milyen felmondási határidő van?"
)

print(result.detailed_analysis)
```

### File Object Használata (pl. Streamlit Upload)

```python
# Streamlit file upload példa
import streamlit as st

uploaded_file = st.file_uploader("Tölts fel PDF-et", type="pdf")

if uploaded_file:
    result = processor.analyze_document(uploaded_file)
    st.write(result.summary)
```

### Egyszerűsített Használat (Helper Function)

```python
from demo.document_processor import analyze_pdf

# Egy lépésben, API kulcs környezeti változóból
result = analyze_pdf(
    "document.pdf",
    question="Mi a fő tartalma ennek a dokumentumnak?"
)

print(result.detailed_analysis)
```

## 2. Hivatalos Levél Értelmező Használata

### Alapvető Használat - Szöveges Fájl

```python
from demo.document_processor import OfficialLetterInterpreter
import anthropic
import os

# Kliens inicializálása
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Interpreter létrehozása
interpreter = OfficialLetterInterpreter(llm_client=client)

# TXT fájl értelmezése
result = interpreter.interpret_from_file("bírósági_idézés.txt")

print(f"Dokumentum típus: {result.document_type.value}")
print(f"\nKöznyelvű összefoglaló:\n{result.plain_language_summary}")
print(f"\nSürgősség: {result.urgency_level}")

print("\nFontos dátumok:")
for date in result.important_dates:
    print(f"  - {date}")

print("\nMit kell tenned:")
for obligation in result.your_obligations:
    print(f"  - {obligation}")

print("\nMire vagy jogosult:")
for right in result.your_rights:
    print(f"  - {right}")

print("\nAjánlott lépések:")
for action in result.recommended_actions:
    print(f"  - {action}")
```

### Word Dokumentum Értelmezése

```python
# DOCX fájl értelmezése
result = interpreter.interpret_from_file("felmondás.docx")

print(result.plain_language_summary)
```

### Direkt Szöveg Értelmezése

```python
# Ha már van szöveged (pl. másolt levél)
letter_text = """
Tisztelt Kovács János!

Tájékoztatjuk, hogy munkaviszonya a 2024. február 29-i dátummal
megszűnik. Végkielégítésre nem jogosult...
"""

result = interpreter.interpret_letter(letter_text)
print(result.plain_language_summary)
```

### Dokumentum Típus Automatikus Felismerése

```python
# Típus automatikus detektálása
doc_type = interpreter.detect_document_type(letter_text)
print(f"Felismert típus: {doc_type.value}")

# Lehetséges típusok:
# - DocumentType.BIROSAGI (bírósági)
# - DocumentType.HATOSAGI (hatósági)
# - DocumentType.MUNKAUGYI (munkaügyi)
# - DocumentType.SZERZODES (szerződés)
# - DocumentType.EGYEB (egyéb hivatalos)
# - DocumentType.ISMERETLEN (ismeretlen)
```

### Egyszerűsített Használat (Helper Functions)

```python
from demo.document_processor import interpret_letter_file, interpret_letter_text

# Fájlból
result = interpret_letter_file("értesítés.txt")

# Szövegből
result = interpret_letter_text("Levél szövege...")

print(result.plain_language_summary)
```

## 3. Integráció a RAG Engine-nel

```python
from demo.rag_engine import LegalRAGEngine
from demo.document_processor import PDFProcessor
import anthropic
import os

# Megosztott Anthropic kliens
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# RAG Engine (törvény keresés)
rag = LegalRAGEngine(
    laws_dir="data/laws",
    chroma_persist_dir="data/chroma_db",
    llm_provider="anthropic",
    api_key=os.getenv("ANTHROPIC_API_KEY")
)

# PDF Processor (dokumentum elemzés)
pdf_processor = PDFProcessor(llm_client=client)

# Workflow: Dokumentum elemzése + Releváns törvények keresése
def analyze_with_legal_context(pdf_path):
    # 1. Elemezd a dokumentumot
    doc_result = pdf_processor.analyze_document(pdf_path)

    print(f"Dokumentum: {doc_result.document_type}")
    print(f"Összefoglaló: {doc_result.summary}")

    # 2. Keress releváns törvényeket a dokumentum alapján
    if doc_result.key_points:
        query = " ".join(doc_result.key_points[:2])
        law_result = rag.answer_query(query)

        print(f"\nReleváns törvények:")
        print(law_result['answer'])

    return doc_result, law_result

# Használat
doc_result, law_result = analyze_with_legal_context("szerződés.pdf")
```

## 4. Streamlit Integráció Példa

```python
import streamlit as st
from demo.document_processor import PDFProcessor, OfficialLetterInterpreter
import anthropic
import os

st.title("Dokumentum Elemző")

# Kliens inicializálása
@st.cache_resource
def get_anthropic_client():
    return anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

client = get_anthropic_client()

# Tab választó
tab1, tab2 = st.tabs(["PDF Elemző", "Levél Értelmező"])

with tab1:
    st.header("PDF Dokumentum Elemzés")

    uploaded_pdf = st.file_uploader("Tölts fel PDF-et", type="pdf", key="pdf")
    question = st.text_input("Opcionális kérdés a dokumentumról:")

    if uploaded_pdf and st.button("Elemzés"):
        with st.spinner("PDF feldolgozása..."):
            processor = PDFProcessor(llm_client=client)
            result = processor.analyze_document(
                uploaded_pdf,
                user_question=question if question else None
            )

        st.success("Elemzés kész!")

        st.subheader("Összefoglaló")
        st.write(result.summary)

        st.subheader("Dokumentum Típus")
        st.info(result.document_type)

        if result.key_points:
            st.subheader("Kulcs Pontok")
            for point in result.key_points:
                st.write(f"- {point}")

        if result.deadlines:
            st.subheader("Határidők")
            for deadline in result.deadlines:
                st.warning(deadline)

        with st.expander("Részletes Elemzés"):
            st.write(result.detailed_analysis)

with tab2:
    st.header("Hivatalos Levél Értelmező")

    input_method = st.radio("Bevitel módja:", ["Fájl feltöltés", "Szöveg bemásolása"])

    if input_method == "Fájl feltöltés":
        uploaded_file = st.file_uploader(
            "Tölts fel dokumentumot",
            type=["txt", "docx"],
            key="letter"
        )

        if uploaded_file and st.button("Értelmezés"):
            with st.spinner("Dokumentum értelmezése..."):
                interpreter = OfficialLetterInterpreter(llm_client=client)

                # Szöveg kinyerése típus szerint
                if uploaded_file.name.endswith('.txt'):
                    text = uploaded_file.read().decode('utf-8')
                else:
                    # Ideiglenes fájlba mentés docx-hez
                    import tempfile
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as tmp:
                        tmp.write(uploaded_file.read())
                        tmp_path = tmp.name
                    result = interpreter.interpret_from_file(tmp_path)
                    os.unlink(tmp_path)
                    text = None

                if text:
                    result = interpreter.interpret_letter(text)

            display_letter_result(st, result)

    else:
        letter_text = st.text_area("Másold be a levél szövegét:", height=300)

        if letter_text and st.button("Értelmezés"):
            with st.spinner("Levél értelmezése..."):
                interpreter = OfficialLetterInterpreter(llm_client=client)
                result = interpreter.interpret_letter(letter_text)

            display_letter_result(st, result)

def display_letter_result(st, result):
    st.success("Értelmezés kész!")

    st.subheader("Dokumentum Típus")
    st.info(result.document_type.value)

    st.subheader("Köznyelvű Összefoglaló")
    st.write(result.plain_language_summary)

    st.subheader("Sürgősség")
    urgency_color = {
        "alacsony": "green",
        "közepes": "orange",
        "magas": "red",
        "kritikus": "red"
    }
    # Dinamikus színezés a sürgősség alapján
    st.markdown(f"**{result.urgency_level}**")

    if result.important_dates:
        st.subheader("Fontos Dátumok")
        for date in result.important_dates:
            st.warning(date)

    col1, col2 = st.columns(2)

    with col1:
        if result.your_obligations:
            st.subheader("Mit Kell Tenned")
            for obligation in result.your_obligations:
                st.write(f"- {obligation}")

    with col2:
        if result.your_rights:
            st.subheader("Mire Vagy Jogosult")
            for right in result.your_rights:
                st.write(f"- {right}")

    if result.recommended_actions:
        st.subheader("Ajánlott Lépések")
        for action in result.recommended_actions:
            st.success(f"✓ {action}")

    with st.expander("Részletes Magyarázat"):
        st.write(result.detailed_explanation)
```

## 5. Hibakezelés

```python
from demo.document_processor import PDFProcessor
import anthropic

try:
    client = anthropic.Anthropic(api_key="invalid-key")
    processor = PDFProcessor(llm_client=client)
    result = processor.analyze_document("nem_létező.pdf")

except FileNotFoundError as e:
    print(f"Fájl nem található: {e}")

except ValueError as e:
    print(f"Érvénytelen adat: {e}")

except ImportError as e:
    print(f"Hiányzó csomag: {e}")

except RuntimeError as e:
    print(f"AI feldolgozási hiba: {e}")

except Exception as e:
    print(f"Általános hiba: {e}")
```

## 6. Teljesítmény és Költség Optimalizálás

```python
# Rövidebb válasz kevesebb token költséggel
result = processor.analyze_document(
    "document.pdf",
    max_tokens=1000  # Alapértelmezett: 2000
)

# Gyorsabb modell használata (olcsóbb)
processor = PDFProcessor(
    llm_client=client,
    model="claude-3-haiku-20240307"  # Haiku: gyors és olcsó
)

# Lassabb de pontosabb modell
processor = PDFProcessor(
    llm_client=client,
    model="claude-3-sonnet-20240229"  # Sonnet: jobb minőség
)
```

## Fontos Megjegyzések

1. **API Kulcs**: Mindig használj környezeti változót az API kulcshoz
2. **Költségek**: Haiku modell ajánlott (gyors és olcsó), nagyobb dokumentumokhoz Sonnet
3. **PDF Képek**: Ha a PDF csak képeket tartalmaz, az OCR nincs beépítve
4. **Hibakezelés**: Mindig használj try-except blokkokat
5. **Nem jogi tanácsadás**: A modul csak tájékoztatást nyújt, nem helyettesít ügyvédet

## Támogatott Fájl Formátumok

- **PDF**: .pdf (pdfplumber könyvtár)
- **Word**: .docx (python-docx könyvtár)
- **Szöveg**: .txt (natív Python)
- **Plain text**: Közvetlenül string-ként

## Hibaelhárítás

### "pdfplumber not found"
```bash
pip install pdfplumber
```

### "python-docx not found"
```bash
pip install python-docx
```

### "ANTHROPIC_API_KEY not set"
```bash
export ANTHROPIC_API_KEY="your-key-here"
# vagy .env fájlban
echo "ANTHROPIC_API_KEY=your-key" >> .env
```

### PDF nem olvasható
- Ellenőrizd, hogy a PDF nem védett-e jelszóval
- Próbálj más PDF olvasó könyvtárat (PyPDF2)
- Ha csak képeket tartalmaz, szükséges OCR (pl. pytesseract)

## További Információk

- Anthropic API dokumentáció: https://docs.anthropic.com
- pdfplumber: https://github.com/jsvine/pdfplumber
- python-docx: https://python-docx.readthedocs.io
