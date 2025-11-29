# utils/label_template.py

def escape_html(s: str) -> str:
    """Basic HTML escaping."""
    return (
        str(s)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )

CSS = """
<style>
    @page { size: A4; margin: 12mm; }
    body {
        font-family: Arial, sans-serif;
        background: #fff;
        color: #000;
        display: flex;
        flex-wrap: wrap;
        justify-content: space-between;
    }
    .label {
        box-sizing: border-box;
        width: 48%;
        height: 170px;
        border: 1px solid #ccc;
        border-radius: 6px;
        margin-bottom: 10px;
        padding: 8px 10px;
        display: flex;
        align-items: center;
    }
    .qr {
        flex: 0 0 35%;
        display: flex;
        justify-content: center;
        align-items: center;
    }
    .qr img {
        width: 110px;
        height: 110px;
    }
    .details {
        flex: 1;
        padding-left: 10px;
        font-size: 10pt;
    }
    .details p {
        margin: 0;
        font-size: 9pt;
        line-height: 1.25;
    }
    .details .field-name {
        font-weight: bold;
        color: #000;
    }
</style>
"""


def render_label_html(qr_path: str, product: dict, column_order: list[str]) -> str:
    """Generate the HTML for a single label dynamically."""
    from .label_template import escape_html

    # Generate dynamic field list
    fields_html = []
    for col in column_order:
        if col in ("qr_status", "qr_hash", "_row"):
            continue

        value = escape_html(product.get(col, ""))
        name = col.replace("_", " ").title()
        fields_html.append(f"<p><span class='field-name'>{name}:</span> {value}</p>")

    fields_joined = "\n".join(fields_html)

    return f"""
    <div class="label">
        <div class="qr">
            <img src="{qr_path}" alt="QR">
        </div>
        <div class="details">
            {fields_joined}
        </div>
    </div>
    """
