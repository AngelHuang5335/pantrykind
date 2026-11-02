# Matching performance and limits

The catalogue reads available stock once, prefetches ingredients once and builds
an index keyed by normalised food name and compatible unit family. Each recipe
looks up its ingredient groups in that shared index. Its results copy batch lists,
so one result cannot mutate the index used by another recipe. Catalogue rendering
uses three SQL queries and displays 24 cards per page, while readiness filtering
and ranking still evaluate the full matching catalogue in memory.

```sh
python manage.py benchmark_matching --recipes 500 --items 2000 --runs 5
```

The command generates synthetic objects in memory and never inserts application
data. It compares rebuilding pantry totals for each recipe with a shared index,
including index construction in the timed region, and checks that readiness counts
agree. Each recipe has five measured ingredients over 100 distinct food names.

On the recorded Windows/Python 3.12.6 run, the median was 691.463ms rebuilding per
recipe and 5.796ms sharing the index. The [raw report](benchmarks/matching-windows-python312.json)
contains every sample, platform details and worst observed times. This comparison
is a local synthetic algorithm benchmark, not a claim about HTTP throughput,
database latency, concurrent users or production service-level guarantees.

The query-budget regression test renders both small and larger catalogues and
requires three queries. PostgreSQL race tests separately verify write correctness.
Large stock collections and recipe libraries still occupy memory; future scale
work should measure representative household sizes, request latency, contention
and process memory before introducing caching or asynchronous indexing.
