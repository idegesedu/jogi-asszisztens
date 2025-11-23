"""
Dokumentum Feldolgozó Modul - PDF és Hivatalos Levelek Elemzése
Jogi dokumentumok, szerződések, hivatalos levelek AI-alapú elemzése és értelmezése
"""

import os
import re
from typing import Dict, List, Optional, Union, BinaryIO
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

# PDF feldolgozás
try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False

# Word dokumentum feldolgozás
try:
    from docx import Document
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False

# AI integráció (Anthropic Claude)
try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False


class DocumentType(Enum):
    """Hivatalos dokumentumok típusai"""
    BIROSAGI = "bírósági"
    HATOSAGI = "hatósági"
    MUNKAUGYI = "munkaügyi"
    SZERZODES = "szerződés"
    EGYEB = "egyéb hivatalos"
    ISMERETLEN = "ismeretlen"


@dataclass
class DocumentAnalysisResult:
    """Dokumentum elemzés eredménye"""
    summary: str
    detailed_analysis: str
    document_type: str
    key_points: List[str]
    deadlines: List[str]
    obligations: List[str]
    rights: List[str]
    next_steps: List[str]
    raw_text: str
    metadata: Dict


@dataclass
class LetterInterpretationResult:
    """Hivatalos levél értelmezés eredménye"""
    document_type: DocumentType
    plain_language_summary: str
    detailed_explanation: str
    important_dates: List[str]
    your_obligations: List[str]
    your_rights: List[str]
    recommended_actions: List[str]
    urgency_level: str
    raw_text: str


