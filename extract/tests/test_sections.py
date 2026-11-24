from hawfinch.wikitext.sections import blocks, german_sections, language_sections, split_sections

PAGE = """\
{{Siehe auch|[[haus]]}}
== Haus ({{Sprache|Deutsch}}) ==
=== {{Wortart|Substantiv|Deutsch}}, {{n}} ===
{{Worttrennung}}
:Haus, {{Pl.}} Häu·ser
<!--
=== {{Wortart|Verb|Deutsch}} ===
-->
==== {{Übersetzungen}} ====
{{Ü-Tabelle|1}}

== Haus ({{Sprache|Englisch}}) ==
=== {{Wortart|Substantiv|Englisch}} ===
"""


def test_tree_and_offsets():
    (german, english) = split_sections(PAGE)
    assert german.level == 2 and german.title == "Haus ({{Sprache|Deutsch}})"
    (pos,) = german.children
    assert [c.title for c in pos.children] == ["{{Übersetzungen}}"]
    assert pos.body(PAGE).startswith("{{Worttrennung}}\n:Haus")
    assert "{{Ü-Tabelle|1}}" in pos.full(PAGE) and "{{Ü-Tabelle|1}}" not in pos.body(PAGE)
    assert german.end == english.start


def test_language_and_part_of_speech():
    entries = language_sections(PAGE)
    assert [(e.word, e.language) for e in entries] == [("Haus", "Deutsch"), ("Haus", "Englisch")]
    (german,) = german_sections(PAGE)
    (pos,) = german.pos_sections
    assert pos.wortarten == [("Substantiv", "Deutsch")]
    assert [t.name for t in pos.heading_templates] == ["Wortart", "n"]


def test_unequal_equals_signs():
    (section,) = split_sections("=== a ==\n")
    assert section.level == 2 and section.title == "= a"


def test_blocks():
    body = (
        "{{Deutsch Substantiv Übersicht\n|Genus=n\n}}\n\n{{Worttrennung}}\n:Haus\n\n"
        "{{Bedeutungen}}\n:[1] Gebäude\n<!-- {{Herkunft}} -->\n::[a] Wohnhaus\n"
        "{{Ähnlichkeiten 1|Anagramme=x}}\n{{Herkunft}}\n:von ''[[hūs]]''\n"
    )
    result = blocks(body)
    assert result["Worttrennung"] == [":Haus"]
    assert result["Bedeutungen"] == [
        ":[1] Gebäude",
        "::[a] Wohnhaus",
        "{{Ähnlichkeiten 1|Anagramme=x}}",
    ]
    assert result["Herkunft"] == [":von ''[[hūs]]''"]
    assert result[""][0] == "{{Deutsch Substantiv Übersicht"
