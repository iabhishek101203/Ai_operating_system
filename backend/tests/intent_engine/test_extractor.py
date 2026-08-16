from app.intent_engine.enums import EntityType
from app.intent_engine.rule_extractor import RuleBasedExtractor


def test_extract_file():
    extractor = RuleBasedExtractor()

    entities = extractor.extract(
        "Rename report.txt to final.txt"
    )

    assert len(entities) == 2
    assert entities[0].type == EntityType.FILE
    assert entities[0].value == "report.txt"
    assert entities[1].value == "final.txt"


def test_extract_folder():
    extractor = RuleBasedExtractor()

    entities = extractor.extract(
        "Move report.pdf to Downloads"
    )

    folders = [
        e for e in entities
        if e.type == EntityType.DIRECTORY
    ]

    assert len(folders) == 1
    assert folders[0].value == "Downloads"


def test_extract_extension():
    extractor = RuleBasedExtractor()

    entities = extractor.extract(
        "Delete every .pdf file"
    )

    extensions = [
        e for e in entities
        if e.type == EntityType.FILE_EXTENSION  
    ]

    assert len(extensions) == 1
    assert extensions[0].value == ".pdf"