class PDFProcessor:
    """
    PDF dokumentumok feldolgozása és AI-alapú elemzése

    Használat:
    ---------
    >>> from demo.document_processor import PDFProcessor
    >>> import anthropic
    >>>
    >>> # Anthropic kliens inicializálása
    >>> client = anthropic.Anthropic(api_key="your-api-key")
    >>>
    >>> # PDF processzor létrehozása
    >>> processor = PDFProcessor(llm_client=client)
    >>>
    >>> # PDF elemzése fájl úttal
    >>> result = processor.analyze_document("contract.pdf")
    >>> print(result.summary)
    >>> print(result.key_points)
    >>>
    >>> # PDF elemzése konkrét kérdéssel
    >>> result = processor.analyze_document(
    ...     "contract.pdf",
    ...     user_question="Mikor jár le ez a szerződés?"
    ... )
    >>> print(result.detailed_analysis)
    """

    def __init__(self, llm_client: 'anthropic.Anthropic', model: str = "claude-3-haiku-20240307"):
        """
        Inicializálás

        Args:
            llm_client: Anthropic API kliens (anthropic.Anthropic instance)
            model: Claude modell neve
        """
        if not HAS_ANTHROPIC:
            raise ImportError("Az anthropic csomag nincs telepítve. Telepítsd: pip install anthropic")

        if not HAS_PDFPLUMBER:
            raise ImportError("A pdfplumber csomag nincs telepítve. Telepítsd: pip install pdfplumber")

        self.llm_client = llm_client
        self.model = model

    def extract_text(self, pdf_source: Union[str, Path, BinaryIO]) -> str:
        """
        Szöveg kinyerése PDF fájlból

        Args:
            pdf_source: PDF fájl útvonala (str/Path) vagy file object (BinaryIO)

        Returns:
            Kinyert szöveg

        Raises:
            FileNotFoundError: Ha a fájl nem található
            ValueError: Ha a PDF üres vagy nem olvasható
        """
        try:
            with pdfplumber.open(pdf_source) as pdf:
                if len(pdf.pages) == 0:
                    raise ValueError("A PDF fájl üres (0 oldal)")

                text_parts = []
                for page_num, page in enumerate(pdf.pages, 1):
                    page_text = page.extract_text()
                    if page_text:
                        # Oldal elválasztó
                        text_parts.append(f"\n--- {page_num}. oldal ---\n")
                        text_parts.append(page_text)

                full_text = "\n".join(text_parts)

                if not full_text.strip():
                    raise ValueError("Nem sikerült szöveget kinyerni a PDF-ből (lehet, hogy csak képeket tartalmaz)")

                return self._clean_text(full_text)

        except FileNotFoundError:
            raise FileNotFoundError(f"A PDF fájl nem található: {pdf_source}")
        except Exception as e:
            raise ValueError(f"Hiba történt a PDF feldolgozása során: {str(e)}")

    def _clean_text(self, text: str) -> str:
        """Szöveg tisztítása és normalizálása"""
        # Több egymást követő whitespace-t egyetlen space-re
        text = re.sub(r'\s+', ' ', text)
        # Felesleges sortörések eltávolítása
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        return text.strip()

    def analyze_document(
        self,
        pdf_source: Union[str, Path, BinaryIO],
        user_question: Optional[str] = None,
        max_tokens: int = 2000
    ) -> DocumentAnalysisResult:
        """
        PDF dokumentum AI-alapú elemzése

        Args:
            pdf_source: PDF fájl forrása
            user_question: Opcionális konkrét kérdés a dokumentummal kapcsolatban
            max_tokens: Maximum token szám a válaszhoz

        Returns:
            DocumentAnalysisResult objektum az elemzés eredményével

        Példa:
        ------
        >>> result = processor.analyze_document("szerzodes.pdf")
        >>> print(f"Típus: {result.document_type}")
        >>> print(f"Összefoglaló: {result.summary}")
        >>> for deadline in result.deadlines:
        ...     print(f"Határidő: {deadline}")
        """
        # Szöveg kinyerése
        raw_text = self.extract_text(pdf_source)

        # Prompt összeállítása
        if user_question:
            system_prompt = self._get_qa_system_prompt()
            user_prompt = self._build_qa_prompt(raw_text, user_question)
        else:
            system_prompt = self._get_analysis_system_prompt()
            user_prompt = self._build_analysis_prompt(raw_text)

        # AI hívás
        try:
            message = self.llm_client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=0.2,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )

            response_text = message.content[0].text

            # Válasz feldolgozása
            return self._parse_analysis_response(response_text, raw_text, user_question)

        except Exception as e:
            raise RuntimeError(f"Hiba történt az AI elemzés során: {str(e)}")

    def _get_analysis_system_prompt(self) -> str:
        """Rendszer prompt általános dokumentum elemzéshez"""
        return """Te egy szakértő jogi dokumentum elemző mesterséges intelligencia vagy.
Feladatod: Elemezd a mellékelt dokumentumot és készíts részletes, strukturált összefoglalót.

FONTOS SZABÁLYOK:
1. Elemezd a dokumentumot szakszerűen, de érthetően
2. Emeld ki a legfontosabb információkat
3. Azonosítsd a dokumentum típusát (szerződés, bírósági irat, hatósági értesítés, stb.)
4. Keress és listázz minden határidőt
5. Azonosítsd a kötelezettségeket és jogokat
6. Javasolj gyakorlati következő lépéseket
7. Ha jogi tanácsra van szükség, jelezd

Válasz formátuma:
1. ÖSSZEFOGLALÓ: (2-3 mondatban)
2. DOKUMENTUM TÍPUSA: (például: "munkaszerződés", "bírósági idézés", stb.)
3. KULCS PONTOK: (bullet lista)
4. HATÁRIDŐK: (dátumok és mit kell tenni)
5. KÖTELEZETTSÉGEK: (mi a teendő)
6. JOGOK: (mire jogosult a címzett)
7. KÖVETKEZŐ LÉPÉSEK: (ajánlások)
8. RÉSZLETES ELEMZÉS: (kibontott magyarázat)"""

    def _get_qa_system_prompt(self) -> str:
        """Rendszer prompt kérdés-válasz módhoz"""
        return """Te egy szakértő jogi dokumentum elemző mesterséges intelligencia vagy.
Feladatod: Válaszolj a felhasználó kérdésére a mellékelt dokumentum alapján.

FONTOS SZABÁLYOK:
1. Csak a dokumentumban található információkra alapozz
2. Ha a válasz nem található meg a dokumentumban, mondd meg
3. Legyél pontos és konkrét
4. Hivatkozz a dokumentum releváns részeire
5. Ha szükséges, javasolj jogi konzultációt
6. Érthetően fogalmazz, laikusok számára

Válasz formátuma:
- Rövid, konkrét válasz (2-3 mondat)
- Releváns dokumentum részletek
- Gyakorlati tanácsok
- Figyelmeztetés, ha szükséges jogi segítség"""

    def _build_analysis_prompt(self, document_text: str) -> str:
        """Prompt összeállítása általános elemzéshez"""
        return f"""Kérlek, elemezd az alábbi dokumentumot a megadott struktúra szerint.

DOKUMENTUM TARTALMA:

{document_text}

Kérlek, készíts részletes elemzést a fenti formátum szerint!"""

    def _build_qa_prompt(self, document_text: str, question: str) -> str:
        """Prompt összeállítása kérdés-válasz módhoz"""
        return f"""DOKUMENTUM TARTALMA:

{document_text}

FELHASZNÁLÓ KÉRDÉSE:
{question}

Kérlek, válaszolj a kérdésre a dokumentum alapján!"""

    def _parse_analysis_response(
        self,
        response: str,
        raw_text: str,
        user_question: Optional[str]
    ) -> DocumentAnalysisResult:
        """AI válasz feldolgozása strukturált eredménybe"""

        # Szekciók kinyerése regex-szel
        def extract_section(pattern: str, text: str) -> str:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            return match.group(1).strip() if match else ""

        def extract_list(pattern: str, text: str) -> List[str]:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if not match:
                return []
            section_text = match.group(1).strip()
            # Bullet pontok kinyerése
            items = re.findall(r'[-•*]\s*(.+?)(?=\n[-•*]|\n\n|\Z)', section_text, re.DOTALL)
            return [item.strip() for item in items if item.strip()]

        summary = extract_section(r'ÖSSZEFOGLALÓ:?\s*(.+?)(?=\n\d+\.|DOKUMENTUM TÍPUSA|$)', response)
        document_type = extract_section(r'DOKUMENTUM TÍPUSA:?\s*(.+?)(?=\n\d+\.|KULCS PONTOK|$)', response)
        detailed_analysis = extract_section(r'RÉSZLETES ELEMZÉS:?\s*(.+?)$', response)

        key_points = extract_list(r'KULCS PONTOK:?\s*(.+?)(?=\n\d+\.|HATÁRIDŐK|$)', response)
        deadlines = extract_list(r'HATÁRIDŐK:?\s*(.+?)(?=\n\d+\.|KÖTELEZETTSÉGEK|$)', response)
        obligations = extract_list(r'KÖTELEZETTSÉGEK:?\s*(.+?)(?=\n\d+\.|JOGOK|$)', response)
        rights = extract_list(r'JOGOK:?\s*(.+?)(?=\n\d+\.|KÖVETKEZŐ LÉPÉSEK|$)', response)
        next_steps = extract_list(r'KÖVETKEZŐ LÉPÉSEK:?\s*(.+?)(?=\n\d+\.|RÉSZLETES ELEMZÉS|$)', response)

        # Ha user_question volt, a teljes választ használjuk detailed_analysis-ként
        if user_question:
            summary = response[:200] + "..." if len(response) > 200 else response
            detailed_analysis = response

        return DocumentAnalysisResult(
            summary=summary or "Összefoglaló nem érhető el",
            detailed_analysis=detailed_analysis or response,
            document_type=document_type or "Nem azonosítható",
            key_points=key_points,
            deadlines=deadlines,
            obligations=obligations,
            rights=rights,
            next_steps=next_steps,
            raw_text=raw_text,
            metadata={
                "model": self.model,
                "has_user_question": user_question is not None,
                "text_length": len(raw_text)
            }
        )


