"""
Extended tests for sepsis_timer module: validation, error handling, and lookup correctness.
"""
import csv
import pathlib
import pytest
import sepsis_timer as m


class TestLookup:
    """Tests for the lookup function."""

    def test_lookup_returns_expected_keys(self):
        r = m.lookup("creatinine")
        assert "top_hit" in r
        assert "score" in r
        assert "all" in r
        assert "query" in r

    def test_lookup_sepsis_terms(self):
        terms = ["lactate", "antibiotic", "fluid", "vasopressor", "qsofa"]
        for term in terms:
            r = m.lookup(term)
            assert r["top_hit"] != "no match", f"Expected match for '{term}', got 'no match'"
            assert r["score"] > 0, f"Expected positive score for '{term}', got {r['score']}"

    def test_lookup_none_raises(self):
        with pytest.raises(ValueError, match="None"):
            m.lookup(None)

    def test_lookup_empty_raises(self):
        with pytest.raises(ValueError, match="empty"):
            m.lookup("")

    def test_lookup_whitespace_raises(self):
        with pytest.raises(ValueError, match="empty"):
            m.lookup("   ")

    def test_lookup_case_insensitive(self):
        r1 = m.lookup("LACTATE")
        r2 = m.lookup("lactate")
        assert r1["top_hit"] == r2["top_hit"]

    def test_lookup_top_hit_is_string(self):
        r = m.lookup("lactate")
        assert isinstance(r["top_hit"], str)


class TestProcessCSV:
    """Tests for the process_csv function."""

    def test_process_csv_basic(self, tmp_path):
        pdir = pathlib.Path(__file__).parent
        inp = str(pdir / "sample.csv")
        out = str(tmp_path / "test_output.csv")
        rows = m.process_csv(inp, out)
        assert len(rows) >= 1
        # Verify output file exists and has content
        out_path = pathlib.Path(out)
        assert out_path.exists()
        # Verify output has expected columns
        with open(out, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            assert "top_hit" in reader.fieldnames
            assert "lookup_score" in reader.fieldnames

    def test_process_csv_file_not_found(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            m.process_csv("/nonexistent/path/input.csv", str(tmp_path / "out.csv"))

    def test_process_csv_empty_header(self, tmp_path):
        # Create a CSV with empty header
        bad_csv = tmp_path / "bad.csv"
        with open(bad_csv, "w", encoding="utf-8") as f:
            f.write("")
        with pytest.raises(ValueError):
            m.process_csv(str(bad_csv), str(tmp_path / "out.csv"))


class TestBuildParser:
    """Tests for the CLI argument parser."""

    def test_single_command(self):
        p = m.build_parser()
        args = p.parse_args(["single", "lactate"])
        assert args.cmd == "single"
        assert args.query == "lactate"

    def test_batch_command(self):
        p = m.build_parser()
        args = p.parse_args(["batch", "--input", "in.csv", "--output", "out.csv"])
        assert args.cmd == "batch"
        assert args.input == "in.csv"
        assert args.output == "out.csv"

    def test_main_single(self, capsys):
        rc = m.main(["single", "lactate"])
        assert rc == 0
        captured = capsys.readouterr()
        assert "lactate" in captured.out

    def test_main_batch(self, capsys, tmp_path):
        pdir = pathlib.Path(__file__).parent
        inp = str(pdir / "sample.csv")
        out = str(tmp_path / "main_out.csv")
        rc = m.main(["batch", "--input", inp, "--output", out])
        assert rc == 0
        captured = capsys.readouterr()
        assert "Processed" in captured.out
