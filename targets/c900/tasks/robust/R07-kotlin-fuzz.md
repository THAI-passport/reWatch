# R07: Kotlin core fuzz and property tests (tests only)

Kind: code. Time box: 2 h. You own: `results/R07.md`, `client/c900-android/core/src/test/kotlin/rewatch/c900/FuzzTest.kt`. Do not edit main sources.

## Setup
JDK 21, Gradle 8. `cd client/c900-android && gradle :core:test` must pass before you start (if Maven returns 429, wait and retry; do not change repositories).

## Tests to add (fixed seeds, kotlin.random.Random(seed))
1. `FrameReader.feed` with 10k random chunks (0-64 bytes): never throws except `Flood`; buffer never grows past 1024 + chunk.
2. `Frames.parse` on random bytes: never throws.
3. Round trip: every `Commands` builder over random valid inputs -> `parse` returns the same cmd/key/payload and ver.
4. Splitting: any valid frame fed in random splits yields exactly one identical result.
5. `CommandQueue`: random interleavings of submit/ack/tick/abortAll never leave two commands in flight, every submit gets exactly one result, writes never exceed the budget.
6. `Gatt.isDenied` is true for every UUID ending `dcca9e` or containing `5610`, false for the three command UUIDs.
7. `Commands.cutUtf8`: random Unicode strings never produce invalid UTF-8 and never exceed the limit.

## If a test finds a bug
Do not fix main code. Keep the test, annotate it `@Ignore("R07 bug: <one line>")`, and describe the input (seed) and failure in R07.md with a proposed fix.

## Done when
Suite runs green (ignored bug tests allowed, each documented), R07.md lists each property and result.
