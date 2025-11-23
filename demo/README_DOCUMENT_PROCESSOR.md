# Dokumentum Feldolgozó Modul

**Jogi Asszisztens Demo - PDF és Dokumentum Elemző Backend**

## Áttekintés

Ez a modul kibővíti a meglévő RAG-alapú jogi asszisztens rendszert PDF dokumentumok és hivatalos levelek AI-alapú elemzésével és értelmezésével.

## Funkciók

### 1. PDFProcessor - PDF Dokumentum Elemző
- PDF fájlok szövegének automatikus kinyerése
- AI-alapú dokumentum elemzés (Claude 3 Haiku/Sonnet)
- Konkrét kérdések megválaszolása PDF tartalom alapján
- Strukturált eredmények: összefoglaló, kulcspontok, határidők, kötelezettségek

**Use Case-ek:**
- Szerződések elemzése
- Jogi dokumentumok áttekintése
- Munkaszerződések, bérleti szerződések értelmezése
- Bírósági iratok feldolgozása

### 2. OfficialLetterInterpreter - Hivatalos Levél Értelmező
- Hivatalos levelek köznyelvű magyarázata
- Automatikus dokumentum típus felismerés (bírósági, hatósági, munkaügyi, stb.)
- Határidők és kötelezettségek kiemelése
- Gyakorlati tanácsok generálása

**Use Case-ek:**
- Bírósági idézések értelmezése
- Hatósági értesítések megértése
- Munkaügyi levelek (felmondás, felszólítás) elemzése
- Közigazgatási határozatok értelmezése

## Telepítés

### 1. Függőségek telepítése

```bash
cd demo
pip install -r requirements.txt
```

Új csomagok:
- `pdfplumber>=0.10.0` - PDF feldolgozás
- `python-docx>=1.0.0` - Word dokumentumok olvasása

### 2. API Kulcs beállítása

```bash
# Linux/Mac
export ANTHROPIC_API_KEY="your-anthropic-api-key"

# Windows PowerShell
$env:ANTHROPIC_API_KEY="your-anthropic-api-key"

# Windows CMD
set ANTHROPIC_API_KEY=your-anthropic-api-key

# Vagy .env fájlban
echo "ANTHROPIC_API_KEY=your-key-here" >> .env
```

## Gyors Start

### PDF Elemzés

```python
from demo.document_processor import analyze_pdf

# Egyszerű használat
result = analyze_pdf("szerzodes.pdf")
print(result.summary)

# Konkrét kérdéssel
result = analyze_pdf(
    "szerzodes.pdf",
    question="Mikor jár le ez a szerződés?"
)
print(result.detailed_analysis)
```

### Hivatalos Levél Értelmezése

```python
from demo.document_processor import interpret_letter_file

# Fájlból (txt, docx)
result = interpret_letter_file("ertesites.txt")
print(f"Típus: {result.document_type.value}")
print(f"Összefoglaló: {result.plain_language_summary}")
print(f"Sürgősség: {result.urgency_level}")

# Fontos információk
for deadline in result.important_dates:
    print(f"Határidő: {deadline}")

for action in result.recommended_actions:
    print(f"Teendő: {action}")
```

### Szöveg Értelmezése

```python
from demo.document_processor import interpret_letter_text

letter = """
Tisztelt Kovács János!
Értesítjük, hogy munkaviszonya...
"""

result = interpret_letter_text(letter)
print(result.plain_language_summary)
```

## Fájl Struktúra

```
demo/
├── document_processor.py           # Fő modul
├── rag_engine.py                   # Meglévő RAG engine
├── app.py                          # Streamlit frontend (nem módosítva)
├── requirements.txt                # Frissített függőségek
├── test_document_processor.py      # Teszt szkript
├── DOCUMENT_PROCESSOR_USAGE.md     # Részletes használati útmutató
└── README_DOCUMENT_PROCESSOR.md    # Ez a fájl
```

## API Dokumentáció

### PDFProcessor

```python
class PDFProcessor:
    def __init__(self, llm_client, model="claude-3-haiku-20240307"):
        """
        Args:
            llm_client: anthropic.Anthropic instance
            model: Claude modell neve
        """

    def extract_text(self, pdf_source) -> str:
        """PDF szöveg kinyerése"""

    def analyze_document(
        self,
        pdf_source,
        user_question: Optional[str] = None,
        max_tokens: int = 2000
    ) -> DocumentAnalysisResult:
        """
        PDF dokumentum AI-alapú elemzése

        Returns:
            DocumentAnalysisResult with:
                - summary: str
                - detailed_analysis: str
                - document_type: str
                - key_points: List[str]
                - deadlines: List[str]
                - obligations: List[str]
                - rights: List[str]
                - next_steps: List[str]
                - raw_text: str
                - metadata: Dict
        """
```

### OfficialLetterInterpreter

