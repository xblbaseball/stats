# XBL Stats

* Python 3.10

Test with

```sh
python -m unittest discover tests/
```

Collect and parse stats with

```sh
python get-sheets.py
python main.py --season 18
```

If you change any of the models in `models.py`, update the equivalent TS types by doing the following:

```sh
# save JSON schemas from the models
python models.py
```
