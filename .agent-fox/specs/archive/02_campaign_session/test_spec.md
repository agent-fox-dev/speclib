# Test Specification: Campaign Management and Spec Authoring Session Model

## Overview

Tests validate campaign directory management, spec authoring session state
machine, session persistence, and delegation to afspec for validation and
rendering. Test cases map 1:1 to requirements; property tests verify state
machine and persistence invariants.

## Test Cases

### TS-02-1: Campaign creation with valid path

**Requirement:** 02-REQ-1.1
**Type:** unit
**Description:** Verify that `Campaign.create(path, name, description)` creates the directory, writes `campaign.yaml`, and returns a `Campaign` instance.

**Preconditions:**
- Temp directory with a non-existent subdirectory as target

**Input:**
- Call `Campaign.create(tmp / "my_campaign", "Test Campaign", "A test")`

**Expected:**
- Target directory exists
- `campaign.yaml` exists within it
- Returned Campaign instance has matching metadata
- `campaign.path` equals the target path

**Assertion pseudocode:**
```
camp = Campaign.create(tmp / "my_campaign", "Test Campaign", "A test")
ASSERT (tmp / "my_campaign").is_dir()
ASSERT (tmp / "my_campaign" / "campaign.yaml").exists()
ASSERT camp.metadata.name == "Test Campaign"
ASSERT camp.metadata.description == "A test"
ASSERT camp.path == tmp / "my_campaign"
```

### TS-02-2: Campaign creation fails on existing campaign

**Requirement:** 02-REQ-1.2
**Type:** unit
**Description:** Verify that creating a campaign where `campaign.yaml` already exists raises `CampaignError`.

**Preconditions:**
- Directory already contains `campaign.yaml`

**Input:**
- Call `Campaign.create(existing_campaign_path, "New", "Duplicate")`

**Expected:**
- `CampaignError` raised
- Error message indicates campaign already exists

**Assertion pseudocode:**
```
Campaign.create(path, "First", "Original")
ASSERT raises(CampaignError, lambda: Campaign.create(path, "Second", "Duplicate"))
ASSERT "already exists" in str(error)
```

### TS-02-3: campaign.yaml contains required fields

**Requirement:** 02-REQ-1.3
**Type:** unit
**Description:** Verify `campaign.yaml` contains name, description, created_at, and updated_at fields.

**Preconditions:**
- Freshly created campaign

**Input:**
- Parse `campaign.yaml` from the campaign directory

**Expected:**
- YAML contains `name`, `description`, `created_at`, `updated_at`
- `created_at` and `updated_at` are valid ISO 8601 strings

**Assertion pseudocode:**
```
camp = Campaign.create(path, "Test", "Desc")
data = yaml.safe_load((path / "campaign.yaml").read_text())
ASSERT data["name"] == "Test"
ASSERT data["description"] == "Desc"
ASSERT "created_at" in data
ASSERT "updated_at" in data
ASSERT datetime.fromisoformat(data["created_at"]) is not None
ASSERT datetime.fromisoformat(data["updated_at"]) is not None
```

### TS-02-4: Campaign.open with valid campaign directory

**Requirement:** 02-REQ-2.1
**Type:** unit
**Description:** Verify that `Campaign.open(path)` reads `campaign.yaml` and returns a Campaign with populated metadata.

**Preconditions:**
- Campaign previously created at path

**Input:**
- Call `Campaign.open(path)`

**Expected:**
- Returns Campaign instance
- Metadata matches values written at creation time

**Assertion pseudocode:**
```
Campaign.create(path, "My Camp", "Testing")
camp = Campaign.open(path)
ASSERT camp.metadata.name == "My Camp"
ASSERT camp.metadata.description == "Testing"
ASSERT camp.path == path
```

### TS-02-5: campaign.specs() returns sorted spec directories

**Requirement:** 02-REQ-2.2
**Type:** unit
**Description:** Verify that `specs()` returns spec subdirectories sorted by numeric prefix, excluding non-spec directories.

**Preconditions:**
- Campaign with multiple spec subdirectories and an `archive/` directory

**Input:**
- Create specs "alpha" and "beta", and an `archive/` dir
- Call `campaign.specs()`

**Expected:**
- Returns list of two Path objects
- Sorted by numeric prefix (01 before 02)
- Excludes `archive/`

**Assertion pseudocode:**
```
camp = Campaign.create(path, "Test", "Desc")
camp.new_spec("alpha", "PRD content")
camp.new_spec("beta", "PRD content 2")
(path / "archive").mkdir()
specs = camp.specs()
ASSERT len(specs) == 2
ASSERT specs[0].name == "01_alpha"
ASSERT specs[1].name == "02_beta"
```