class OfficialLetterInterpreter:
    """
    Hivatalos levelek és dokumentumok értelmezése köznyelvű magyarázattal

    Használat:
    ---------
    >>> from demo.document_processor import OfficialLetterInterpreter
    >>> import anthropic
    >>>
    >>> # Anthropic kliens inicializálása
    >>> client = anthropic.Anthropic(api_key="your-api-key")
    >>>
    >>> # Interpreter létrehozása
    >>> interpreter = OfficialLetterInterpreter(llm_client=client)
    >>>
    >>> # Szöveges dokumentum értelmezése
    >>> with open("ertesites.txt", "r", encoding="utf-8") as f:
    ...     text = f.read()
    >>> result = interpreter.interpret_letter(text)
    >>>
    >>> print(f"Típus: {result.document_type.value}")
    >>> print(f"Köznyelvű összefoglaló: {result.plain_language_summary}")
    >>> print(f"Sürgősség: {result.urgency_level}")
    >>>
    >>> # Word dokumentum értelmezése
    >>> result = interpreter.interpret_from_file("level.docx")
    >>> for action in result.recommended_actions:
    ...     print(f"Teendő: {action}")
    """

    def __init__(self, llm_client: 'anthropic.Anthropic', model: str = "claude-3-haiku-20240307"):
        """
        Inicializálás

        Args:
            llm_client: Anthropic API kliens
            model: Claude modell neve
        """
        if not HAS_ANTHROPIC:
            raise ImportError("Az anthropic csomag nincs telepítve. Telepítsd: pip install anthropic")

        self.llm_client = llm_client
        self.model = model

    def interpret_from_file(self, file_path: Union[str, Path]) -> LetterInterpretationResult:
        """
        Dokumentum értelmezése fájlból (txt, docx)

        Args:
            file_path: Fájl útvonala

        Returns:
            LetterInterpretationResult

        Raises:
            FileNotFoundError: Ha a fájl nem található
            ValueError: Ha a fájl formátum nem támogatott
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"Fájl nem található: {file_path}")

        # Fájl típus alapján olvasás
        if file_path.suffix.lower() == '.txt':
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()

        elif file_path.suffix.lower() in ['.docx', '.doc']:
            if not HAS_DOCX:
                raise ImportError("A python-docx csomag nincs telepítve. Telepítsd: pip install python-docx")
            text = self._extract_text_from_docx(file_path)

        else:
            raise ValueError(f"Nem támogatott fájl formátum: {file_path.suffix}")

        return self.interpret_letter(text)

    def _extract_text_from_docx(self, docx_path: Union[str, Path]) -> str:
        """Szöveg kinyerése Word dokumentumból"""
        try:
            doc = Document(docx_path)
            paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
            return "\n\n".join(paragraphs)
        except Exception as e:
            raise ValueError(f"Hiba történt a Word dokumentum olvasása során: {str(e)}")

    def detect_document_type(self, text: str) -> DocumentType:
        """
        Dokumentum típusának automatikus felismerése

        Args:
            text: Dokumentum szövege

        Returns:
            DocumentType enum érték
        """
        text_lower = text.lower()

        # Bírósági dokumentumok
        birosagi_keywords = [
            'bíróság', 'ítélet', 'végzés', 'idézés', 'tárgyalás',
            'felperest', 'alperest', 'ügyszám', 'perköltség', 'fellebbezés'
        ]

        # Hatósági dokumentumok
        hatosagi_keywords = [
            'hatóság', 'közigazgatási', 'értesítés', 'határozat', 'jogorvoslat',
            'kormányhivatal', 'önkormányzat', 'jegyző', 'polgármesteri hivatal'
        ]

        # Munkaügyi dokumentumok
        munkaugyi_keywords = [
            'munkáltató', 'munkavállaló', 'munkaszerződés', 'felmondás',
            'végkielégítés', 'munkabér', 'túlóra', 'szabadság', 'munkaviszony'
        ]

        # Szerződések
        szerzodes_keywords = [
            'szerződés', 'felek megállapodnak', 'jelen szerződés', 'szerződő felek',
            'megbízási', 'vállalkozási', 'adásvételi', 'bérleti', 'kölcsönszerződés'
        ]

        # Pontozás
        scores = {
            DocumentType.BIROSAGI: sum(1 for kw in birosagi_keywords if kw in text_lower),
            DocumentType.HATOSAGI: sum(1 for kw in hatosagi_keywords if kw in text_lower),
            DocumentType.MUNKAUGYI: sum(1 for kw in munkaugyi_keywords if kw in text_lower),
            DocumentType.SZERZODES: sum(1 for kw in szerzodes_keywords if kw in text_lower),
        }

        max_score = max(scores.values())

        if max_score == 0:
            return DocumentType.ISMERETLEN

        # Legmagasabb pontszámú típus visszaadása
        for doc_type, score in scores.items():
            if score == max_score:
                return doc_type

        return DocumentType.EGYEB

    def interpret_letter(
        self,
        text: str,
        max_tokens: int = 2000
    ) -> LetterInterpretationResult:
        """
        Hivatalos levél értelmezése köznyelvű magyarázattal

        Args:
            text: A levél szövege
            max_tokens: Maximum token szám

        Returns:
            LetterInterpretationResult

        Példa:
        ------
        >>> letter_text = '''
        ... Tisztelt Kovács János!
        ...
        ... Tájékoztatjuk, hogy munkaviszonya 2024. február 29-én megszűnik...
        ... '''
        >>> result = interpreter.interpret_letter(letter_text)
        >>> print(result.plain_language_summary)
        """
        if not text.strip():
            raise ValueError("A dokumentum szövege üres")

        # Dokumentum típus felismerése
        doc_type = self.detect_document_type(text)

        # System prompt
        system_prompt = self._get_interpretation_system_prompt()

        # User prompt
        user_prompt = self._build_interpretation_prompt(text, doc_type)

        # AI hívás
        try:
            message = self.llm_client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=0.2,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )

            response_text = message.content[0].text

            # Válasz feldolgozása
            return self._parse_interpretation_response(response_text, text, doc_type)

        except Exception as e:
            raise RuntimeError(f"Hiba történt az értelmezés során: {str(e)}")

    def _get_interpretation_system_prompt(self) -> str:
        """Rendszer prompt hivatalos levelek értelmezéséhez"""
        return """Te egy szakértő jogi tolmács mesterséges intelligencia vagy.
