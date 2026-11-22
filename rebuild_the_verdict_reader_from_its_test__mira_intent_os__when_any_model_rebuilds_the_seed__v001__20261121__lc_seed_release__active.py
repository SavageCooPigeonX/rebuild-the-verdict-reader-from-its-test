# Checksum: 888  christ is king
"""Seed contract: the verdict reader. This test is the whole specification; there is no code to copy.

Write a module named `verdict_reader` (one file, standard library only) that makes this file pass:

    pytest rebuild_the_verdict_reader_from_its_test__mira_intent_os__when_any_model_rebuilds_the_seed__v001__20261121__lc_seed_release__active.py

What the module does
--------------------
An agent posts a numbered list of proposed work items. The operator types one short reply, for example
"approve 1, reject 2", "29 approve 30 reject", "approve all" or "0970 approve". The reader turns that one typed row
into a verdict per item number. It is a deterministic pre-check: it never guesses at prose, and every receipt says
"deterministic_precheck".

The rules, in the order the reader applies them. Every match is case-insensitive.

1. Typos. fix_approve_typos(text) looks at each run of letters A-Z. A run one typed letter off "approve" or
   "approved" (compared in lower case: one letter wrong, missing or extra, or two neighbouring letters swapped)
   becomes "approve". The real approve words and "approval", "approvals", "approver", "approvers" stay as typed.
   Two typed letters off is no typo ("aprvoe", "pprovd"); neither is "improve", "reprove" or "unapprove".
2. Glued words. After the typo fix, a space is typed between a digit and a verdict word it touches: digit then
   word ("1approve" reads "1 approve", "12hold" reads "12 hold"), and word then digit ("approve3" reads
   "approve 3", "29 approve30 reject" reads "29 approve 30 reject"). Only the word's own far end is checked: in
   digit-then-word the word must end at a word edge, and in word-then-digit it must start at one (a word edge has
   a letter, digit or "_" on one side and anything else, or the row's start or end, on the other). The digits'
   side is never checked, so the number may have more digits. The words that can be glued are
   approve/approved/approves/approving, reject/rejected, deny/denied, hold and skip/skipped. A verdict word glued
   to letters ("approvepush", "1approvepush") is not unglued, and it is no verdict word.
3. Verdict words are whole words. Approve words: approve, approved, approves, approving. Deny words: reject...,
   deny, denied, denies, hold, holding, skip..., no, nope, not, never, don't, dont, drop..., declin..., unapprov...,
   disapprov... ("..." means any letters may follow). Each keeps the spelling it has after rules 1-2. The whole
   word must be one of these spellings; only the six stems written with "..." may go on. So any other word that
   merely starts like a deny word is no verdict word ("now", "none", "noticed", "nothing", "note", "holder",
   "denying", "denial", "nevermind", "donate"), while "skipper", "dropbox" and "rejection" are deny words.
4. Item numbers. An item number is 1 to 3 digits read as an int, so 0 is an item number too ("0 approve",
   "approve 00" and "007" read 0, 0 and 7). It is optionally typed after "#" ("#3"), or a range "8-12", which gives
   every number in it when the second is larger than the first by at most 20. Any other range gives no number at
   all, not even its first number ("8-30", "12-8" and "3-3" give none). An item number is never part of a word,
   a longer number, a decimal, a time, a size, a price or a path: the character right before it is not a letter,
   digit, "_", ".", ":", "$", "%", "/", "@" or "-", and the character right after it is not a letter, digit, "_",
   "%" or "/", nor a "." or ":" followed by a digit. "3." and "3)" are item numbers; "22:15", "1.5", "5%", "v2"
   and "0970" are not.
5. Groups. Item numbers joined only by spaces, commas, "&", "+", "/" or the word "and" form one group ("1,2,3",
   "1 and 2"). Any other text between two numbers starts a new group. A "#" belongs to the number right after it
   only when the character before that "#" passes rule 4's "right before" check (or the "#" starts the row);
   otherwise the "#" is plain text. So "#6 and #7", "#1, #2, #3" and "#1 #2" are each one group, while in "#1#2"
   and "1#2" the second "#" follows a digit, so it is plain text between 1 and 2 and they are two groups.
6. Touching. A word's next group is the first group that starts after the word ends; its previous group is the
   last group that ends before the word starts. (A group never counts as both.) The word touches its next group
   when the text between them is only spaces, the words "the", "item", "items", "number", "numbers" (each followed
   by a space) and a final "#" ("reject items 4 and 5", "approve #6", "approve 1"). It touches its previous group
   when the text between them is only spaces and these eight characters, each taken literally: comma, full stop,
   colon, semicolon, ")", "]", "#" and "-" ("3. hold", "4) reject", "5 - deny", "2 approve"). (In a regular
   expression character class, "]" and "-" must be escaped to be taken literally.) In "approve all - 4" approve does not touch 4,
   because "all" sits between.
7. Style. The row's anchor is its first verdict word that touches its next or previous group, or its first
   verdict word when none touches. style is "verb_first" when the row has a group and the anchor starts before the
   first group starts; otherwise it is "number_first" (also for a row with no verdict word or no number). So a
   verdict word in another clause that touches no number ("no push tests ... - 2 approve") does not make the row
   verb first.
8. Naming. Each verdict word names at most one group. In a verb_first row it names its next group when it touches
   it. Otherwise (in every number_first row, and in a verb_first row when it does not touch its next group) it
   names its previous group, however far back, even when it touches its next group too: in the number_first row
   "1 ok 3 later skip 9" skip names 3, not 9. With no previous group, it names its next group
   only when it touches it; else it names nothing. So in "approve 1, reject 2" approve names 1 and reject names 2;
   in "approve 5 - 6 reject" (a verb_first row) reject has no next group, so it names its previous group, 6;
   in "approve 1 and 2, then 3 later reject" it names 3 the same way, though "later" sits between; and in
   "approve this, then 4 is fine, no rush" the word "no" names 4;
   in "approve all - 4 hold" hold names 4 and approve names nothing; in "2 reject, approve all" both name 2.
9. Verdicts. A group takes the first verdict word that names it: each of its numbers reads {"verdict": "approve"}
   or {"verdict": "deny"} with "word" set to that word. A number no word names reads {"verdict": "none",
   "word": None}. A number in two groups keeps its first group's verdict. verdicts is keyed by int.
10. "all" is true when an approve word is followed by "all" (or "them all", "these all", "it all"), or "all" is
   followed by an approve word (or "all are approved", "all is approved"). "cards" is true when an approve word is
   followed by "card" or "cards" with, between them, optionally one of "the", "all", "these" and then optionally
   "held" ("approve the held cards"); or "card"/"cards" (optionally then "are") is followed by an approve word.
   Both are read after rules 1-2, and the words in each pattern are separated only by whitespace: a number or a
   mark between them breaks the pattern ("approve 1 cards", "approve, all" and "all 3 approved" count neither).
11. read_row(text) returns exactly {"checked_by": "deterministic_precheck", "style", "verdicts", "all", "cards",
   "approve_words", "deny_words"}: approve_words and deny_words say whether any verdict word of that kind was read.
12. Identities. item_ikid(item) returns the 4-digit identity typed after "IKID" (spaces and one "#" may sit
   between) when the item shows exactly one distinct identity, else None. name_items_by_ikid(text, [(number,
   ikid), ...]) rewrites each identity that stands where an item number could (rule 4's edges; a "#" before it is
   kept) as that item's number, so "0970 reject" reads "1 reject"; "10970" is not "0970".
13. named_by(read, *, number=None, slug=None, text="", only_item=False) says how a row approves a stated item:
   "number" when that number's verdict is approve; None when it is deny; else "slug" when the slug is a substring
   of text exactly as typed and the row read approve words and no deny words; else "all" when read["all"]; else
   "only_item" when only_item is true and the row has no item number, read approve words and no deny words; else
   None.
"""
import argparse
from contextlib import redirect_stdout
import hashlib
import json
from pathlib import Path
import sys