### TS-02-6: new_spec with string PRD creates spec directory

**Requirement:** 02-REQ-3.1
**Type:** unit
**Description:** Verify `new_spec()` with a string PRD creates the directory, writes `prd.md`, writes `_session.json`, and returns a SpecSession.

**Preconditions:**
- Existing campaign

**Input:**
- Call `campaign.new_spec("my_spec", "# My PRD\n\nContent here")`

**Expected:**
- Spec directory `01_my_spec` created
- `prd.md` exists with frontmatter and PRD content
- `_session.json` exists with `init` state
- Returned SpecSession is in `init` state

**Assertion pseudocode:**
```
camp = Campaign.create(path, "Test", "Desc")
session = camp.new_spec("my_spec", "# My PRD\n\nContent here")
spec_dir = path / "01_my_spec"
ASSERT spec_dir.is_dir()
ASSERT (spec_dir / "prd.md").exists()
ASSERT "Content here" in (spec_dir / "prd.md").read_text()
ASSERT (spec_dir / "_session.json").exists()
ASSERT session.state == SessionState.INIT
```

### TS-02-7: new_spec with Path PRD copies file content

**Requirement:** 02-REQ-3.2
**Type:** unit
**Description:** Verify `new_spec()` with a Path PRD copies the file content into `prd.md`.

**Preconditions:**
- Existing campaign
- PRD file exists at a separate path

**Input:**
- Create a temp file with PRD content
- Call `campaign.new_spec("from_file", Path(prd_file))`

**Expected:**
- `prd.md` in spec directory contains the original file's content

**Assertion pseudocode:**
```
prd_file = tmp / "source_prd.md"
prd_file.write_text("# Source PRD\n\nOriginal content")
camp = Campaign.create(path, "Test", "Desc")
session = camp.new_spec("from_file", prd_file)
prd_text = (path / "01_from_file" / "prd.md").read_text()
ASSERT "Original content" in prd_text
```

### TS-02-8: Spec directory naming with sequential prefixes

**Requirement:** 02-REQ-3.3
**Type:** unit
**Description:** Verify spec directories use sequential numeric prefixes starting from 01.

**Preconditions:**
- Existing campaign

**Input:**
- Create three specs in sequence

**Expected:**
- Directories named `01_first`, `02_second`, `03_third`

**Assertion pseudocode:**
```
camp = Campaign.create(path, "Test", "Desc")
camp.new_spec("first", "PRD 1")
camp.new_spec("second", "PRD 2")
camp.new_spec("third", "PRD 3")
specs = camp.specs()
ASSERT specs[0].name == "01_first"
ASSERT specs[1].name == "02_second"
ASSERT specs[2].name == "03_third"
```

### TS-02-9: Generated prd.md has required frontmatter

**Requirement:** 02-REQ-3.4
**Type:** unit
**Description:** Verify the generated `prd.md` includes required YAML frontmatter fields.

**Preconditions:**
- Existing campaign

**Input:**
- Create a spec with string PRD
- Parse the frontmatter of the generated `prd.md`

**Expected:**
- Frontmatter contains `spec_id`, `spec_name`, `title`, `status: draft`, `created_at`, `updated_at`, `owner`, `source`, `schema_version: 1`

**Assertion pseudocode:**
```
camp = Campaign.create(path, "Test", "Desc")
camp.new_spec("my_spec", "# My Spec PRD")
prd_text = (path / "01_my_spec" / "prd.md").read_text()
frontmatter = parse_yaml_frontmatter(prd_text)
ASSERT frontmatter["spec_id"] == "01"
ASSERT frontmatter["spec_name"] == "my_spec"
ASSERT frontmatter["status"] == "draft"
ASSERT frontmatter["schema_version"] == 1
ASSERT "created_at" in frontmatter
ASSERT "updated_at" in frontmatter
```

### TS-02-10: SessionState enum values

**Requirement:** 02-REQ-4.1
**Type:** unit
**Description:** Verify SessionState enum has all six required values.

**Preconditions:**
- None

**Input:**
- Import SessionState

**Expected:**
- Has values: init, assessing, refining, prd_accepted, generating, generated

**Assertion pseudocode:**
```
from speclib.session import SessionState
ASSERT SessionState.INIT.value == "init"
ASSERT SessionState.ASSESSING.value == "assessing"
ASSERT SessionState.REFINING.value == "refining"
ASSERT SessionState.PRD_ACCEPTED.value == "prd_accepted"
ASSERT SessionState.GENERATING.value == "generating"
ASSERT SessionState.GENERATED.value == "generated"
ASSERT len(SessionState) == 6
```

