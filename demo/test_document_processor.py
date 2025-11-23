"""
Teszt szkript a document_processor modulhoz
Demonstrációs célokra - NEM unit teszt
"""

import os
import sys
from pathlib import Path

# Hozzáadjuk a demo könyvtárat a Python path-hoz
sys.path.insert(0, str(Path(__file__).parent))

try:
    from document_processor import (
        PDFProcessor,
        OfficialLetterInterpreter,
        DocumentType,
        analyze_pdf,
        interpret_letter_text
    )
    import anthropic
except ImportError as e:
    print(f"HIBA: Hiányzó csomag - {e}")
    print("\nTelepítsd a szükséges csomagokat:")
    print("pip install -r requirements.txt")
    sys.exit(1)


def test_letter_interpreter():
    """Hivatalos levél értelmező teszt mock adatokkal"""
    print("\n" + "=" * 80)
    print("HIVATALOS LEVÉL ÉRTELMEZŐ TESZT")
    print("=" * 80)

    # Teszt szöveg - Bírósági idézés mintája
    mock_birosagi_level = """
    BUDAPESTI II. ÉS III. KERÜLETI BÍRÓSÁG
    1027 Budapest, Frankel Leó út 15.

    Ügyszám: 12.P.23.456/2024/5

    IDÉZÉS

    Kovács János
    1024 Budapest, Margit körút 10.

    Tisztelt Kovács János!

    Tájékoztatom, hogy a Budapesti II. és III. Kerületi Bíróság előtt
    Nagy Péter (felperes) kontra Kovács János (alperes) között
    kártérítési ügyben folyamatban lévő perben 2024. március 15-én,
    10:00 órakor tárgyalás lesz a 301-es tárgyalóteremben.

    Megjelenése kötelező. Távolmaradás esetén mulasztási bírság
    kiszabására vagy mulasztási ítélet meghozatalára kerülhet sor.

    Jogosult jogi képviselőt (ügyvédet) meghatalmazni.

    A tárgyalásra hozza magával:
    - Személyi igazolványát
    - Az ügyre vonatkozó minden okiratot
    - Tanúinak nevét és elérhetőségét

    Kelt: 2024. február 10.

    Dr. Szabó Mária
    Bíró
    """

    # API kulcs ellenőrzés
    api_key = os.getenv("ANTHROPIC_API_KEY")

    if not api_key:
        print("\nFIGYELMEZTETÉS: ANTHROPIC_API_KEY nincs beállítva!")
        print("A teszt mock válasszal fog futni (AI nélkül).\n")
        print("Valós teszt futtatásához:")
        print("export ANTHROPIC_API_KEY='your-api-key'\n")

        # Mock válasz AI nélkül
        print("MOCK EREDMÉNY (AI nélkül):")
        print("-" * 80)
        print("Dokumentum típus: bírósági")
        print("\nKöznyelvű összefoglaló:")
        print("Bírósági idézést kaptál egy kártérítési perben, ahol téged perelnek.")
        print("2024. március 15-én 10 órakor meg kell jelenned a bíróságon.")
        print("Ha nem mész el, bírságot kaphatnak vagy ítéletet hozhatnak ellened.")
        print("\nSürgősség: MAGAS - Kötelező megjelenés, jogsértő következményekkel")
        return

    # Valós AI teszt
    try:
        print("\nFuttatás valós AI-val...")
        print("-" * 80)

        client = anthropic.Anthropic(api_key=api_key)
        interpreter = OfficialLetterInterpreter(llm_client=client)

        # Dokumentum típus detektálás
        detected_type = interpreter.detect_document_type(mock_birosagi_level)
        print(f"Automatikusan felismert típus: {detected_type.value}")

        # Teljes értelmezés
        print("\nLevél értelmezése folyamatban...")
        result = interpreter.interpret_letter(mock_birosagi_level)

        print(f"\nVégleges dokumentum típus: {result.document_type.value}")
        print(f"\nKöznyelvű összefoglaló:\n{result.plain_language_summary}")
        print(f"\nSürgősség: {result.urgency_level}")

        if result.important_dates:
            print("\nFontos dátumok:")
            for date in result.important_dates:
                print(f"  - {date}")

        if result.your_obligations:
            print("\nMit kell tenned:")
            for obligation in result.your_obligations:
                print(f"  - {obligation}")

        if result.your_rights:
            print("\nMire vagy jogosult:")
            for right in result.your_rights:
                print(f"  - {right}")

        if result.recommended_actions:
            print("\nAjánlott lépések:")
            for action in result.recommended_actions:
                print(f"  - {action}")

        print("\n" + "=" * 80)
        print("TESZT SIKERES!")
        print("=" * 80)

    except Exception as e:
        print(f"\nHIBA történt: {e}")
        import traceback
        traceback.print_exc()


