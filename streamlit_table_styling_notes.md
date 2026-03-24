# Streamlit Table Styling: Centering and Hiding the Index

This document serves as a reference for how we achieved perfectly centered tables (both headers and data) while completely removing the unwanted numerical index in the ESPN Fantasy Dashboard. 

This was necessary due to specific behaviors in newer versions of Streamlit (e.g., 1.55.0) and Pandas `Styler` objects.

## The Challenges

1. **`st.dataframe` ignores CSS alignment:** Streamlit's `st.dataframe` component renders an interactive canvas (Glide Data Grid). Because it draws to a canvas rather than generating HTML elements, it completely ignores HTML/CSS text alignment properties, even when explicitly passed a Pandas `Styler` object with `text-align: center`.
2. **`st.table` ignores `.hide_index()`:** While `st.table` renders standard HTML (which *does* respect CSS), newer versions of Streamlit explicitly ignore the `.hide_index()` or `.hide(axis="index")` methods from Pandas `Styler`. This causes the numerical index to persistently appear.

## The Solution ("Option C")

To get exactly what we wanted, we combined three specific workarounds into a single `prepare_df_for_display` function in `streamlit_app.py`.

### 1. Switch to `st.table`
First, we replaced all `st.dataframe` calls with `st.table` so the tables would render as standard HTML elements capable of receiving CSS styling.

### 2. Hijack the First Column (The "Option C" Hack)
Since `.hide_index()` doesn't work, we forcefully hide the numerical index by dynamically setting the first data column (e.g., "Year" or "Team") to *be* the index. This removes the numerical index without leaving a blank column behind.

### 3. Fix the Duplicate Index `KeyError`
When you set a column like "Year" as the index, you inevitably create duplicate index values. Pandas `Styler` crashes when applying styles to a dataframe with a non-unique index (`KeyError: 'Styler.apply' and '.map' are not compatible with non-unique index'`). 

**The Fix:** We programmatically append invisible zero-width space characters (`\u200b`) to duplicate values. This makes every single index value completely unique under the hood, preventing the crash, while remaining visually identical to the user.

```python
first_col = df_copy.columns[0]
s = df_copy[first_col].astype(str)
# Append zero-width spaces to duplicates
df_copy[first_col] = s + s.groupby(s).cumcount().map(lambda x: '\u200b' * x)
df_copy = df_copy.set_index(first_col)
```

### 4. Force Global CSS Alignment
Because our new "first column" is technically the index, Streamlit renders it using row header tags (`<th>`) instead of standard data cell tags (`<td>`). 

Pandas `Styler` properties (like `text-align: center`) generally only apply to standard data cells (`<td>`), which caused our first column to remain stubbornly left-aligned. 

**The Fix:** We injected a global CSS rule at the top of the app that targets Streamlit's specific table class (`[data-testid="stTable"]`), forcing the browser to center every single `<th>` and `<td>` element inside it.

```html
<style>
    /* Force centering for all st.table elements (including row headers) */
    [data-testid="stTable"] th, [data-testid="stTable"] td {
        text-align: center !important;
    }
</style>
```

---
*Note: If Streamlit ever updates `st.dataframe` to natively support text alignment, or fixes `st.table` to respect `.hide_index()`, this workaround can be safely removed.*