### TS-02-11: Legal state transitions are enforced

**Requirement:** 02-REQ-4.2
**Type:** unit
**Description:** Verify each legal transition succeeds and each illegal transition raises SessionError.

**Preconditions:**
- Session in each possible state

**Input:**
- Attempt each method call from each state

**Expected:**
- Legal transitions succeed (or raise NotImplementedError for stub methods)
- Illegal transitions raise SessionError

**Assertion pseudocode:**
```
# Legal: init -> assessing via assess()
session = create_session_in_state("init")
ASSERT raises(NotImplementedError, session.assess)
# The state check happens BEFORE the NotImplementedError

# Illegal: init -> refining
session = create_session_in_state("init")
ASSERT raises(SessionError, lambda: session.refine({}))

# Illegal: init -> generating
session = create_session_in_state("init")
ASSERT raises(SessionError, session.generate)
```

### TS-02-12: Illegal state transition error message

**Requirement:** 02-REQ-4.3
**Type:** unit
**Description:** Verify SessionError names the current state and the required state.

**Preconditions:**
- Session in `init` state

**Input:**
- Call `session.generate()` (requires `prd_accepted`)

**Expected:**
- SessionError raised
- Message contains current state name and required state name

**Assertion pseudocode:**
```
session = create_session_in_state("init")
try:
    session.generate()
except SessionError as e:
    ASSERT "init" in str(e)
    ASSERT "prd_accepted" in str(e)
```

### TS-02-13: accept_prd() transitions from assessing or refining

**Requirement:** 02-REQ-4.4
**Type:** unit
**Description:** Verify `accept_prd()` works from both `assessing` and `refining` states.

**Preconditions:**
- Session in `assessing` state; session in `refining` state

**Input:**
- Call `accept_prd()` from each state

**Expected:**
- State transitions to `prd_accepted` in both cases

**Assertion pseudocode:**
```
session_a = create_session_in_state("assessing")
session_a.accept_prd()
ASSERT session_a.state == SessionState.PRD_ACCEPTED

session_r = create_session_in_state("refining")
session_r.accept_prd()
ASSERT session_r.state == SessionState.PRD_ACCEPTED
```

### TS-02-14: State persisted on transition

**Requirement:** 02-REQ-5.1
**Type:** unit
**Description:** Verify `_session.json` is updated on every state transition.

**Preconditions:**
- Session created in a spec directory

**Input:**
- Call `accept_prd()` from `assessing` state
- Read `_session.json` from disk

**Expected:**
- JSON file contains `"state": "prd_accepted"`

**Assertion pseudocode:**
```
session = create_session_in_state("assessing")
session.accept_prd()
data = json.loads((session.spec_dir / "_session.json").read_text())
ASSERT data["state"] == "prd_accepted"
```

### TS-02-15: Session resume restores state

**Requirement:** 02-REQ-5.2
**Type:** unit
**Description:** Verify `SpecSession.resume()` restores session state from `_session.json`.

**Preconditions:**
- Session created with some state transitions applied

**Input:**
- Create session, transition to `prd_accepted`, then resume from disk

**Expected:**
- Resumed session is in `prd_accepted` state
- Assessment history and Q&A exchanges are restored

**Assertion pseudocode:**
```
session = create_session_in_state("assessing")
session.accept_prd()
resumed = SpecSession.resume(session.spec_dir)
ASSERT resumed.state == SessionState.PRD_ACCEPTED
ASSERT resumed.spec_dir == session.spec_dir
```

### TS-02-16: _session.json contains required fields

**Requirement:** 02-REQ-5.3
**Type:** unit
**Description:** Verify `_session.json` contains all required fields.

**Preconditions:**
- Session created in a spec directory

**Input:**
- Read `_session.json` from the spec directory

**Expected:**
- Contains: state, prd_path, assessment_history, qa_exchanges, generated_artifacts, mode

**Assertion pseudocode:**
```
camp = Campaign.create(path, "Test", "Desc")
session = camp.new_spec("test_spec", "PRD content")
data = json.loads((session.spec_dir / "_session.json").read_text())
ASSERT "state" in data
ASSERT "prd_path" in data
ASSERT "assessment_history" in data
ASSERT "qa_exchanges" in data
ASSERT "generated_artifacts" in data
ASSERT "mode" in data
```