def test_pdf_processor_mock():
    """PDF processzor mock teszt (AI nélkül, csak struktura)"""
    print("\n" + "=" * 80)
    print("PDF PROCESSZOR STRUKTÚRA TESZT (Mock)")
    print("=" * 80)

    api_key = os.getenv("ANTHROPIC_API_KEY")

    if not api_key:
        print("\nINFO: PDF processzor teszt csak AI kulccsal futtatható.")
        print("Export ANTHROPIC_API_KEY='your-key' a teszteléshez.\n")
        print("Példa használat:")
        print("""
        from document_processor import PDFProcessor
        import anthropic

        client = anthropic.Anthropic(api_key='your-key')
        processor = PDFProcessor(llm_client=client)

        # Általános elemzés
        result = processor.analyze_document('document.pdf')
        print(result.summary)
        print(result.key_points)

        # Konkrét kérdés
        result = processor.analyze_document(
            'document.pdf',
            user_question='Mikor jár le a szerződés?'
        )
        print(result.detailed_analysis)
        """)
        return

    print("\nPDF processzor inicializálva és használatra kész.")
    print("PDF fájlra van szükség a valós teszthez.")


def test_helper_functions():
    """Egyszerűsített helper függvények teszt"""
    print("\n" + "=" * 80)
    print("HELPER FÜGGVÉNYEK TESZT")
    print("=" * 80)

    print("\nElérhető helper függvények:")
    print("  1. analyze_pdf(pdf_path, api_key, question)")
    print("  2. interpret_letter_file(file_path, api_key)")
    print("  3. interpret_letter_text(text, api_key)")

    print("\nPélda használat:")
    print("""
    # PDF elemzés egy lépésben
    result = analyze_pdf('document.pdf', question='Összefoglalás?')

    # Levél értelmezés fájlból
    result = interpret_letter_file('ertesites.txt')

    # Levél értelmezés szövegből
    result = interpret_letter_text('Levél tartalma...')
    """)


def test_document_type_detection():
    """Dokumentum típus felismerés teszt"""
    print("\n" + "=" * 80)
    print("DOKUMENTUM TÍPUS FELISMERÉS TESZT")
    print("=" * 80)

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("\nMock teszt (AI nélkül)")
        print("-" * 80)

    test_cases = [
        ("Bírósági idézés a tárgyalásra...", DocumentType.BIROSAGI),
        ("A kormányhivatal értesíti, hogy határozat...", DocumentType.HATOSAGI),
        ("Munkaszerződés megszüntetése... felmondás...", DocumentType.MUNKAUGYI),
        ("Jelen szerződés tárgya... felek megállapodnak...", DocumentType.SZERZODES),
        ("Tisztelt Ügyfelünk! Tájékoztatjuk...", DocumentType.ISMERETLEN),
    ]

    if api_key:
        try:
            client = anthropic.Anthropic(api_key=api_key)
            interpreter = OfficialLetterInterpreter(llm_client=client)

            print("\nTípus felismerés tesztek:")
            for text_sample, expected in test_cases:
                detected = interpreter.detect_document_type(text_sample)
                status = "OK" if detected == expected else "FAIL"
                print(f"{status} '{text_sample[:40]}...' -> {detected.value} (várva: {expected.value})")

        except Exception as e:
            print(f"Hiba: {e}")
    else:
        print("\nLehetséges dokumentum típusok:")
        for doc_type in DocumentType:
            print(f"  - {doc_type.value}")


def main():
    """Fő teszt függvény"""
    # Windows encoding fix
    if sys.platform == 'win32':
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

    print("=" * 80)
    print("DOKUMENTUM FELDOLGOZÓ MODUL - TESZT SUITE")
    print("=" * 80)

    # Környezet ellenőrzés
    print("\nKörnyezet ellenőrzése...")
    api_key = os.getenv("ANTHROPIC_API_KEY")
    print(f"ANTHROPIC_API_KEY: {'Beállítva OK' if api_key else 'Nincs beállítva'}")

    # Csomagok ellenőrzése
    print("\nCsomagok ellenőrzése...")
    packages = {
        "anthropic": None,
        "pdfplumber": None,
        "docx": "python-docx"
    }

    for package, install_name in packages.items():
        try:
            __import__(package)
            print(f"  {install_name or package}: Telepítve OK")
        except ImportError:
            print(f"  {install_name or package}: HIÁNYZIK")

    # Tesztek futtatása
    try:
        test_document_type_detection()
        test_letter_interpreter()
        test_pdf_processor_mock()
        test_helper_functions()

        print("\n" + "=" * 80)
        print("ÖSSZES TESZT LEFUTOTT")
        print("=" * 80)
        print("\nA modul használatra kész!")
        print("Részletes használati útmutató: DOCUMENT_PROCESSOR_USAGE.md")

    except KeyboardInterrupt:
        print("\n\nTeszt megszakítva.")
    except Exception as e:
        print(f"\n\nVáratlan hiba: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