```python
class OfficialLetterInterpreter:
    def __init__(self, llm_client, model="claude-3-haiku-20240307"):
        """
        Args:
            llm_client: anthropic.Anthropic instance
            model: Claude modell neve
        """

    def detect_document_type(self, text: str) -> DocumentType:
        """Automatikus dokumentum típus felismerés"""

    def interpret_from_file(self, file_path) -> LetterInterpretationResult:
        """Dokumentum értelmezése fájlból (txt, docx)"""

    def interpret_letter(self, text: str) -> LetterInterpretationResult:
        """
        Szöveg értelmezése

        Returns:
            LetterInterpretationResult with:
                - document_type: DocumentType
                - plain_language_summary: str
                - detailed_explanation: str
                - important_dates: List[str]
                - your_obligations: List[str]
                - your_rights: List[str]
                - recommended_actions: List[str]
                - urgency_level: str
                - raw_text: str
        """
```

### DocumentType Enum

```python
class DocumentType(Enum):
    BIROSAGI = "bírósági"
    HATOSAGI = "hatósági"
    MUNKAUGYI = "munkaügyi"
    SZERZODES = "szerződés"
    EGYEB = "egyéb hivatalos"
    ISMERETLEN = "ismeretlen"
```

## Integráció a RAG Engine-nel

```python
from demo.rag_engine import LegalRAGEngine
from demo.document_processor import PDFProcessor
import anthropic
import os

# Megosztott API kliens
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# RAG Engine (törvény keresés)
rag = LegalRAGEngine(
    laws_dir="data/laws",
    chroma_persist_dir="data/chroma_db",
    llm_provider="anthropic",
    api_key=os.getenv("ANTHROPIC_API_KEY")
)

# PDF Processzor
pdf_processor = PDFProcessor(llm_client=client)

# Komplex workflow
def analyze_with_legal_context(pdf_path):
    # 1. PDF elemzése
    doc_result = pdf_processor.analyze_document(pdf_path)

    # 2. Releváns törvények keresése
    query = " ".join(doc_result.key_points[:2])
    law_result = rag.answer_query(query)

    return {
        "document_analysis": doc_result,
        "relevant_laws": law_result
    }
```

## Tesztelés

```bash
# Teszt futtatása
python demo/test_document_processor.py

# Valós AI teszthez API kulcs szükséges
export ANTHROPIC_API_KEY="your-key"
python demo/test_document_processor.py
```

## Támogatott Formátumok

- **PDF**: .pdf (pdfplumber)
- **Word**: .docx (python-docx)
- **Text**: .txt (natív)
- **String**: Közvetlenül szövegként

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
export ANTHROPIC_API_KEY="sk-ant-..."
```

### PDF üres szöveget ad vissza
- Ellenőrizd, hogy a PDF nem védett-e
- Ha képeket tartalmaz, OCR szükséges (pytesseract)

## Költségek és Teljesítmény

### Modellek
- **claude-3-haiku-20240307**: Gyors, olcsó, ajánlott
- **claude-3-sonnet-20240229**: Pontosabb, drágább

### Token használat
- Átlagos PDF (10 oldal): ~5000-8000 token
- Hivatalos levél: ~1000-3000 token
- Válasz generálás: ~500-2000 token

### Optimalizálás
```python
# Rövidebb válasz
result = processor.analyze_document("doc.pdf", max_tokens=1000)

# Gyorsabb modell
processor = PDFProcessor(client, model="claude-3-haiku-20240307")
```

## Biztonsági Megjegyzések

1. **API kulcs védelem**: Soha ne commitold a kódba
2. **Érzékeny adatok**: A dokumentumok tartalma elküldésre kerül az Anthropic API-hoz
3. **Adatvédelem**: Biztosítsd, hogy megfeleljen a GDPR-nak

## Limitációk

1. **Nem jogi tanácsadás**: Csak tájékoztatás, nem helyettesít ügyvédet
2. **OCR hiánya**: Csak szöveges PDF-ek, képek nem támogatottak
3. **Nyelv**: Elsősorban magyar dokumentumokra optimalizálva
4. **Méret**: Nagy dokumentumok (100+ oldal) lassabbak és drágábbak

## Következő Lépések

1. **Streamlit integráció**: Frissítsd az `app.py`-t UI-val
2. **OCR támogatás**: pytesseract integráció képes PDF-ekhez
3. **Batch processing**: Több dokumentum párhuzamos feldolgozása
4. **Cache**: Ismételt elemzések gyorsítótárazása

## Részletes Dokumentáció

- **Használati útmutató**: `DOCUMENT_PROCESSOR_USAGE.md`
- **API referencia**: Docstringek a `document_processor.py`-ban
- **Példakódok**: `test_document_processor.py`

## Licensz

Ugyanaz, mint a projekt többi része.

## Kapcsolat és Támogatás

Ez egy demo projekt a RAG-alapú jogi asszisztens kibővítésére.

---

**Verzió**: 1.0.0
**Létrehozva**: 2024
**Claude Model**: claude-3-haiku-20240307 (alapértelmezett)