### TS-02-17: validate() with all artifacts present

**Requirement:** 02-REQ-6.1
**Type:** unit
**Description:** Verify `validate()` loads the spec via afspec and returns a ValidationResult.

**Preconditions:**
- Spec directory with all four required artifacts (prd.md, requirements.md, design.md, test_spec.md)

**Input:**
- Call `session.validate()` with mocked afspec

**Expected:**
- Returns `ValidationResult` with `valid` field and error lists
- afspec `load_spec` and `validate` were called

**Assertion pseudocode:**
```
session = create_session_with_all_artifacts()
with mock(afspec, "load_spec"), mock(afspec, "validate"):
    result = session.validate()
ASSERT isinstance(result, ValidationResult)
ASSERT isinstance(result.valid, bool)
ASSERT isinstance(result.schema_errors, list)
ASSERT isinstance(result.integrity_errors, list)
```

### TS-02-18: render(combined=True) returns combined markdown

**Requirement:** 02-REQ-6.2
**Type:** unit
**Description:** Verify `render(combined=True)` returns a single markdown string from afspec.

**Preconditions:**
- Spec directory with all four required artifacts

**Input:**
- Call `session.render(combined=True)` with mocked afspec

**Expected:**
- Returns a string (combined markdown)

**Assertion pseudocode:**
```
session = create_session_with_all_artifacts()
with mock(afspec, "load_spec"), mock(afspec, "render_combined", return_value="# Combined"):
    result = session.render(combined=True)
ASSERT isinstance(result, str)
ASSERT len(result) > 0
```

### TS-02-19: render(combined=False) returns artifact dict

**Requirement:** 02-REQ-6.3
**Type:** unit
**Description:** Verify `render(combined=False)` returns a dict mapping artifact names to markdown.

**Preconditions:**
- Spec directory with all four required artifacts

**Input:**
- Call `session.render(combined=False)` with mocked afspec

**Expected:**
- Returns a dict with string keys and string values

**Assertion pseudocode:**
```
session = create_session_with_all_artifacts()
with mock(afspec, "load_spec"), mock(afspec, "render_individual", return_value={"prd": "..."}):
    result = session.render(combined=False)
ASSERT isinstance(result, dict)
ASSERT all(isinstance(k, str) and isinstance(v, str) for k, v in result.items())
```

## Property Test Cases

### TS-02-P1: State machine transitions are total and exclusive

**Property:** Property 1 from design.md
**Validates:** 02-REQ-4.2, 02-REQ-4.3
**Type:** property
**Description:** For any session state and method call, the result is either a successful transition to a defined target state or a SessionError. No other outcome is possible (excluding NotImplementedError for stubs).

**For any:** SessionState value `s`, method `m` in {assess, refine, accept_prd, generate}
**Invariant:** Either the transition is legal (state changes to defined target) or SessionError is raised

**Assertion pseudocode:**
```
LEGAL = {
    ("init", "assess"): "assessing",
    ("assessing", "refine"): "refining",
    ("assessing", "accept_prd"): "prd_accepted",
    ("refining", "assess"): "assessing",
    ("refining", "accept_prd"): "prd_accepted",
    ("prd_accepted", "generate"): "generating",
}
FOR ANY state IN SessionState:
    FOR ANY method IN ["assess", "refine", "accept_prd", "generate"]:
        session = create_session_in_state(state)
        IF (state, method) IN LEGAL:
            # Legal transition - may raise NotImplementedError for stubs
            # but state check passes
            try:
                getattr(session, method)()
                ASSERT session.state == LEGAL[(state, method)]
            except NotImplementedError:
                pass  # stub — state check passed
        ELSE:
            ASSERT raises(SessionError, getattr(session, method))
```

### TS-02-P2: Session persistence is idempotent on resume

**Property:** Property 2 from design.md
**Validates:** 02-REQ-5.1, 02-REQ-5.2
**Type:** property
**Description:** For any session that has undergone valid transitions, persisting and resuming produces an equivalent session.

**For any:** sequence of legal transitions from `init`
**Invariant:** resumed session has same state and spec_dir as the original

**Assertion pseudocode:**
```
FOR ANY transition_sequence IN valid_transition_sequences():
    session = create_new_session()
    apply_transitions(session, transition_sequence)
    resumed = SpecSession.resume(session.spec_dir)
    ASSERT resumed.state == session.state
    ASSERT resumed.spec_dir == session.spec_dir
```

### TS-02-P3: Spec directory numbering is monotonically increasing

