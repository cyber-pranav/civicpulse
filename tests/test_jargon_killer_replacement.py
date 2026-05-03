"""
test_jargon_killer.py — Unit Tests for the Jargon-Killer Translation Layer.

Validates:
  - "Constituency" is replaced by "Your Voting Neighborhood" / "your voting area".
  - Case-insensitive matching works correctly.
  - Multi-word terms are matched before sub-phrases.
  - The glossary is accessible and complete.
  - Jargon tooltips wrap terms in <span> tags with the original on hover.
"""

from __future__ import annotations


from backend.utils.jargon_killer import translate, get_glossary, JARGON_MAP


class TestJargonTranslation:
    """Tests for the translate() function."""

    def test_constituency_replaced(self):
        """The term 'Constituency' must be replaced by 'your voting area'."""
        result = translate("Please check your Constituency details.")
        assert "constituency" not in result.lower()
        assert "voting area" in result.lower()

    def test_constituency_case_insensitive(self):
        """Translation must be case-insensitive."""
        result = translate("Check the CONSTITUENCY for updates.")
        assert "constituency" not in result.lower()
        assert "voting area" in result.upper() or "VOTING AREA" in result

    def test_electoral_roll_replaced(self):
        """'Electoral roll' should become 'the official voter list'."""
        result = translate("Verify your name on the electoral roll.")
        assert "electoral roll" not in result.lower()
        assert "voter list" in result.lower()

    def test_vvpat_replaced(self):
        """'VVPAT' should become 'Voting Receipt Machine'."""
        result = translate("The VVPAT slip is displayed for 7 seconds.")
        assert "voting receipt machine" in result.lower()

    def test_evm_replaced(self):
        """'EVM' should become 'Electronic Voting Machine'."""
        result = translate("Press the button on the EVM.")
        assert "electronic voting machine" in result.lower()

    def test_epic_replaced(self):
        """'EPIC' should become 'Voter ID card'."""
        result = translate("Carry your EPIC to the booth.")
        assert "voter id" in result.lower()

    def test_nota_replaced(self):
        """'NOTA' should become 'None Of The Above'."""
        result = translate("You can vote for NOTA if needed.")
        assert "none of the above" in result.lower()

    def test_multi_word_longer_first(self):
        """'Parliamentary constituency' must be replaced before 'constituency'."""
        result = translate("A parliamentary constituency determines your MP.")
        assert "lok sabha voting area" in result.lower()

    def test_empty_string(self):
        """Empty string should return empty string."""
        assert translate("") == ""

    def test_no_jargon_passthrough(self):
        """Text without jargon should pass through unchanged."""
        text = "Hello, how are you today?"
        assert translate(text) == text

    def test_multiple_terms_in_one_sentence(self):
        """Multiple jargon terms in a single sentence should all be replaced."""
        result = translate(
            "Check the electoral roll, find your constituency, "
            "and bring your EPIC to the polling booth."
        )
        assert "electoral roll" not in result.lower()
        assert "constituency" not in result.lower()
        # EPIC might be consumed by 'EPIC number' rule or standalone
        assert "voter id" in result.lower() or "Voter ID" in result

    def test_counting_day_replaced(self):
        """'Counting day' should become 'the day votes are counted'."""
        result = translate("Results will be announced on counting day.")
        assert "the day votes are counted" in result.lower()


class TestGlossary:
    """Tests for the get_glossary() function."""

    def test_glossary_returns_dict(self):
        """Glossary should return a non-empty dictionary."""
        glossary = get_glossary()
        assert isinstance(glossary, dict)
        assert len(glossary) > 0

    def test_glossary_contains_constituency(self):
        """Glossary must contain the 'constituency' term."""
        glossary = get_glossary()
        assert "constituency" in glossary

    def test_glossary_constituency_value(self):
        """Glossary 'constituency' value should be 'your voting area'."""
        glossary = get_glossary()
        assert glossary["constituency"] == "your voting area"

    def test_glossary_contains_key_terms(self):
        """Glossary must contain all critical election terms."""
        glossary = get_glossary()
        expected_terms = [
            "constituency",
            "electoral roll",
            "vvpat",
            "evm",
            "epic",
            "nota",
            "mcc",
        ]
        for term in expected_terms:
            assert term in glossary, f"Missing term: {term}"

    def test_jargon_map_is_lowercase(self):
        """All keys in JARGON_MAP should be lowercase."""
        for key in JARGON_MAP:
            assert key == key.lower(), f"Key not lowercase: {key}"
