IGNORE = header.gp
GPLOTS = $(shell ls *.gp)
PLOTS  = $(filter-out $(IGNORE),$(GPLOTS))
EPS_GRAPHS = ${PLOTS:.gp=.eps}
PDF_GRAPHS = ${PLOTS:.gp=.pdf}

all: $(PDF_GRAPHS)
 
.PHONY: all clean
 
# we want all .gnuplot files to be 'made' into .eps files
# the % replaces any name
# in the rule:  $< replaces the source
#               $@ replaces the target
# example: convert $< $@
#
%.eps: %.gp
	gnuplot < $<
     
%.eps: %.py
	python $<
 
%.pdf: %.eps
	epstopdf $<
	mv $@ ./../plots/
 
clean:
	rm -f $(EPS_GRAPHS) $(PDF_GRAPHS)