**Property:** Property 3 from design.md
**Validates:** 02-REQ-3.3
**Type:** property
**Description:** For any number of specs created sequentially, prefixes are 01, 02, ..., n with no gaps.

**For any:** n in range(1, 20)
**Invariant:** specs() returns paths with prefixes 01 through n in order

**Assertion pseudocode:**
```
FOR ANY n IN integers(min_value=1, max_value=20):
    camp = Campaign.create(tmp / f"camp_{n}", "Test", "Desc")
    FOR i IN range(n):
        camp.new_spec(f"spec_{ascii_lowercase[i]}", f"PRD {i}")
    specs = camp.specs()
    ASSERT len(specs) == n
    FOR i, spec_path IN enumerate(specs):
        prefix = int(spec_path.name.split("_")[0])
        ASSERT prefix == i + 1
```

### TS-02-P4: Campaign.create is atomic with respect to campaign.yaml

**Property:** Property 4 from design.md
**Validates:** 02-REQ-1.1, 02-REQ-1.2, 02-REQ-1.E1
**Type:** property
**Description:** After a successful create, campaign.yaml exists with correct content; after a failed create, no campaign.yaml is introduced.

**For any:** valid name and description strings
**Invariant:** success implies campaign.yaml exists and matches; failure implies no campaign.yaml added

**Assertion pseudocode:**
```
FOR ANY name IN text(min_size=1, max_size=50):
    FOR ANY desc IN text(min_size=0, max_size=200):
        path = tmp / "test_campaign"
        camp = Campaign.create(path, name, desc)
        data = yaml.safe_load((path / "campaign.yaml").read_text())
        ASSERT data["name"] == name
        ASSERT data["description"] == desc
```

### TS-02-P5: validate() and render() require all four artifacts

**Property:** Property 5 from design.md
**Validates:** 02-REQ-6.1, 02-REQ-6.E1
**Type:** property
**Description:** For any subset of the four required artifacts that is not the full set, validate() and render() raise SessionError.

**For any:** strict subset S of {prd.md, requirements.md, design.md, test_spec.md}
**Invariant:** SessionError raised listing the missing artifacts

**Assertion pseudocode:**
```
ARTIFACTS = {"prd.md", "requirements.md", "design.md", "test_spec.md"}
FOR ANY subset IN strict_subsets(ARTIFACTS):
    session = create_session_with_artifacts(subset)
    missing = ARTIFACTS - subset
    ASSERT raises(SessionError, session.validate)
    ASSERT all(name in str(error) for name in missing)
```

### TS-02-P6: accept_prd() is only callable from assessing or refining

**Property:** Property 6 from design.md
**Validates:** 02-REQ-4.4
**Type:** property
**Description:** accept_prd() succeeds only from assessing or refining; all other states raise SessionError.

**For any:** SessionState value
**Invariant:** accept_prd() succeeds iff state is assessing or refining

**Assertion pseudocode:**
```
FOR ANY state IN SessionState:
    session = create_session_in_state(state)
    IF state IN {SessionState.ASSESSING, SessionState.REFINING}:
        session.accept_prd()
        ASSERT session.state == SessionState.PRD_ACCEPTED
    ELSE:
        ASSERT raises(SessionError, session.accept_prd)
```

## Edge Case Tests

### TS-02-E1: Create campaign in non-empty non-campaign directory

**Requirement:** 02-REQ-1.E1
**Type:** unit
**Description:** Verify CampaignError when target directory exists, is non-empty, but has no campaign.yaml.

**Preconditions:**
- Directory exists with some files but no campaign.yaml

**Input:**
- Call `Campaign.create(path, "Test", "Desc")`

**Expected:**
- CampaignError raised indicating directory not empty and not a campaign

**Assertion pseudocode:**
```
path = tmp / "non_empty"
path.mkdir()
(path / "random_file.txt").write_text("stuff")
ASSERT raises(CampaignError, lambda: Campaign.create(path, "Test", "Desc"))
```

### TS-02-E2: Create campaign when parent directory missing

**Requirement:** 02-REQ-1.E2
**Type:** unit
**Description:** Verify CampaignError when the target path's parent does not exist.

**Preconditions:**
- Parent directory does not exist

**Input:**
- Call `Campaign.create(tmp / "nonexistent" / "child", "Test", "Desc")`

**Expected:**
- CampaignError raised indicating parent directory does not exist

**Assertion pseudocode:**
```
ASSERT raises(
    CampaignError,
    lambda: Campaign.create(tmp / "nonexistent" / "child", "Test", "Desc")
)
```

### TS-02-E3: Open non-campaign directory

