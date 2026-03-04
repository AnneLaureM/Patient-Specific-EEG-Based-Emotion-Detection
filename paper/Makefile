# Makefile for compiling LaTeX paper

.PHONY: all clean view

TEX = pdflatex
BIB = bibtex
MAIN = main
OUTPUT_DIR = build

all: $(OUTPUT_DIR)
	$(TEX) -output-directory=$(OUTPUT_DIR) $(MAIN).tex
	-$(BIB) $(OUTPUT_DIR)/$(MAIN)
	$(TEX) -output-directory=$(OUTPUT_DIR) $(MAIN).tex
	$(TEX) -output-directory=$(OUTPUT_DIR) $(MAIN).tex
	cp $(OUTPUT_DIR)/$(MAIN).pdf .

$(OUTPUT_DIR):
	mkdir -p $(OUTPUT_DIR)

view: all
	@if [ -f $(MAIN).pdf ]; then \
		if command -v evince > /dev/null; then \
			evince $(MAIN).pdf & \
		elif command -v xdg-open > /dev/null; then \
			xdg-open $(MAIN).pdf & \
		else \
			echo "PDF generated: $(MAIN).pdf"; \
		fi \
	else \
		echo "PDF not generated"; \
	fi

clean:
	rm -rf $(OUTPUT_DIR)
	rm -f $(MAIN).pdf
	rm -f *.aux *.log *.bbl *.blg *.toc *.out *.lof *.lot

quick:
	$(TEX) -output-directory=$(OUTPUT_DIR) $(MAIN).tex
	cp $(OUTPUT_DIR)/$(MAIN).pdf .