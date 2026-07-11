# RealSpec B1/B2/M Summary

Rows=309

## Mean Conf by mode
```json
{
  "B1": 0.9029,
  "B2": 1.0,
  "M": 1.0
}
```

## By source_type × mode
```json
{
  "industrial_pattern|B1": 0.8387,
  "industrial_pattern|B2": 1.0,
  "industrial_pattern|M": 1.0,
  "published_case|B1": 0.9,
  "published_case|B2": 1.0,
  "published_case|M": 1.0,
  "real_derived|B1": 0.925,
  "real_derived|B2": 1.0,
  "real_derived|M": 1.0,
  "textbook|B1": 0.9545,
  "textbook|B2": 1.0,
  "textbook|M": 1.0
}
```

## Reading for C4
If B2 >= M on mean Conf for industrial/textbook slices, that supports default-B2.
If M leads only on a source_type, escalate selectively.