Feladatod: Magyarázd el hivatalos levelek, hatósági és bírósági értesítések tartalmát KÖZNYELVŰ, egyszerű magyarsággal.

FONTOS SZABÁLYOK:
1. Kerüld a jogi zsargont - írj úgy, mint egy segítőkész ügyvéd, aki a nagyszüleinek magyaráz
2. Emeld ki a legfontosabb információkat (határidők, kötelezettségek, jogok)
3. Határozd meg a sürgősségi szintet (alacsony, közepes, magas, kritikus)
4. Adj praktikus, konkrét tanácsokat
5. Figyelmeztetés: NE adj jogi tanácsot, csak magyarázd el a dokumentumot
6. Javasolj szakértő segítséget, ha szükséges

Válasz formátuma:
1. KÖZNYELVŰ ÖSSZEFOGLALÓ: (3-5 mondatban, teljesen egyszerűen)
2. DOKUMENTUM TÍPUSA: (megerősítés/finomítás)
3. FONTOS DÁTUMOK: (minden határidő dátummal)
4. MIT KELL TENNED: (kötelezettségek egyszerűen)
5. MIRE VAGY JOGOSULT: (jogok, lehetőségek)
6. AJÁNLOTT LÉPÉSEK: (konkrét, gyakorlati tanácsok)
7. SÜRGŐSSÉG: (alacsony/közepes/magas/kritikus + indoklás)
8. RÉSZLETES MAGYARÁZAT: (kibontott értelmezés)"""

    def _build_interpretation_prompt(self, text: str, doc_type: DocumentType) -> str:
        """Prompt összeállítása értelmezéshez"""
        return f"""Az alábbi hivatalos dokumentumot kell értelmezned.

