.PHONY.:	all clean realclean
LATEXMK      = latexmk
#LATEXMKFLAGS = -f -pdf -g -pdf="pdflatex --shell-escape %O %S"
LATEXMKFLAGS = -f -pdf -g 
LATEXMKCLEAN = -C
export TEXINPUTS:=./includes:${TEXINPUTS}
export BSTINPUTS:=./includes:${BSTINPUTS}

SOURCES      = paper.tex
EXECS        = $(SOURCES:.tex=.pdf)
BASE         = $(SOURCES:.tex=)

TEXSRC       = $(filter-out $(SOURCES), $(shell ls *.tex))

BIBSRC       = $(shell ls *.bib)
BBL          = $(notdir $(BIBSRC:.bib=.bbl))

DEPS         = $(DEP) $(TEXSRC) $(BIBSRC) plots


all: $(EXECS)

$(EXECS): %.pdf : %.tex $(DEPS) 
	$(LATEXMK) $(LATEXMKFLAGS) $<
	$(LATEXMK) $(LATEXMKFLAGS) $<

$(BBL): $(BIBSRC)
	bibtex $(BASE)

plots:
	${MAKE} -C gp

view:	all
	$(LATEXMK) -pvc -view=ps -r latexmkrc paper

clean:
	${MAKE} -C gp clean
	$(LATEXMK) $(LATEXMKCLEAN)
	@rm -f *~

realclean: clean
	${MAKE} -C plots realclean
	@rm -f *.bbl *.bak *.log *.dvi *.ps