import verdict_reader as vr


def verdict(text, number):
    return vr.read_row(text)["verdicts"].get(number, {}).get("verdict")


def test_each_number_takes_the_verdict_typed_for_it():
    assert verdict("29 approve 30 reject", 29) == "approve" and verdict("29 approve 30 reject", 30) == "deny"
    assert verdict("approve 1, reject 2", 1) == "approve" and verdict("approve 1, reject 2", 2) == "deny"
    assert verdict("3. approved", 3) == "approve"
    for word in ("reject", "hold", "skip", "deny", "no"):
        assert verdict(f"30 {word}", 30) == "deny"
    assert verdict("30 not approved", 30) != "approve"
    assert vr.read_row("30 reject")["verdicts"][30] == {"verdict": "deny", "word": "reject"}
    for word in ("approved", "approves", "approving", "Approve"):
        assert vr.read_row(f"33 {word}")["verdicts"][33] == {"verdict": "approve", "word": word}, word
    for word in ("rejected", "denied", "denies", "holding", "skipped", "nope", "never", "don't", "dont", "dropped",
                 "declined", "unapproved", "disapproves"):
        assert verdict(f"30 {word}", 30) == "deny", word
    assert verdict("30 reject approve", 30) == "deny"
    for word in ("nothing", "note", "know", "holder", "denying", "nevermind", "snot", "notable", "now", "noticed",
                 "none", "nobody", "notify", "normal", "north", "holdout", "household", "denial", "nevertheless",
                 "donate", "dontcha", "nod"):
        assert vr.read_row(f"1 approve - {word} later")["deny_words"] is False, word
    for word in ("skipper", "dropbox", "rejection"):
        assert vr.read_row(f"1 approve - {word}")["deny_words"] is True, word
    assert vr.read_row("approve 5 - 6 reject")["verdicts"] == {5: {"verdict": "approve", "word": "approve"},
                                                              6: {"verdict": "deny", "word": "reject"}}


