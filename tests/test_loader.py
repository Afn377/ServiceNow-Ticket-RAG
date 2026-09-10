from kb_parser.loader import read_kb_file


def test_read_kb_file_decodes_utf8(tmp_path):
    path = tmp_path / "utf8.txt"
    path.write_bytes("KB0000001 Network Wi–Fi Setup".encode("utf-8"))

    text = read_kb_file(path)

    assert text == "KB0000001 Network Wi–Fi Setup"


def test_read_kb_file_falls_back_to_latin1_when_not_valid_utf8(tmp_path):
    path = tmp_path / "latin1.txt"
    # 0xE9 is 'e' with acute accent in latin-1; invalid as a UTF-8 lead byte here
    path.write_bytes("KB0000002 Network Caf\xe9 kiosk".encode("latin-1"))

    text = read_kb_file(path)

    assert text == "KB0000002 Network Caf\xe9 kiosk"