AUTOMATIKUSAN FELISMERT TÍPUS: {doc_type.value}

DOKUMENTUM SZÖVEGE:

{text}

Kérlek, magyarázd el ezt a dokumentumot a megadott struktúra szerint, TELJESEN KÖZÉRTHETŐ NYELVEN!
Képzeld el, hogy egy aggódó embernek magyarázod, aki nem ért a jogi nyelvhez."""

    def _parse_interpretation_response(
        self,
        response: str,
        raw_text: str,
        detected_type: DocumentType
    ) -> LetterInterpretationResult:
        """AI válasz feldolgozása strukturált eredménybe"""

        def extract_section(pattern: str, text: str) -> str:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            return match.group(1).strip() if match else ""

        def extract_list(pattern: str, text: str) -> List[str]:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if not match:
                return []
            section_text = match.group(1).strip()
            items = re.findall(r'[-•*]\s*(.+?)(?=\n[-•*]|\n\n|\Z)', section_text, re.DOTALL)
            return [item.strip() for item in items if item.strip()]

        plain_summary = extract_section(r'KÖZNYELVŰ ÖSSZEFOGLALÓ:?\s*(.+?)(?=\n\d+\.|DOKUMENTUM TÍPUSA|$)', response)
        doc_type_text = extract_section(r'DOKUMENTUM TÍPUSA:?\s*(.+?)(?=\n\d+\.|FONTOS DÁTUMOK|$)', response)
        detailed_explanation = extract_section(r'RÉSZLETES MAGYARÁZAT:?\s*(.+?)$', response)
        urgency = extract_section(r'SÜRGŐSSÉG:?\s*(.+?)(?=\n\d+\.|RÉSZLETES MAGYARÁZAT|$)', response)

        important_dates = extract_list(r'FONTOS DÁTUMOK:?\s*(.+?)(?=\n\d+\.|MIT KELL TENNED|$)', response)
        obligations = extract_list(r'MIT KELL TENNED:?\s*(.+?)(?=\n\d+\.|MIRE VAGY JOGOSULT|$)', response)
        rights = extract_list(r'MIRE VAGY JOGOSULT:?\s*(.+?)(?=\n\d+\.|AJÁNLOTT LÉPÉSEK|$)', response)
        actions = extract_list(r'AJÁNLOTT LÉPÉSEK:?\s*(.+?)(?=\n\d+\.|SÜRGŐSSÉG|$)', response)

        # Dokumentum típus finomítása AI válasz alapján
        final_doc_type = detected_type
        if doc_type_text:
            doc_type_lower = doc_type_text.lower()
            if 'bíróság' in doc_type_lower or 'bírósági' in doc_type_lower:
                final_doc_type = DocumentType.BIROSAGI
            elif 'hatóság' in doc_type_lower or 'hatósági' in doc_type_lower:
                final_doc_type = DocumentType.HATOSAGI
            elif 'munka' in doc_type_lower or 'munkaügyi' in doc_type_lower:
                final_doc_type = DocumentType.MUNKAUGYI
            elif 'szerződés' in doc_type_lower:
                final_doc_type = DocumentType.SZERZODES

        return LetterInterpretationResult(
            document_type=final_doc_type,
            plain_language_summary=plain_summary or "Összefoglaló nem érhető el",
            detailed_explanation=detailed_explanation or response,
            important_dates=important_dates,
            your_obligations=obligations,
            your_rights=rights,
            recommended_actions=actions,
            urgency_level=urgency or "nem meghatározott",
            raw_text=raw_text
        )


# Segédfüggvények a gyors használathoz

def analyze_pdf(
    pdf_path: Union[str, Path],
    api_key: Optional[str] = None,
    question: Optional[str] = None
) -> DocumentAnalysisResult:
    """
    Egyszerűsített PDF elemzés egy függvényhívással

    Args:
        pdf_path: PDF fájl útvonala
        api_key: Anthropic API kulcs (opcionális, környezeti változóból is olvassa)
        question: Opcionális kérdés

    Returns:
        DocumentAnalysisResult

    Példa:
    ------
    >>> result = analyze_pdf("szerzodes.pdf", question="Mikor jár le?")
    >>> print(result.detailed_analysis)
    """
    api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("API kulcs szükséges (paraméter vagy ANTHROPIC_API_KEY környezeti változó)")

    client = anthropic.Anthropic(api_key=api_key)
    processor = PDFProcessor(llm_client=client)
    return processor.analyze_document(pdf_path, user_question=question)


def interpret_letter_file(
    file_path: Union[str, Path],
    api_key: Optional[str] = None
) -> LetterInterpretationResult:
    """
    Egyszerűsített hivatalos levél értelmezés egy függvényhívással

    Args:
        file_path: Dokumentum fájl útvonala (txt, docx)
        api_key: Anthropic API kulcs (opcionális)

    Returns:
        LetterInterpretationResult

    Példa:
    ------
    >>> result = interpret_letter_file("felmondas.txt")
    >>> print(result.plain_language_summary)
    >>> print(f"Sürgősség: {result.urgency_level}")
    """
    api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("API kulcs szükséges (paraméter vagy ANTHROPIC_API_KEY környezeti változó)")

    client = anthropic.Anthropic(api_key=api_key)
    interpreter = OfficialLetterInterpreter(llm_client=client)
    return interpreter.interpret_from_file(file_path)


def interpret_letter_text(
    text: str,
    api_key: Optional[str] = None
) -> LetterInterpretationResult:
    """
    Egyszerűsített hivatalos levél értelmezés szövegből

    Args:
        text: Dokumentum szövege
        api_key: Anthropic API kulcs (opcionális)

    Returns:
        LetterInterpretationResult

    Példa:
    ------
    >>> letter = "Tisztelt Uram! Értesítjük, hogy..."
    >>> result = interpret_letter_text(letter)
    >>> for action in result.recommended_actions:
    ...     print(action)
    """
    api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("API kulcs szükséges (paraméter vagy ANTHROPIC_API_KEY környezeti változó)")

    client = anthropic.Anthropic(api_key=api_key)
    interpreter = OfficialLetterInterpreter(llm_client=client)
    return interpreter.interpret_letter(text)


# Demonstrációs példa
if __name__ == "__main__":
    import sys

    print("=" * 80)
    print("DOKUMENTUM FELDOLGOZÓ MODUL - Demonstráció")
    print("=" * 80)

    # API kulcs ellenőrzés
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("\nHIBA: ANTHROPIC_API_KEY környezeti változó nincs beállítva!")
        print("Használat: export ANTHROPIC_API_KEY='your-api-key'")
        sys.exit(1)

    # Anthropic kliens
    client = anthropic.Anthropic(api_key=api_key)

    print("\n1. PDF PROCESSZOR PÉLDA")
    print("-" * 80)
    print("Usage példa:")
    print("""
    processor = PDFProcessor(llm_client=client)

    # Általános elemzés
    result = processor.analyze_document("szerzodes.pdf")
    print(result.summary)
    print(result.key_points)

    # Konkrét kérdés
    result = processor.analyze_document(
        "szerzodes.pdf",
        user_question="Mikor jár le a szerződés?"
    )
    print(result.detailed_analysis)
    """)

    print("\n2. HIVATALOS LEVÉL ÉRTELMEZŐ PÉLDA")
    print("-" * 80)
    print("Usage példa:")
    print("""
    interpreter = OfficialLetterInterpreter(llm_client=client)

    # Fájlból
    result = interpreter.interpret_from_file("ertesites.txt")
    print(f"Típus: {result.document_type.value}")
    print(f"Összefoglaló: {result.plain_language_summary}")
    print(f"Sürgősség: {result.urgency_level}")

    # Szövegből
    letter_text = "Tisztelt Kovács János! ..."
    result = interpreter.interpret_letter(letter_text)
    for action in result.recommended_actions:
        print(f"- {action}")
    """)

    print("\n3. EGYSZERŰSÍTETT SEGÉDFÜGGVÉNYEK")
    print("-" * 80)
    print("Usage példa:")
    print("""
    # PDF elemzés egy lépésben
    result = analyze_pdf("document.pdf", question="Összefoglaló?")

    # Levél értelmezés fájlból
    result = interpret_letter_file("level.docx")

    # Levél értelmezés szövegből
    result = interpret_letter_text("Levél tartalma...")
    """)

    print("\n" + "=" * 80)
    print("A modul használatra kész!")
    print("Importálás: from demo.document_processor import PDFProcessor, OfficialLetterInterpreter")
    print("=" * 80)