def test_groups_and_ranges_share_one_verdict():
    assert verdict("approve 1 and 2", 1) == "approve" and verdict("approve 1 and 2", 2) == "approve"
    assert all(verdict("1,2,3 approve", n) == "approve" for n in (1, 2, 3))
    assert all(verdict("8-12 approve", n) == "approve" for n in range(8, 13))
    assert all(verdict("1-3 approve", n) == "approve" for n in (1, 2, 3))
    assert vr.read_row("approve 1, reject 2 and 3")["verdicts"] == {1: {"verdict": "approve", "word": "approve"},
                                                                   2: {"verdict": "deny", "word": "reject"},
                                                                   3: {"verdict": "deny", "word": "reject"}}
    assert sorted(vr.read_row("1-21 approve")["verdicts"]) == list(range(1, 22))
    assert sorted(vr.read_row("90-100 approve")["verdicts"]) == list(range(90, 101))
    for text in ("1-22 approve", "8-30 approve", "12-8 approve", "3-3 approve", "approve 1000", "approve 2-1",
                 "approve 3-3", "approve 1-22"):
        assert vr.read_row(text)["verdicts"] == {}, text
    assert all(verdict("approve 1-2", n) == "approve" for n in (1, 2))
    assert vr.read_row("reject 1, approve 1-2")["verdicts"] == {1: {"verdict": "deny", "word": "reject"},
                                                               2: {"verdict": "approve", "word": "approve"}}
    assert verdict("approve 100", 100) == "approve"
    assert verdict("0 approve", 0) == "approve" and verdict("approve 00", 0) == "approve"
    assert verdict("approve 007", 7) == "approve" and all(verdict("0-3 reject", n) == "deny" for n in range(4))
    for text in ("1 & 2 approve", "1+2 approve", "1 / 2 approve", "1, 2 and 3 approve"):
        assert verdict(text, 1) == "approve" and verdict(text, 2) == "approve", text
    assert vr.read_row("1 reject 4,5 approved")["verdicts"] == {1: {"verdict": "deny", "word": "reject"},
                                                               4: {"verdict": "approve", "word": "approved"},
                                                               5: {"verdict": "approve", "word": "approved"}}
    for text in ("approve item 4", "approve items 4 and 5", "approve the 4", "approve number 4",
                 "approve numbers 4 and 5", "approve #4"):
        assert verdict(text, 4) == "approve", text
    for text, numbers in (("approve #6 and #7", (6, 7)), ("approve #1, #2, #3", (1, 2, 3)),
                          ("approve #1 #2", (1, 2)), ("#2 #3 approve", (2, 3))):
        assert all(verdict(text, n) == "approve" for n in numbers), text
    for text in ("#1#2 approve", "1#2 approve", "1# 2 approve"):
        assert vr.read_row(text)["verdicts"] == {1: {"verdict": "none", "word": None},
                                                 2: {"verdict": "approve", "word": "approve"}}, text
    assert vr.read_row("1 ok 3 later skip 9")["verdicts"] == {1: {"verdict": "none", "word": None},
                                                             3: {"verdict": "deny", "word": "skip"},
                                                             9: {"verdict": "none", "word": None}}


