import pytest

from score_loader import load_scores


def make_csv(tmp_path, content, encoding="utf-8"):
    """각 테스트에서 사용할 임시 CSV 파일을 만든다."""
    path = tmp_path / "scores.csv"
    path.write_bytes(content.encode(encoding))
    return path


def check_skipped(skipped, expected_lines):
    """제외된 줄 번호가 맞고 각 줄에 사유가 기록되었는지 확인한다."""
    assert [record[0] for record in skipped] == expected_lines
    for record in skipped:
        reason = record[-1]
        assert isinstance(reason, str)
        assert reason.strip() != ""


@pytest.mark.parametrize("encoding", ["utf-8", "utf-8-sig"])
def test_valid_rows_keep_order(tmp_path, encoding):
    # 정상 입력은 BOM 유무와 관계없이 원래 순서대로 반환한다.
    path = make_csv(tmp_path, "name,score\n지민,83\n가영,95\n", encoding)
    kept, skipped = load_scores(path)

    assert kept == [("지민", 83), ("가영", 95)]
    assert skipped == []


def test_header_only(tmp_path):
    path = make_csv(tmp_path, "name,score\n")

    assert load_scores(path) == ([], [])


@pytest.mark.parametrize("score", [0, 100])
def test_valid_score_boundaries(tmp_path, score):
    path = make_csv(tmp_path, f"name,score\n승현,{score}\n")
    kept, skipped = load_scores(path)

    assert kept == [("승현", score)]
    assert skipped == []


@pytest.mark.parametrize(
    "invalid_row",
    [
        pytest.param("승현,-1", id="below-minimum"),
        pytest.param("승현,101", id="above-maximum"),
        pytest.param("승현,80.5", id="decimal"),
        pytest.param("승현,abc", id="non-numeric"),
        pytest.param(",80", id="missing-name"),
        pytest.param("승현,", id="missing-score"),
        pytest.param("승현", id="too-few-columns"),
        pytest.param("승현,80,추가", id="too-many-columns"),
    ],
)
def test_invalid_row_is_reported_and_reading_continues(tmp_path, invalid_row):
    # 잘못된 행 바로 다음에 정상 행을 두어 계속 읽는지도 검사한다.
    path = make_csv(tmp_path, f"name,score\n{invalid_row}\n민석,75\n")
    kept, skipped = load_scores(path)

    assert kept == [("민석", 75)]
    check_skipped(skipped, [2])


def test_duplicate_keeps_first_valid_score(tmp_path):
    path = make_csv(
        tmp_path,
        "name,score\n"
        "승현,오류\n"  # 2줄: 무효이므로 이름을 선점하면 안 된다.
        "민석,70\n"   # 3줄: 첫 번째 유효 행
        "승현,85\n"   # 4줄: 승현의 첫 유효 점수
        "승현,99\n",  # 5줄: 중복
    )
    kept, skipped = load_scores(path)

    assert kept == [("민석", 70), ("승현", 85)]
    check_skipped(skipped, [2, 5])


def test_file_is_read_only(tmp_path):
    # BOM, 줄바꿈, 잘못된 행까지 포함해 원본 바이트가 그대로인지 검사한다.
    path = make_csv(tmp_path, "name,score\r\n승현,90\r\n민석,101\r\n", "utf-8-sig")
    before = path.read_bytes()

    load_scores(path)

    assert path.read_bytes() == before