**Requirement:** 02-REQ-2.E1
**Type:** unit
**Description:** Verify CampaignError when opening a directory without campaign.yaml.

**Preconditions:**
- Directory exists but has no campaign.yaml

**Input:**
- Call `Campaign.open(path)`

**Expected:**
- CampaignError raised

**Assertion pseudocode:**
```
path = tmp / "not_campaign"
path.mkdir()
ASSERT raises(CampaignError, lambda: Campaign.open(path))
```

### TS-02-E4: Open campaign with invalid YAML

**Requirement:** 02-REQ-2.E2
**Type:** unit
**Description:** Verify CampaignError when campaign.yaml contains invalid YAML.

**Preconditions:**
- Directory with campaign.yaml containing invalid YAML

**Input:**
- Call `Campaign.open(path)`

**Expected:**
- CampaignError raised with parse error detail

**Assertion pseudocode:**
```
path = tmp / "bad_yaml"
path.mkdir()
(path / "campaign.yaml").write_text(":::invalid yaml{{{")
ASSERT raises(CampaignError, lambda: Campaign.open(path))
```

### TS-02-E5: new_spec with invalid spec_name

**Requirement:** 02-REQ-3.E1
**Type:** unit
**Description:** Verify CampaignError for spec names with invalid characters.

**Preconditions:**
- Existing campaign

**Input:**
- Call `campaign.new_spec("Invalid-Name!", "PRD")`
- Call `campaign.new_spec("123starts_with_number", "PRD")`
- Call `campaign.new_spec("has spaces", "PRD")`

**Expected:**
- CampaignError raised for each invalid name

**Assertion pseudocode:**
```
camp = Campaign.create(path, "Test", "Desc")
ASSERT raises(CampaignError, lambda: camp.new_spec("Invalid-Name!", "PRD"))
ASSERT raises(CampaignError, lambda: camp.new_spec("123numeric", "PRD"))
ASSERT raises(CampaignError, lambda: camp.new_spec("has spaces", "PRD"))
```

### TS-02-E6: new_spec with non-existent PRD path

**Requirement:** 02-REQ-3.E2
**Type:** unit
**Description:** Verify CampaignError when PRD is a Path that does not exist.

**Preconditions:**
- Existing campaign
- Path to a non-existent file

**Input:**
- Call `campaign.new_spec("test", Path("/nonexistent/prd.md"))`

**Expected:**
- CampaignError raised

**Assertion pseudocode:**
```
camp = Campaign.create(path, "Test", "Desc")
ASSERT raises(CampaignError, lambda: camp.new_spec("test", Path("/nonexistent/prd.md")))
```

### TS-02-E7: generate() from non-prd_accepted state

**Requirement:** 02-REQ-4.E1
**Type:** unit
**Description:** Verify SessionError when generate() is called from a state other than prd_accepted.

**Preconditions:**
- Session in `init` state

**Input:**
- Call `session.generate()`

**Expected:**
- SessionError raised

**Assertion pseudocode:**
```
session = create_session_in_state("init")
ASSERT raises(SessionError, session.generate)
session2 = create_session_in_state("assessing")
ASSERT raises(SessionError, session2.generate)
```

### TS-02-E8: assess() from generated state

**Requirement:** 02-REQ-4.E2
**Type:** unit
**Description:** Verify SessionError when assess() is called from the generated terminal state.

**Preconditions:**
- Session in `generated` state

**Input:**
- Call `session.assess()`

**Expected:**
- SessionError raised

**Assertion pseudocode:**
```
session = create_session_in_state("generated")
ASSERT raises(SessionError, session.assess)
```

### TS-02-E9: resume() without _session.json

**Requirement:** 02-REQ-5.E1
**Type:** unit
**Description:** Verify SessionError when resume() is called on a directory without _session.json.

**Preconditions:**
- Directory exists but has no _session.json

**Input:**
- Call `SpecSession.resume(empty_dir)`

**Expected:**
- SessionError raised

**Assertion pseudocode:**
```
empty_dir = tmp / "no_session"
empty_dir.mkdir()
ASSERT raises(SessionError, lambda: SpecSession.resume(empty_dir))
```

### TS-02-E10: resume() with invalid JSON

**Requirement:** 02-REQ-5.E2
**Type:** unit
**Description:** Verify SessionError when _session.json contains invalid JSON.

**Preconditions:**
- Directory with _session.json containing invalid JSON

**Input:**
- Call `SpecSession.resume(dir_with_bad_json)`

**Expected:**
- SessionError raised with parse detail