def test_a_row_reports_its_style_and_words():
    row = vr.read_row("approve 1, reject 2")
    assert row["checked_by"] == "deterministic_precheck"
    assert row["style"] == "verb_first" and vr.read_row("29 approve 30 reject")["style"] == "number_first"
    assert row["approve_words"] is True and row["deny_words"] is True
    assert vr.read_row("1 approve")["verdicts"][1] == {"verdict": "approve", "word": "approve"}
    assert vr.read_row("2 approvepush")["verdicts"][2] == {"verdict": "none", "word": None}
    for mark in (",", ".", ":", ";", ")", "]", "#", " -"):
        assert vr.read_row(f"approve this - 3{mark} reject")["style"] == "number_first", mark
    assert vr.read_row("approve this, then 4 is fine, no rush")["style"] == "verb_first"
    assert vr.read_row("approve this, then 4 is fine, no rush")["verdicts"] == {4: {"verdict": "deny", "word": "no"}}
    assert vr.read_row("approve 1 and 2, then 3 later reject")["verdicts"] == {
        1: {"verdict": "approve", "word": "approve"}, 2: {"verdict": "approve", "word": "approve"},
        3: {"verdict": "deny", "word": "reject"}}
    assert vr.read_row("ok approved, 1,2,3 approve")["style"] == "number_first"


def test_glued_numbers_times_and_other_clauses():
    assert verdict("1approve", 1) == "approve" and verdict("approve2", 2) == "approve"
    assert vr.read_row("64 approve3")["verdicts"] == {64: {"verdict": "approve", "word": "approve"},
                                                     3: {"verdict": "none", "word": None}}
    assert vr.read_row("29 approve30 reject")["verdicts"] == {29: {"verdict": "approve", "word": "approve"},
                                                             30: {"verdict": "deny", "word": "reject"}}
    assert set(vr.read_row("at 22:15 approve 7")["verdicts"]) == {7}
    row = "no push tests is exactly what my syntax means - 2 approve 3 approve"
    assert verdict(row, 2) == "approve" and verdict(row, 3) == "approve"
    for word in ("approve", "approved", "approves", "approving", "reject", "rejected", "deny", "denied", "hold",
                 "skip", "skipped"):
        kind = "approve" if word.startswith("approv") else "deny"
        assert verdict(f"5{word}", 5) == kind and verdict(f"{word}5", 5) == kind, word
    assert vr.read_row("1approvepush")["verdicts"] == {}
    assert set(vr.read_row("approve 7 - v2 $3 @4 /5 x_6 %8 1.5 22:15 -9 5% 6/ 3a")["verdicts"]) == {7}


def test_all_and_cards_count_only_next_to_an_approve_word():
    assert vr.read_row("approve all -")["all"] and not vr.read_row("all of it is fine 2 approve")["all"]
    assert vr.read_row("approve cards")["cards"]
    assert not vr.read_row("29 approve the link cards and alerts")["cards"]
    for text in ("approved them all", "approve these all", "approve it all", "all approved", "all are approved",
                 "all is approved"):
        assert vr.read_row(text)["all"], text
    for text in ("approve card", "approve the cards", "approve all cards", "approve these cards",
                 "approve held cards", "approve the held cards", "card approved", "cards are approved"):
        assert vr.read_row(text)["cards"], text
    for text in ("approve 1 cards", "approve, cards", "cards, approved", "approve 1 all", "approve, all",
                 "all, approved", "all 3 approved"):
        row = vr.read_row(text)
        assert not row["all"] and not row["cards"], text


