import json
from pathlib import Path
from typing import Any, Dict, List

import streamlit as st

DEFAULT_RUBRIC_PATH = Path(__file__).resolve().parent / "rubrics" / "psychiatry_intake.json"


def _safe_json_loads(text: str):
    try:
        return json.loads(text), None
    except Exception as e:
        return None, str(e)


def _split_lines_to_list(s: str) -> List[str]:
    if s is None:
        return []
    lines = []
    for line in str(s).splitlines():
        line = line.strip()
        if line:
            lines.append(line)
    return lines


def _items_to_editor_rows(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows = []
    for it in items or []:
        rows.append(
            {
                "id": it.get("id", ""),
                "desc": it.get("desc", ""),
                "weight": it.get("weight", 0),
                "gate": it.get("gate", ""),
                "safety_critical": bool(it.get("safety_critical", False)),
                "patterns_en": "\n".join(it.get("patterns_en", []) or []),
                "patterns_ar": "\n".join(it.get("patterns_ar", []) or []),
            }
        )
    return rows


def _editor_rows_to_items(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    items = []
    for r in rows or []:
        if not (r.get("id") or "").strip():
            # skip empty rows
            continue
        items.append(
            {
                "id": (r.get("id") or "").strip(),
                "desc": r.get("desc", "") or "",
                "weight": float(r.get("weight", 0) or 0),
                **({"gate": r.get("gate")} if (r.get("gate") or "").strip() else {}),
                **({"safety_critical": True} if bool(r.get("safety_critical", False)) else {}),
                "patterns_en": _split_lines_to_list(r.get("patterns_en", "")),
                "patterns_ar": _split_lines_to_list(r.get("patterns_ar", "")),
            }
        )
    return items


def _load_rubric_from_path(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _dump_rubric(rubric: Dict[str, Any]) -> str:
    return json.dumps(rubric, ensure_ascii=False, indent=2)


st.set_page_config(page_title="Rubric Editor", layout="wide")
st.title("Rubric Editor (Examiner)")

# -----------------------------
# Sidebar: load/save controls
# -----------------------------
st.sidebar.header("Rubric source")

if "rubric_path" not in st.session_state:
    st.session_state.rubric_path = str(DEFAULT_RUBRIC_PATH)

rubric_path_str = st.sidebar.text_input("Rubric file path (server)", value=st.session_state.rubric_path)
st.session_state.rubric_path = rubric_path_str

uploaded = st.sidebar.file_uploader("...or upload a rubric JSON", type=["json"])

colA, colB = st.sidebar.columns(2)
load_clicked = colA.button("Load")
save_clicked = colB.button("Save to path")

# Load rubric
if "rubric" not in st.session_state:
    st.session_state.rubric = None

if load_clicked:
    if uploaded is not None:
        # Uploaded rubric lives in memory; store it in session_state
        data = uploaded.getvalue().decode("utf-8")
        rubric, err = _safe_json_loads(data)
        if err:
            st.sidebar.error(f"Upload JSON parse error: {err}")
        else:
            st.session_state.rubric = rubric
            st.sidebar.success("Loaded rubric from upload.")
    else:
        path = Path(rubric_path_str)
        if not path.exists():
            st.sidebar.error("File not found on server path.")
        else:
            try:
                st.session_state.rubric = _load_rubric_from_path(path)
                st.sidebar.success("Loaded rubric from path.")
            except Exception as e:
                st.sidebar.error(f"Failed to load rubric: {e}")

# If nothing loaded yet, try auto-load default path
if st.session_state.rubric is None:
    try:
        if Path(rubric_path_str).exists():
            st.session_state.rubric = _load_rubric_from_path(Path(rubric_path_str))
        elif DEFAULT_RUBRIC_PATH.exists():
            st.session_state.rubric = _load_rubric_from_path(DEFAULT_RUBRIC_PATH)
            st.session_state.rubric_path = str(DEFAULT_RUBRIC_PATH)
    except Exception:
        pass

rubric = st.session_state.rubric
if rubric is None:
    st.warning("No rubric loaded yet. Use the sidebar to load a rubric JSON.")
    st.stop()

# Save rubric back to server path
if save_clicked:
    path = Path(rubric_path_str)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(_dump_rubric(rubric), encoding="utf-8")
        st.sidebar.success(f"Saved to: {path}")
    except Exception as e:
        st.sidebar.error(f"Save failed: {e}")

# Always offer download
st.sidebar.download_button(
    "Download rubric JSON",
    data=_dump_rubric(rubric),
    file_name=f"{rubric.get('rubric_id','rubric')}.json",
    mime="application/json",
)

# -----------------------------
# Main UI: edit rubric fields
# -----------------------------
meta_col1, meta_col2, meta_col3 = st.columns([2, 1, 1])
with meta_col1:
    rubric["rubric_id"] = st.text_input("Rubric ID", value=rubric.get("rubric_id", ""))
    rubric["version"] = st.text_input("Version", value=rubric.get("version", ""))
with meta_col2:
    rubric["languages"] = st.multiselect(
        "Languages",
        options=["English", "Arabic"],
        default=rubric.get("languages", ["English", "Arabic"]),
    )
with meta_col3:
    pass_cfg = rubric.get("pass_criteria", {})
    min_percent = st.number_input("Pass: min percent", min_value=0.0, max_value=1.0, value=float(pass_cfg.get("min_percent", 0.7)), step=0.05)
    fail_flags = st.text_input("Fail-on flags (comma-separated)", value=",".join(pass_cfg.get("fail_on_flags", ["SAFETY_CRITICAL"])))
    rubric["pass_criteria"] = {"min_percent": float(min_percent), "fail_on_flags": [x.strip() for x in fail_flags.split(",") if x.strip()]}

st.divider()

# Patient cue patterns
st.subheader("Patient cues")
cue = rubric.get("patient_cues", {}).get("risk_positive", {})
c1, c2 = st.columns(2)
with c1:
    cue_en = st.text_area("Risk-positive cues (English) — one regex per line", value="\n".join(cue.get("patterns_en", []) or []), height=140)
with c2:
    cue_ar = st.text_area("Risk-positive cues (Arabic) — one regex per line", value="\n".join(cue.get("patterns_ar", []) or []), height=140)

rubric.setdefault("patient_cues", {})
rubric["patient_cues"]["risk_positive"] = {
    "patterns_en": _split_lines_to_list(cue_en),
    "patterns_ar": _split_lines_to_list(cue_ar),
}

st.divider()

# Items editor
st.subheader("Checklist items")
st.caption("Edit items below. Patterns are newline-separated (one regex per line).")

editor_rows = _items_to_editor_rows(rubric.get("items", []))

edited_rows = st.data_editor(
    editor_rows,
    num_rows="dynamic",
    use_container_width=True,
    key="items_editor",
    column_config={
        "weight": st.column_config.NumberColumn("weight", min_value=0.0, step=1.0),
        "safety_critical": st.column_config.CheckboxColumn("safety_critical"),
        "patterns_en": st.column_config.TextColumn("patterns_en", help="One regex per line"),
        "patterns_ar": st.column_config.TextColumn("patterns_ar", help="One regex per line"),
    },
)

col_apply, col_raw = st.columns([1, 2])
with col_apply:
    if st.button("Apply edits to rubric"):
        rubric["items"] = _editor_rows_to_items(edited_rows)
        st.session_state.rubric = rubric
        st.success("Applied edits (not saved to disk unless you click 'Save to path').")

with col_raw:
    with st.expander("Advanced: edit raw JSON", expanded=False):
        raw = st.text_area("Raw rubric JSON", value=_dump_rubric(rubric), height=320)
        if st.button("Apply raw JSON"):
            new_rubric, err = _safe_json_loads(raw)
            if err:
                st.error(f"Raw JSON parse error: {err}")
            else:
                st.session_state.rubric = new_rubric
                st.success("Replaced rubric with raw JSON.")