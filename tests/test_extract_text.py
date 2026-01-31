from humanized_selenium_scraper.extract_text import (
    decode_antispam_mail,
    parse_phone_and_email_obfuscated,
)


def test_decode_antispam_mail_shift_minus_one() -> None:
    assert decode_antispam_mail("nbjmup;") == "mailto:"


def test_parse_phone_and_email_obfuscated_normal_and_obf() -> None:
    text = """
    Telefon: +49 (0) 1234 567890
    Mail: info@example.org
    Obf: sales (at) example (dot) com
    """
    phones, mails = parse_phone_and_email_obfuscated(text)
    assert any("1234" in p for p in phones)
    assert "info@example.org" in mails
    assert "sales@example.com" in mails
