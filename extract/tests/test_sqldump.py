import gzip

from hawfinch.dump.sqldump import iter_rows


def test_rows_with_escapes_parentheses_and_null(tmp_path):
    path = tmp_path / "t.sql.gz"
    sql = (
        "-- MySQL dump\n"
        "CREATE TABLE `t` (`a` int);\n"
        "INSERT INTO `t` VALUES (1,'Substantiv_(Deutsch)',14),"
        "(2,'it\\'s, a \\\\ (x)',NULL),(3,'',-1.5);\n"
        "INSERT INTO `other` VALUES (9,'x');\n"
        "INSERT INTO `t` VALUES\n"
        "(4,'one row per line;',1),\n"
        "(5,'x',2);\n"
        "(6,'after the statement',3)\n"
    )
    with gzip.open(path, "wt", encoding="utf-8") as f:
        f.write(sql)
    assert list(iter_rows(path, "t")) == [
        (1, "Substantiv_(Deutsch)", 14),
        (2, "it's, a \\ (x)", None),
        (3, "", -1.5),
        (4, "one row per line;", 1),
        (5, "x", 2),
    ]