**Assertion pseudocode:**
```
bad_dir = tmp / "bad_json"
bad_dir.mkdir()
(bad_dir / "_session.json").write_text("{invalid json!!!")
ASSERT raises(SessionError, lambda: SpecSession.resume(bad_dir))
```

### TS-02-E11: validate() and render() with missing artifacts

**Requirement:** 02-REQ-6.E1
**Type:** unit
**Description:** Verify SessionError when validate() or render() is called before all required artifacts exist.

**Preconditions:**
- Spec directory with only prd.md (missing requirements.md, design.md, test_spec.md)

**Input:**
- Call `session.validate()`
- Call `session.render()`

**Expected:**
- SessionError raised indicating which artifacts are missing

**Assertion pseudocode:**
```
session = create_session_with_only_prd()
try:
    session.validate()
except SessionError as e:
    ASSERT "requirements.md" in str(e)
    ASSERT "design.md" in str(e)
    ASSERT "test_spec.md" in str(e)

try:
    session.render()
except SessionError as e:
    ASSERT "requirements.md" in str(e)
```

## Integration Smoke Tests

### TS-02-SMOKE-1: Campaign creation through spec creation

**Execution Path:** Path 1, Path 3 from design.md
**Description:** Full flow: create campaign, create spec, verify directory structure.

**Setup:** Temp directory.

**Trigger:**
1. `Campaign.create(tmp / "smoke", "Smoke Test", "Integration test")`
2. `campaign.new_spec("first_spec", "# PRD\n\nContent")`

**Expected side effects:**
- Campaign directory exists with `campaign.yaml`
- Spec directory `01_first_spec` exists with `prd.md` and `_session.json`
- Campaign metadata matches creation args
- Session is in `init` state

**Must NOT satisfy with:** Mocking Campaign or SpecSession internals.

**Assertion pseudocode:**
```
camp = Campaign.create(tmp / "smoke", "Smoke Test", "Integration test")
session = camp.new_spec("first_spec", "# PRD\n\nContent")
ASSERT (tmp / "smoke" / "campaign.yaml").exists()
ASSERT (tmp / "smoke" / "01_first_spec" / "prd.md").exists()
ASSERT (tmp / "smoke" / "01_first_spec" / "_session.json").exists()
ASSERT camp.metadata.name == "Smoke Test"
ASSERT session.state == SessionState.INIT
```

### TS-02-SMOKE-2: Campaign open and spec listing

**Execution Path:** Path 2 from design.md
**Description:** Full flow: create campaign with specs, close, reopen, list specs.

**Setup:** Temp directory with created campaign and two specs.

**Trigger:**
1. Create campaign and two specs
2. Open campaign from path
3. Call `specs()`

**Expected side effects:**
- Opened campaign has correct metadata
- `specs()` returns both spec directories in order

**Must NOT satisfy with:** Mocking Campaign internals.

**Assertion pseudocode:**
```
camp = Campaign.create(tmp / "smoke2", "Test", "Desc")
camp.new_spec("alpha", "PRD A")
camp.new_spec("beta", "PRD B")
reopened = Campaign.open(tmp / "smoke2")
ASSERT reopened.metadata.name == "Test"
specs = reopened.specs()
ASSERT len(specs) == 2
ASSERT specs[0].name == "01_alpha"
ASSERT specs[1].name == "02_beta"
```

### TS-02-SMOKE-3: Session state machine lifecycle

**Execution Path:** Path 4 from design.md
**Description:** Full lifecycle through accept_prd (non-stub path) verifying state transitions and persistence.

**Setup:** Campaign with a spec.

**Trigger:**
1. Create session via `new_spec()`
2. Manually set session to `assessing` state (simulating post-assess)
3. Call `accept_prd()`
4. Verify state is `prd_accepted`
5. Resume session from disk
6. Verify resumed state matches

**Expected side effects:**
- State transitions persist correctly
- Resumed session matches pre-resume state

**Must NOT satisfy with:** Mocking SpecSession or its persistence layer.

**Assertion pseudocode:**
```
camp = Campaign.create(tmp / "smoke3", "Test", "Desc")
session = camp.new_spec("lifecycle", "PRD content")
# Simulate assess having run (set state directly for test)
session._set_state(SessionState.ASSESSING)
session.accept_prd()
ASSERT session.state == SessionState.PRD_ACCEPTED

resumed = SpecSession.resume(session.spec_dir)
ASSERT resumed.state == SessionState.PRD_ACCEPTED
```

### TS-02-SMOKE-4: Session resume end-to-end

