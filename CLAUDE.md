# CLAUDE.md

## Code Style

### General Principles

- Write clean, readable code. Prioritize clarity over cleverness.
- Functions should be short (aim for <20 lines in the body). If a function
  does two things, split it into two functions.
- Names must be descriptive and intention-revealing. No abbreviations unless
  they are universally understood in the domain (see *Files and Naming* for
  how a domain abbreviation is adopted).
- Names must be readable at the CALL SITE, not only at the declaration.
  `self.__iteration_factory.build(...)` narrates itself;
  `self.__factory.build(...)` forces the reader to click through to learn
  "factory of what?". Qualify a member's role whenever the bare noun leaves
  that question open.
- One narrated step per line: when a chained call's intermediate value has a
  meaningful name, split the chain and name it
  (`iteration = factory.build(...)` then `report = iteration.run()`), so a
  traceback points at the step that failed. Chains stay fine when the
  intermediate is nameless (`text.strip().lower()`).
- No magic numbers or string literals. Extract them into named constants or
  config fields.
- Prefer explicit over implicit. Never rely on side effects for control flow.
- No commented-out code. Remove dead code; git history preserves it.

### Type Annotations

- Type-annotate every function signature, every return type, and every class
  attribute. No exceptions.
- Use modern syntax: `list[X]`, `dict[K, V]`, `tuple[X, ...]`, `X | None`
  (not `List[X]`, `Optional[X]`). Write `torch.Tensor`, not bare `Tensor`.
- Use `X | None` only when `None` is a semantically meaningful value, not as
  a default-avoidance pattern.
- Use `Protocol` or `ABC` for structural/nominal typing of interfaces.
- Generic classes use `Generic[T]` with meaningful type variables.

### Classes and OOP

- Class members are **private** (`__` prefix) by default, **protected**
  (`_` prefix) when a subclass needs them, and exposed only through
  `@property` getters. Provide setters only when mutation is explicitly part
  of the design. Frozen dataclass fields are the exception: immutability
  already protects them, so they stay plain public fields.
- Use `@property` (not methods) for structural attributes that describe what
  an object IS (e.g., `n_features`, `input_dim`). The `()` on a method call
  implies an action or non-trivial computation.
- Use `@dataclass(frozen=True)` for all value objects and configuration.
  Mutable dataclasses need strong justification.
- Use `ABC` + `@abstractmethod` to define interfaces. Concrete implementations
  inherit from these.
- Use `Generic[T]` on ABCs when subclasses are parameterized by a type (e.g.,
  a factory generic over its params dataclass). Expose the concrete type via
  a `@property` returning `type[T]` so callers can construct instances
  without knowing the concrete subclass.
- Use inheritance when two classes share behavior that varies in one
  dimension: a base class holds the shared logic and an abstract method the
  varying part. Use composition when the relationship is "has-a".
- Use `enum.Enum` (or `enum.StrEnum`) for categorical choices, never raw
  strings.
- Each class has a single responsibility. If it does two unrelated things,
  split it.
- Implement `__repr__` on all public-facing classes (automatic for
  dataclasses).

### Functions

- Functions do one thing. If the name contains "and", it probably does two.
- Separate commands from queries, and let the VERB disclose the effect. A
  computational verb (`estimate_`, `compare_`, `assemble_`, `derive_`) means
  no effect beyond the return value; a method that persists or mutates says
  so (`record_`, `write_`, `save_`, `submit_`, `add_`, `narrow_to`). Never
  use the functional `with_*` prefix (returns a modified COPY) for an
  in-place mutation; a caller who kept the original gets silent corruption.
- Prefer pure functions (no side effects, deterministic) wherever possible.
  "Pure" is about effects, not placement: see *No free-floating functions*
  for where logic lives.
- Limit function arguments to 5 or fewer. If more are needed, group them into
  a config or dataclass.
- Use keyword-only arguments (after `*`) for any argument that is not
  self-evident from position.

