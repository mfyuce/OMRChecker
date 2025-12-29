# Create an A4 OMR (optical mark recognition) midterm form PDF with 50 questions (A–D choices)
# The layout includes: title, student name/id fields, and two columns of 25 questions with 4 bubbles each.
# We'll also add corner registration squares and edge tick marks to help with optical alignment when scanning.

import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle
from matplotlib.backends.backend_pdf import PdfPages

# Page settings
inch = 1.0
a4_w_in, a4_h_in = 8.27, 11.69  # A4 in inches
margin = 0.5 * inch

# Bubble settings
bubble_radius = 0.10 * inch
bubble_gap_x = 0.20 * inch  # gap between bubble centers horizontally
bubble_gap_y = 0.28 * inch  # row height

# Layout: two columns
questions_total = 50
per_col = 25
num_cols = 2
choices = ['A', 'B', 'C', 'D']

# Compute column boxes
col_width = (a4_w_in - 2*margin) / num_cols

def draw_header(ax):
    # Title
    ax.text(a4_w_in/2, a4_h_in - margin*0.55, "MIS 233 - Web Based Application Development - 2025", ha='center', va='center', fontsize=18, fontweight='bold')
    # Fields
    y = a4_h_in - margin*1.2
    line_len = 3.8 * inch
    ax.text(margin, y, "Student Name:", ha='left', va='center', fontsize=12)
    ax.plot([margin+1.4*inch, margin+1.2*inch+line_len], [y, y], color='black', linewidth=0.8)
    y2 = y - 0.35*inch
    ax.text(margin, y2, "Student ID      :", ha='left', va='center', fontsize=12)
    ax.plot([margin+1.4*inch, margin+1.2*inch+line_len], [y2, y2], color='black', linewidth=0.8)
    # Exam name
    y3 = y2 - 0.35*inch
    ax.text(margin, y3, "Exam Name    :", ha='left', va='center', fontsize=12)
    ax.text(margin+1.4*inch, y3, "Midterm", ha='left', va='center', fontsize=12, fontstyle='italic')
    # Instructions
    y4 = y3 - 0.35*inch
    ax.text(margin, y4, "Fill bubbles completely. Use a dark pen or pencil. Do not fold. Print at 100% scale.",
            ha='left', va='center', fontsize=9)
    global header_bottom_y
    header_bottom_y = y4 - 0.5 * inch  # or 0.6 inch for more space

def draw_registration_marks(ax):
    # Corner squares
    sq = 0.25 * inch
    # bottom-left
    ax.add_patch(Rectangle((margin - 0.15*inch, margin - 0.15*inch), sq, sq, fill=True))
    # bottom-right
    ax.add_patch(Rectangle((a4_w_in - margin - sq + 0.15*inch, margin - 0.15*inch), sq, sq, fill=True))
    # top-left
    ax.add_patch(Rectangle((margin - 0.15*inch, a4_h_in - margin - sq + 0.15*inch), sq, sq, fill=True))
    # top-right
    ax.add_patch(Rectangle((a4_w_in - margin - sq + 0.15*inch, a4_h_in - margin - sq + 0.15*inch), sq, sq, fill=True))
    # Edge tick marks
    for i in range(10):
        x0 = margin - 0.10*inch
        y = margin + i*( (a4_h_in - 2*margin) / 9.0 )
        ax.plot([x0, x0 - 0.10*inch], [y, y], color='black', linewidth=1.0)
        x1 = a4_w_in - margin + 0.10*inch
        ax.plot([x1, x1 + 0.10*inch], [y, y], color='black', linewidth=1.0)

def draw_bubble(ax, cx, cy, label=None):
    circ = Circle((cx, cy), bubble_radius, fill=False, linewidth=0.9)
    ax.add_patch(circ)
    if label:
        ax.text(cx, cy, label, ha='center', va='center', fontsize=8)

def draw_column(ax, col_index, start_qnum):
    # Column origin
    col_x = margin + col_index * col_width
    # Starting y below header
    start_y = header_bottom_y
    # Column title
    ax.text(col_x, start_y, f"Questions {start_qnum}–{start_qnum+per_col-1}",
            ha='left', va='center', fontsize=12, fontweight='bold')
    start_y = start_y - margin*2.0
    # Horizontal positions: number + 4 bubbles
    num_x = col_x + 0.00*inch
    first_bubble_x = col_x + 0.75*inch
    # For each question row
    for i in range(per_col):
        q_num = start_qnum + i
        row_y = start_y - i * bubble_gap_y
        # Question number
        ax.text(num_x, row_y, f"{q_num:>2}", ha='left', va='center', fontsize=10)
        # Bubbles A-D
        for j, ch in enumerate(choices):
            cx = first_bubble_x + j * (2*bubble_radius + bubble_gap_x)
            # Draw circle and print letter above
            draw_bubble(ax, cx, row_y, None)
            ax.text(cx, row_y - 0.07*inch, ch, ha='center', va='bottom', fontsize=9)

# Create PDF
pdf_path = "./omr_midterm_50q.pdf"
svg_path = "./omr_midterm_50q.svg"

with PdfPages(pdf_path) as pdf:
    fig = plt.figure(figsize=(a4_w_in, a4_h_in))
    ax = fig.add_axes([0,0,1,1])
    ax.set_xlim(0, a4_w_in)
    ax.set_ylim(0, a4_h_in)
    ax.axis('off')

    draw_header(ax)
    draw_registration_marks(ax)

    # Columns
    draw_column(ax, 0, 1)
    draw_column(ax, 1, per_col+1)

    pdf.savefig(fig, bbox_inches='tight')
    plt.close(fig)

# Also save an SVG version (use the same drawing once more)
fig = plt.figure(figsize=(a4_w_in, a4_h_in))
ax = fig.add_axes([0,0,1,1])
ax.set_xlim(0, a4_w_in)
ax.set_ylim(0, a4_h_in)
ax.axis('off')
draw_header(ax)
draw_registration_marks(ax)
draw_column(ax, 0, 1)
draw_column(ax, 1, per_col+1)
fig.savefig(svg_path, bbox_inches='tight', format='svg')
plt.close(fig)

pdf_path, svg_path
