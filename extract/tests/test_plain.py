from hawfinch.features.partofspeech import COMMON_NOUN, PROPER_NOUN, noun_class
from hawfinch.wikitext.plain import to_plain


def test_plain_text():
    line = (
        ":[2] {{K|Recht|ft=x}} ein [[Verpflichtungsgeschäft]] zum ''[[Erwerb]]'' "
        "[[lieben|liebe]]<ref>{{Lit|A=1}}</ref> {{ugs.}} {{Ü|en|house}}"
    )
    assert to_plain(line) == (
        ":[2] (Recht) ein Verpflichtungsgeschäft zum Erwerb liebe ⟨ugs.⟩ ⟨Ü: en, house⟩"
    )


def test_noun_class():
    assert noun_class(["Substantiv", "Toponym"]) == PROPER_NOUN
    assert noun_class(["Eigenname"]) == PROPER_NOUN
    assert noun_class(["Substantiv", "Abkürzung"]) == COMMON_NOUN
    assert noun_class(["Verb"]) is None


def test_language_names():
    def cls(title, sense):
        return noun_class(["Substantiv"], title=title, first_sense=sense)

    assert cls("Estnisch", ":[1] die Sprache der Esten") == PROPER_NOUN
    assert cls("Dzongkha", ":[1] die Amtssprache Bhutans") == PROPER_NOUN
    assert cls("Banda", ":[1] austronesische Sprache, die auf den Kai-Inseln gesprochen wird") == (
        PROPER_NOUN
    )
    assert cls("Hocharabisch", ":[1] Varietät des Arabischen") == PROPER_NOUN
    assert cls("Etruskisch", ":[1] Sprachwissenschaft: ausgestorbene Sprache") == PROPER_NOUN
    # register labels, a definition merely mentioning a language, a kind of language
    assert cls("Lenzpumpe", ":[1] Seemannssprache: Pumpe") == COMMON_NOUN
    assert cls("Smutje", ":[1] (Seemannssprache) Koch an Bord") == COMMON_NOUN
    assert cls("Germanistik", ":[1] die Wissenschaft von der deutschen Sprache") == COMMON_NOUN
    assert cls("Fachsprache", ":[1] die Sprache eines Fachs") == COMMON_NOUN
    assert noun_class(["Substantiv"], first_sense=":[1] die Sprache der Esten") == COMMON_NOUN