### Error Handling

- Raise specific exceptions with informative messages. Never use bare
  `except:` or `except Exception:` without re-raising.
- Validate inputs at public API boundaries. Internal functions can trust
  their callers.
- Use custom exception classes for domain-specific errors (inherit from the
  appropriate built-in).
- Every validation message tells the caller how to fix the problem; see
  *Validation errors must contain the remediation*.

### Package Structure

- Organize code into clearly separated packages and sub-packages. Each
  package represents a coherent domain concept.
- Every package has an `__init__.py` that explicitly exports its public API
  via `__all__`.
- Avoid circular imports. If two modules need each other, extract the shared
  abstraction into a third module.
- Keep module files focused. A module with more than ~300 lines likely needs
  splitting.

### Files and Naming

- One module per substantial class, named after it: `IterationFactory` lives
  in `iteration_factory.py` and is tested in `test_iteration_factory.py`.
  Small definitions that exist only in service of that class (its params
  dataclass, a local enum, a domain exception, a private helper) live in the
  same module.
- Module basenames are unique across the whole package, so editor tabs,
  tracebacks, and grep are unambiguous. Do not rely on the package path to
  disambiguate: `heart_rate/features.py` beside `breathing_rate/features.py`
  is two files called `features.py`.
- When repeating the domain word makes names long
  (`heart_rate/heart_rate_features.py`), shorten it with an abbreviation
  that is standard in the domain and use that abbreviation consistently in
  package, module, and class: `hr/hr_features.py` holds `HrFeatures`,
  `br/br_features.py` holds `BrFeatures`. Expand the abbreviation once in
  the package's `__init__.py` docstring. An abbreviation adopted this way is
  the "universally understood in the domain" exception to the no-abbreviation
  rule; it is never introduced ad hoc in a single identifier.
- Falling back to the package path (`heart_rate/features.py`) is acceptable
  only when no standard abbreviation exists. Never mix both styles within one
  package.

---

## Architectural Design Principles

These are hard requirements, not style preferences. They prevent the design
drift that creates bugs and technical debt.

### A. Class shape and content

#### Classes must mirror the domain, not the implementation

Ask: "what is this thing mathematically / conceptually?" The fields and
methods match that answer, nothing more. If a mathematical object is defined
by X and Y, the class contains X and Y. Do not add Z because some algorithm
that consumes the object needs Z; that algorithm derives Z from X and Y, or
Z lives on the algorithm's side.

#### Design classes so misuse is structurally impossible

The test of a class design: how hard is it to construct or use one WRONGLY,
with inconsistent fields, out of context, or bypassing the invariants its
consumers rely on? Prefer designs where the illegal state cannot be expressed
at all over designs where it is merely documented away.

Two kinds of data-bearing classes get different constructor policies:

- A **value object**'s meaning is entirely in its fields: any combination
  that passes validation is legitimate, whoever built it. These are
  `@dataclass(frozen=True)` with an OPEN constructor plus a `__post_init__`
  that enforces every internal invariant (shape agreement, ranges,
  cross-field consistency).