def test_one_typed_letter_off_approve_approves():
    for text in ("30 apprpve", "30 aprove", "30 aproved", "30 approvee", "30 apporve", "30 Apprive", "30 approvd"):
        assert verdict(text, 30) == "approve", text
    for text in ("30 aprvoe", "30 pprovd", "30 approval", "30 approver", "30 improve", "30 reprove",
                 "30 unapprove", "30 disapprove"):
        assert verdict(text, 30) != "approve", text
    assert vr.fix_approve_typos("needs approval - apprpve 3") == "needs approval - approve 3"
    assert vr.read_row("apprpve all")["all"]


def test_an_items_identity_names_its_number():
    assert vr.item_ikid("1. IKID 0970 v001: a_sample_item - checks: the reader") == "0970"
    assert vr.item_ikid("1. an item with no identity") is None
    assert vr.name_items_by_ikid("approve 0970", [(1, "0970")]) == "approve 1"
    assert vr.name_items_by_ikid("approve 10970 and 0971", [(1, "0970")]) == "approve 10970 and 0971"
    assert verdict(vr.name_items_by_ikid("0970 reject", [(1, "0970")]), 1) == "deny"
    assert vr.item_ikid("1. IKID #0970 v001") == "0970" and vr.item_ikid("IKID 0970, again ikid 0970") == "0970"
    assert vr.item_ikid("IKID 09701") is None and vr.item_ikid("IKID 0970 and IKID 0971") is None
    assert (vr.name_items_by_ikid("0970.5 0970/2 0970:1 x0970 #0970 approve", [(1, "0970")])
            == "0970.5 0970/2 0970:1 x0970 #1 approve")
    edges = "v.0970 :0970 $0970 %0970 /0970 @0970 -0970 0970% 0970x 0970_ approve"
    assert vr.name_items_by_ikid(edges, [(1, "0970")]) == edges


def test_how_a_row_approves_a_stated_item():
    assert vr.named_by(vr.read_row("2 approve"), number=2) == "number"
    assert vr.named_by(vr.read_row("2 reject, approve all"), number=2) is None
    assert vr.named_by(vr.read_row("approve all - 4 hold"), number=4) is None
    assert vr.named_by(vr.read_row("approve all"), number=5) == "all"
    text = "approve a_sample_item"
    assert vr.named_by(vr.read_row(text), slug="a_sample_item", text=text) == "slug"
    assert vr.named_by(vr.read_row("not a_sample_item, approve"), slug="a_sample_item",
                       text="not a_sample_item, approve") is None
    assert vr.named_by(vr.read_row("yeah approved"), number=1, only_item=True) == "only_item"
    assert vr.named_by(vr.read_row("yeah approved"), number=1, only_item=False) is None
    assert vr.named_by(vr.read_row("approved - not yet"), number=1, only_item=True) is None
    assert vr.named_by(vr.read_row("approved 2"), number=1, only_item=True) is None


def _main():
    parser = argparse.ArgumentParser(description="Test the verdict reader or run its verified implementation.")
    parser.add_argument("mode", choices=("test", "execute"))
    parser.add_argument("reply", nargs="?")
    args = parser.parse_args()
    if (args.mode == "execute") != (args.reply is not None):
        parser.error("execute takes one reply, and test takes none")

    import pytest

    seed = Path(__file__)
    candidate = Path(vr.__file__)
    seed_sha256 = hashlib.sha256(seed.read_bytes()).hexdigest()
    candidate_sha256 = hashlib.sha256(candidate.read_bytes()).hexdigest()
    with redirect_stdout(sys.stderr):
        status = int(pytest.main([str(seed), "-q", "-p", "no:cacheprovider"]))
    if status:
        return status
    if (seed_sha256 != hashlib.sha256(seed.read_bytes()).hexdigest()
            or candidate_sha256 != hashlib.sha256(candidate.read_bytes()).hexdigest()):
        print("Seed or candidate changed during testing.", file=sys.stderr)
        return 1
    if args.mode == "execute":
        print(json.dumps({
            "mode": "execute",
            "seed_sha256": seed_sha256,
            "candidate_sha256": candidate_sha256,
            "result": vr.read_row(args.reply),
        }))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
