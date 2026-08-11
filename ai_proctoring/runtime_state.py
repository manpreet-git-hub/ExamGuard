_FALLBACK_STATE = {}


def _streamlit_state():
    try:
        import streamlit as st

        return st.session_state
    except Exception:
        return None


def get_state(key, default=None):
    state = _streamlit_state()
    if state is not None:
        if key not in state:
            state[key] = default
        return state[key]

    return _FALLBACK_STATE.get(key, default)


def set_state(key, value):
    state = _streamlit_state()
    if state is not None:
        state[key] = value
    else:
        _FALLBACK_STATE[key] = value

    return value
