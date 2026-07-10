"""
app/ui/theme.py — UI Color neon dark palette and typography font constants.
"""

BG          = "#0d0f18"
BG2         = "#111624"
BG3         = "#1a2035"
SIDEBAR_BG  = "#0b0d14"
ACCENT      = "#00e5ff"
ACCENT2     = "#4f8eff"
SUCCESS     = "#00e676"
WARN        = "#ffab40"
ERR         = "#ff4d6d"
TXT         = "#e2e8f0"
TXT_DIM     = "#64748b"
BORDER      = "#1e2d45"

FONT_MAIN   = ("Segoe UI",  11)
FONT_MONO   = ("Consolas",  10)
FONT_TITLE  = ("Segoe UI",  20, "bold")
FONT_LABEL  = ("Segoe UI",   9, "bold")
FONT_BTN    = ("Segoe UI",  11, "bold")


def rounded_rect(canvas, x1, y1, x2, y2, r=12, **kw):
    """Draws a smooth rounded rectangle on a Tkinter canvas."""
    pts = [
        x1+r, y1,   x2-r, y1,
        x2,   y1,   x2,   y1+r,
        x2,   y2-r, x2,   y2,
        x2-r, y2,   x1+r, y2,
        x1,   y2,   x1,   y2-r,
        x1,   y1+r, x1,   y1,
        x1+r, y1,
    ]
    return canvas.create_polygon(pts, smooth=True, **kw)