- A **result object** additionally CLAIMS provenance ("this is what the
  fit/parser/resolver produced") and its fields can be individually valid
  yet jointly a lie. Close the front door: construction goes through the
  producer or a named factory (`between(...)`, `of_result(...)`,
  `parse(...)`); fields are keyword-only; and where the blast radius
  warrants it, use a plain class with protected members behind read-only
  properties, so no open constructor exists at all.

Rules that follow:

- **Invariants live on the TYPE, never only in the factory.** A check
  performed in `from_x()` but not in `__init__`/`__post_init__` is a check
  every direct construction silently skips. Factories DERIVE; the type
  ENFORCES.
- If a docstring needs to say "construct directly only in tests", the
  constructor wants to be closed: either enforce the invariants in
  `__post_init__` so direct construction is safe, or remove the open
  constructor.
- Make fields keyword-only (`kw_only=True`) whenever two fields share a
  type; positionally swapped same-type arguments are exactly the silent
  misuse this section prevents.
- Do not reach for producer-only construction by default: it costs the
  generated `__eq__`/`__repr__`, `dataclasses.replace`, and cheap test
  fixtures. Reserve it for objects whose claim cannot be validated from
  their own fields and whose misconstruction would flow into artifacts or
  decisions undetected. Where such a class must still evolve (a resumed fit
  extending its history), give it a NAMED evolution method rather than
  leaving `replace` as the mutation surface.

#### Distinguish structural properties from behavioral properties

A domain object has two kinds of information: what it IS (structure) and
what it DOES (behavior). Represent them separately, and do not conflate
derived properties with defining ones.

- If two properties seem related but can diverge in edge cases, they are
  separate concepts and are stored or computed independently.
- Properties computable from defining properties are derived `@property`
  methods, not redundant stored fields. If computation is expensive, cache.

#### Separate defining parameters from runtime inputs

The values that define what an object IS are distinguished from the inputs
it receives at execution time.

- A neural network is defined by its architecture and weights. The input
  tensor is an argument to `forward()`, not a constructor parameter.
- A domain model is defined by its structure and parameters. Runtime inputs
  (initial states, time spans, solver settings) are passed at the call site,
  not stored in the same config or params object.
- A factory's params dataclass contains only defining parameters.

This separation prevents conflation in sampling, serialization, and
composition.

#### No free-floating functions for logic that has state or identity

If a function constructs something, transforms something, or dispatches on
type, it belongs as a classmethod, factory method, or method on an enum.
Free functions are acceptable only for pure stateless utilities (math
helpers, tensor manipulation).

- A factory that selects a subclass based on an enum value is a method on
  the enum, or a classmethod on the base class.
- A function that closes over parameters and returns a callable becomes a
  callable class with `__call__`, so the captured parameters are inspectable
  via properties. Raw lambdas are acceptable only for throwaway one-liners
  in tests or examples, never in production code paths.

#### Parameters belong inside closures, not alongside them

When a function is parameterized (e.g., a scoring function with
coefficients), the parameters are captured at construction time, not passed
at every call site.

- Bad: `score_fn` and `score_params` as parallel fields, params passed to fn
  at every evaluation.
- Good: the scoring callable captures its params; the call site invokes
  `score(state)` with no extra arguments. The callable is a class (not a
  lambda) exposing a `.params` property for serialization and debugging.

### B. Typed interfaces over untyped data

#### String-keyed dicts are not a typed interface

`dict[str, float]` or `dict[str, Any]` configuration gives the caller no
type checking, no autocompletion, and no safe refactoring. A misspelled key
(`k_prodd` instead of `k_prod`) is a runtime `KeyError`, not a type error.

- More than two related parameters that could be misspelled are grouped into
  a frozen dataclass with named, typed fields.
- A factory that constructs objects from a parameter set takes a typed
  dataclass, not a dict, and is generic over the params type.
- The single place where string-keyed dicts become typed params is a
  dedicated `from_dict()` / `params_from_dict()` method. No other code
  indexes into a params dict by string key.
- Modules sharing parameter values need no special "sharing" machinery;
  Python variable binding of typed dataclass fields is sufficient.

#### Positional indexing into flat tensors is not an API

If a tensor has semantic slots (`params[0]` = rate_constant, `params[1]` =
k_m), the mapping is defined in exactly one place: a frozen dataclass with
`to_tensor()` / `from_tensor()`. No code outside that dataclass indexes into
the tensor by position.

### C. Constants and single source of truth

#### Structural constants belong inside the class

A constant intrinsic to a specific class is a `ClassVar` on that class, not
a module-level variable. Module-level constants are only for genuinely
module-wide values (a logger, a global registry). When several classes in
one module each have structural constants, module-level placement leaves it
ambiguous which constant belongs to which class. Constants callers might
customize are exposed through the constructor with the `ClassVar` as the
default.

#### Structural constants have a single source of truth

When a dimension, count, or schema is determined by one module and consumed
by another, define it once and have every consumer derive from it. Never
duplicate a constant across files, even if both agree today.

- If a feature vector has N channels, define an Enum listing the channels in
  the module that constructs the vector and export `N = len(TheEnum)`.
  Consumers import N.
- Never store structural constants (dimensions dictated by the data format)
  in config. Config is for hyperparameters the user chooses; a dimension
  dictated by the code is a derived property.
- If adding a channel requires changing more than two locations (the enum +
  the builder), the abstraction is leaking.
- Co-locate field metadata (valid range, unit, description) with the field
  via `dataclasses.field(metadata={...})`. A field name that appears in the
  dataclass and again in a separate metadata dict keyed by string is a
  duplication bug waiting to happen.

### D. Module boundaries and layering

#### Orthogonality: consumers must not know about producers

Modules depend on interfaces, not on each other.

- A downstream consumer (solver, encoder, renderer) accepts generic inputs
  (matrices, tensors, callables), not a domain object. The domain object
  provides what the consumer needs via a method; the consumer never imports
  the domain class.
- A neural network encoder consumes a tensor representation, not a symbolic
  domain object. The symbolic-to-tensor conversion happens at an explicit
  boundary (a dedicated converter module), not inside the encoder.

#### Translate at boundaries; do not modify endpoints to fit each other

When two modules disagree on a convention (frame, units, schema), the fix is
a translator class at the boundary, not a patch to either endpoint. The
endpoints stay correct in their own domain; the translator is the only place
that knows both. Even when an endpoint *could* internalize the conversion
via a flag, prefer the external translator so the boundary is named.

- Translators carry the assumption in their name (`MetricToImperialAdapter`
  wrapping a metric sensor for an imperial consumer), so the cost of the
  translation is visible at the call site.
- A configurable convention on one endpoint is a smell: it becomes a global
  setting propagating through every call. Multiple thin translators are
  healthier.
- The endpoint to leave alone is the one correct in its own domain: a
  third-party library staying bit-exact with upstream, a data source
  faithfully representing its format.

#### Shared utilities live in neutral modules; layering must not invert

When two sibling packages need the same helper, move it to a shared, neutral
module rather than reaching across package boundaries or duplicating it.

- A library package never imports from an application package. If a library
  needs something an application provides, that something is mis-located.
- Inlining a small helper into a second consumer to avoid the refactor is
  technical debt: the day the two copies diverge silently, the bug ships.
- "Neutral" means the module sits at or above the level of every consumer
  in the dependency graph, e.g. `<project_root>/<helper>.py`, not inside one
  of the siblings.

#### Organize by dependency layer, not by feature slice, when components are coupled

Feature slices (one package per feature, each owning its types, logic, and
API) work only when features are independent. When components exchange
data, form a pipeline, or feed back into each other, feature-slicing forces
them to import one another and the graph tangles. Decompose by layer:

- Shared **data types and contracts** go *down* into a core layer everything
  depends on.
- Shared **algorithms** go *down* into a layer written against the core
  types only.
- The **wiring** that composes components into a pipeline goes *up* into an
  orchestration layer.
- Feature/domain modules sit in between, each depending only on layers
  below it, never on a sibling.

**A feedback loop in data flow must never become a cycle in the code
dependency graph.** If A produces what B consumes and B produces what A
consumes, define the exchanged objects in the core layer; both depend on
core; an orchestrator on top closes the loop. The whole graph is a DAG.
Decomposition test: can two components be built and tested without
importing each other? If not, the shared part has not been pushed far
enough down. Add an import-linter to CI so a layer violation fails the
build.

#### Never import private symbols across module boundaries

A leading underscore means internal to its module. Other modules never
import it.

- To dispatch on the type of an object from another module, use a protocol
  (`hasattr` check), a registry keyed on a public type (e.g., the params
  dataclass), or a method on the object itself. Never `isinstance` against a
  private class from another module.
- If you find yourself importing `_FooBar` from another module, stop. Either
  make it public and commit to the interface, or redesign so the import is
  unnecessary.

#### Notebooks and scripts must use the library, not reimplement it

More than 10 lines of notebook logic duplicating a library class (e.g., a
training loop that mirrors the Trainer) is a bug. Call the public API; if
the API does not support what the notebook needs, extend the API.

- Trainer returns a result object that notebooks can plot directly.
- A custom training variant subclasses the Trainer or passes configuration;
  it does not copy-paste the loop.

### E. Validation and errors

#### No silent fallbacks for missing data

If a loss requires M >= 2 samples to compute variance and receives M = 1, it
raises `ValueError`; it does not return zero. Silent fallbacks hide bugs.

- Never return a zero tensor as a "safe default" for a loss that cannot be
  computed. That is a gradient dead zone invisible during training.
- Never silently squeeze, unsqueeze, or reshape tensors to make shapes match.
  Raise a clear error stating expected and actual shapes.
- When dispatching on a capability via `hasattr` or `Protocol`, the branch
  for an object lacking the capability raises unless the fallback behavior
  is provably correct. A plausible but incorrect result is worse than a
  crash.

#### Validation errors must contain the remediation

When a class rejects an input, the exception message tells the caller
exactly how to fix it. "X is not Y" is insufficient; "X is not Y. Wrap it
in `Z(...)`." is the minimum bar. This matters most at numerically critical
boundaries (frame conventions, units, schemas), where the alternative to a
clear error is a silent wrong output.

- The reader of the error never needs to open the source. Include the
  remediation snippet, the suggested adapter, or the exact config change.
- Pair with type-tagged contracts (enums, properties) so mismatches are
  caught at construction, not after data has flowed.
- Never auto-correct silently. The user should see the wrap / convert / cast
  in their own code; auto-correction is exactly the silent-bug pattern this
  rule prevents.

### F. ML / Neural network specifics

#### Prefer computable features over manual annotations for ML inputs

Feed the encoder features derived from the existing data structure rather
than manually annotated categories.

- Derived features (graph connectivity, statistical summaries, structural
  properties) are always consistent with the data, cannot be mislabeled, and
  generalize to novel structures.
- Manual annotations require domain expertise, are incomplete by nature, and
  let the model shortcut structural learning by memorizing labels.
- If the encoder cannot distinguish important cases from structure alone,
  enrich the computable features (edge features, sensitivity estimates)
  before resorting to annotations.

#### Network architecture details must be configurable, not hardcoded

Layer counts, hidden dimensions, activations, and conditioning strategies
are hyperparameters. They live in config dataclasses, not in constructor
bodies.

- Never write out a fixed sequence of `nn.Linear` / activation pairs. Loop
  over an `n_hidden_layers` config value and store layers in
  `nn.ModuleList`.
- Extract a recurring pattern ("MLP with conditioning at every layer") into
  its own `nn.Module` class. Networks sharing a pattern are instances of
  that class, not copy-pasted `nn.Sequential` blocks.
- Conditioning (FiLM, concatenation, cross-attention) is applied at every
  hidden layer, not only at the output. Output-only conditioning restricts
  the network to context-independent intermediate features.

#### Train sequential models on one-step objectives first

For models that generate sequences (trajectories, time series,
autoregressive outputs), the primary training objective is a one-step
prediction loss with teacher forcing. Full-rollout losses are for validation
and optional fine-tuning.

- Full rollout compounds early errors; by step T the model is far from the
  training distribution and gradients are noisy.
- Teacher forcing keeps every training step on-distribution.
- When the model defines a tractable per-step likelihood (e.g., Gaussian
  transitions in an Euler-Maruyama SDE), use the negative log-likelihood as
  the loss. It trains mean and variance jointly and removes arbitrary
  loss-weighting hyperparameters.
- To bridge teacher-forced training and free-running inference, use
  scheduled sampling: start at 100% teacher forcing and gradually increase
  the fraction of steps that use the model's own predictions.

---

## Documentation

- **Docstrings**: Google style on all public classes, methods, and functions,
  with `Args:`, `Returns:`, and `Raises:` sections where applicable.
- Private/protected methods get a one-line docstring explaining intent,
  unless the name is fully self-documenting.
- Module-level docstrings at the top of each `.py` file explain the module's
  purpose in one to three sentences.
- No docstrings that restate the name (`"""Gets the name."""` on
  `get_name`).

---

## Testing

### Structure

Tests mirror the source tree exactly: `src/<package>/foo/bar.py` has
`tests/foo/test_bar.py`. Because modules are named after their class, each
substantial class gets its own test module. Every test directory has an
`__init__.py`.

### Philosophy

- **Test external interfaces, not internal behavior.** Test a private
  (`_`-prefixed) method through the public method that calls it.
- **Tests explain why they exist.** Names state the contract verified:
  `test_exponential_decay_matches_analytical`.
- **Use analytical references for numerical tests**, not
  cross-implementation comparisons.
- **Statistical tests use wide tolerances** and enough samples to keep the
  flaky failure rate below 1%.
- **Do not test trivial behavior.** Dataclass field defaults, enum string
  values, and `__repr__` need no tests. Test validation logic
  (`__post_init__` that raises on invalid inputs).

### Fixtures and Stubs

- `conftest.py` files provide stubs that satisfy interfaces without
  importing heavyweight modules.
- Downstream component tests do NOT depend on upstream components being
  correct; use fakes or stubs to isolate.
- Prefer factory fixtures over mutable shared state.

### Conventions

- Use `pytest`. No unittest-style classes unless grouping is genuinely
  needed.
- Use `pytest.mark.parametrize` for the same logic across multiple inputs.
- Use `pytest.approx` or `torch.testing.assert_close` with explicit
  tolerances for numerical comparisons.
- Guard tests that depend on optional packages with `pytest.mark.skipif`.
- All tests are fast (<5 seconds each), use tiny configs and minimal data,
  and run on CPU only.

### What to prioritize when writing new tests

1. **Data pipeline correctness** (corrupted inputs silently poison
   everything downstream).
2. **Loss function numerics** (sign/normalization bugs are silent and
   devastating).
3. **Interface contracts** (type hierarchy, protocol compliance, batch vs.
   single-item consistency).
4. **Factory/builder correctness** (config-to-object mapping dispatches to
   the correct classes).

### What to skip

- `__repr__` methods and dataclass field defaults (unless validation logic
  exists).
- Full training loop integration (too slow for unit tests).
- External service integrations (require live credentials).

---

## PyTorch Conventions

- All `nn.Module` subclasses call `super().__init__()` first.
- Define sub-modules in `__init__`, compute in `forward`. No module creation
  inside `forward`.
- Name tensor dimensions in comments where shapes are non-obvious:
  `# (batch, n_features, d_model)`.
- Use `torch.no_grad()` explicitly for inference and evaluation.
- Prefer `torch.nn.functional` for stateless operations; use `nn.Module`
  wrappers for stateful ones (layers with parameters).
- **Never loop over a batch dimension in Python.** If the same operation
  applies to N independent items, reshape them into one batch tensor and run
  one forward pass. Python loops launch thousands of tiny kernels; one
  batched operation launches one, typically 10-100x faster. To support both
  single-item and batched input, branch on `dim()` at the entry point, not
  by looping internally.

---

## Git Practices

- Commit messages are imperative and concise: "Add data loader", not "Added
  the data loader".
- One logical change per commit. Do not mix refactoring with feature
  additions.
- Run `uv run tox` (or at minimum `uv run pytest` + `uv run tox -e lint`)
  before every commit. Commit `uv.lock` whenever dependencies change.