**Execution Path:** Path 5 from design.md
**Description:** Create session, transition states, resume, verify full restoration.

**Setup:** Campaign with a spec that has undergone transitions.

**Trigger:**
1. Create campaign and spec
2. Transition to `prd_accepted`
3. Resume session from `_session.json`

**Expected side effects:**
- Resumed session state matches
- Spec directory path matches
- Assessment property is accessible

**Must NOT satisfy with:** Mocking SpecSession persistence.

**Assertion pseudocode:**
```
camp = Campaign.create(tmp / "smoke4", "Test", "Desc")
session = camp.new_spec("resume_test", "PRD")
session._set_state(SessionState.ASSESSING)
session.accept_prd()
ASSERT session.state == SessionState.PRD_ACCEPTED
original_dir = session.spec_dir

resumed = SpecSession.resume(original_dir)
ASSERT resumed.state == SessionState.PRD_ACCEPTED
ASSERT resumed.spec_dir == original_dir
```

### TS-02-SMOKE-5: Validation and rendering end-to-end

**Execution Path:** Path 6 from design.md
**Description:** Create a spec directory with all artifacts, validate and render.

**Setup:** Spec directory populated with all four required artifacts.

**Trigger:**
1. Call `session.validate()`
2. Call `session.render(combined=True)`
3. Call `session.render(combined=False)`

**Expected side effects:**
- validate() returns a ValidationResult
- render(combined=True) returns a string
- render(combined=False) returns a dict

**Must NOT satisfy with:** Mocking the validate/render methods themselves (afspec internals may be mocked).

**Assertion pseudocode:**
```
session = create_session_with_all_artifacts()
result = session.validate()
ASSERT isinstance(result, ValidationResult)

combined = session.render(combined=True)
ASSERT isinstance(combined, str)

individual = session.render(combined=False)
ASSERT isinstance(individual, dict)
```

## Coverage Matrix

| Requirement | Test Spec Entry | Type |
|-------------|-----------------|------|
| 02-REQ-1.1 | TS-02-1 | unit |
| 02-REQ-1.2 | TS-02-2 | unit |
| 02-REQ-1.3 | TS-02-3 | unit |
| 02-REQ-2.1 | TS-02-4 | unit |
| 02-REQ-2.2 | TS-02-5 | unit |
| 02-REQ-3.1 | TS-02-6 | unit |
| 02-REQ-3.2 | TS-02-7 | unit |
| 02-REQ-3.3 | TS-02-8 | unit |
| 02-REQ-3.4 | TS-02-9 | unit |
| 02-REQ-4.1 | TS-02-10 | unit |
| 02-REQ-4.2 | TS-02-11 | unit |
| 02-REQ-4.3 | TS-02-12 | unit |
| 02-REQ-4.4 | TS-02-13 | unit |
| 02-REQ-5.1 | TS-02-14 | unit |
| 02-REQ-5.2 | TS-02-15 | unit |
| 02-REQ-5.3 | TS-02-16 | unit |
| 02-REQ-6.1 | TS-02-17 | unit |
| 02-REQ-6.2 | TS-02-18 | unit |
| 02-REQ-6.3 | TS-02-19 | unit |
| 02-REQ-1.E1 | TS-02-E1 | unit |
| 02-REQ-1.E2 | TS-02-E2 | unit |
| 02-REQ-2.E1 | TS-02-E3 | unit |
| 02-REQ-2.E2 | TS-02-E4 | unit |
| 02-REQ-3.E1 | TS-02-E5 | unit |
| 02-REQ-3.E2 | TS-02-E6 | unit |
| 02-REQ-4.E1 | TS-02-E7 | unit |
| 02-REQ-4.E2 | TS-02-E8 | unit |
| 02-REQ-5.E1 | TS-02-E9 | unit |
| 02-REQ-5.E2 | TS-02-E10 | unit |
| 02-REQ-6.E1 | TS-02-E11 | unit |
| Property 1 | TS-02-P1 | property |
| Property 2 | TS-02-P2 | property |
| Property 3 | TS-02-P3 | property |
| Property 4 | TS-02-P4 | property |
| Property 5 | TS-02-P5 | property |
| Property 6 | TS-02-P6 | property |
| Path 1+3 | TS-02-SMOKE-1 | integration |
| Path 2 | TS-02-SMOKE-2 | integration |
| Path 4 | TS-02-SMOKE-3 | integration |
| Path 5 | TS-02-SMOKE-4 | integration |
| Path 6 | TS-02-SMOKE-5 | integration |
