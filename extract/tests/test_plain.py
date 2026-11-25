from hawfinch.wikitext.plain import to_plain


def test_plain_text():
    line = (
        ":[2] {{K|Recht|ft=x}} ein [[Verpflichtungsgeschäft]] zum ''[[Erwerb]]'' "
        "[[lieben|liebe]]<ref>{{Lit|A=1}}</ref> {{ugs.}} {{Ü|en|house}}"
    )
    assert to_plain(line) == (
        ":[2] (Recht) ein Verpflichtungsgeschäft zum Erwerb liebe ⟨ugs.⟩ ⟨Ü: en, house⟩"
    )
