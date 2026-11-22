# Verdict reader test

The reader takes a short reply to a numbered list and returns a verdict for each item. For example, in
`approve 1, reject 2`, item 1 is approved and item 2 is denied.

## What the tests cover

- Verdicts attach to numbered items, groups, and short ranges.
- A number may touch its verdict word. A time or decimal does not count as an item number.
- Four-digit item identifiers can name their corresponding list items.
- A one-letter typo in an approval word can still count. Ordinary words such as `approval` and `approver` keep their meaning.
- The returned result records how the reply was read, including whether it used number-first or verb-first order.

## Rebuild and run

Use the rules and assertions in `rebuild_the_verdict_reader_from_its_test__mira_intent_os__when_any_model_rebuilds_the_seed__v001__20261121__lc_seed_release__active.py` to write `verdict_reader.py` in the same directory. The reader uses the Python standard library. Install pytest and run all eight checks.

```sh
python -m pip install pytest
python rebuild_the_verdict_reader_from_its_test__mira_intent_os__when_any_model_rebuilds_the_seed__v001__20261121__lc_seed_release__active.py test
```

To read a fresh reply, use execution mode. It first runs the same eight checks. A failing reader returns no verdict.

```sh
python rebuild_the_verdict_reader_from_its_test__mira_intent_os__when_any_model_rebuilds_the_seed__v001__20261121__lc_seed_release__active.py execute "approve 1, reject 2"
```

888  christ is king
