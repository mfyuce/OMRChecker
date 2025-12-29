from pdf2image import convert_from_path

# pdf_paths = ["/home/fatihyuce/work/academic/2025/bu/MIS 233 - Web Based Application Development/midterms/1/examp_papers/mis233-midterm-1.pdf",
#             "/home/fatihyuce/work/academic/2025/bu/MIS 233 - Web Based Application Development/midterms/1/examp_papers/mis233-midterm-2.pdf"
#
#             ]
# pdf_paths = ["/home/fatihyuce/work/academic/2025/bu/MIS 233 - Web Based Application Development/midterms/1/examp_papers/mis233-midterm-aligned-cropbox.pdf"
pdf_paths = ["/home/fatihyuce/work/academic/2025/bu/MIS 233 - Web Based Application Development/midterms/makeup/papers/omr_midterm_50q_v1.pdf"

            ]
index_pdf = 0
for pdf_path in pdf_paths:
    pages = convert_from_path(pdf_path, dpi=300)

    for i, page in enumerate(pages, start=1):
        page.save(f"/home/fatihyuce/work/projects/tmp/optical_form/apps/OMRChecker/back/makeup/paper_{index_pdf}.png", "PNG")
        index_pdf=index_pdf+1
