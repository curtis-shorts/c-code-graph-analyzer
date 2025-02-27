#
# Common parameters for all of our plots.
#
set terminal postscript eps enhanced color colortext \
	dashed dashlength 4.0 linewidth 0.7 butt \
	"Helvetica" 40
# set size 2.5,1.5
# set size 2.5,2.0
set size 2.0, 2.0
set rmargin 6	# Make room for the xtick label
set grid front
#set grid y

# The 3 at the end says draw the border on the left and bottom only
set border lc rgbcolor "grey10" 3

# Don't put ticks on the border we just erased
set ytics nomirror
set xtics nomirror rotate by -45 scale 0

set xtics("8B" 8, "16B" 16, "32B" 32, "64B" 64, "128B" 128, "256B" 256, "512B" 512, "1KiB" 1024, "2KiB" 2048, "4KiB" 4096, "8KiB" 8192, "16KiB" 16384, "32KiB" 32696, "64KiB" 65392, "128KiB" 131072, "256KiB" 262144,  "512KiB" 524288, "1MiB" 1048570)

set tics out textcolor rgbcolor "#000000"

set grid noxtics ls 100

set grid lc rgbcolor "#606060"
set title textcolor rgbcolor "#000000"
set ylabel textcolor rgbcolor "#000000"
set xlabel textcolor rgbcolor "#000000"

# pt 7 is a filled circle
# pt 9 is a filled triangle
# pt 13 is a filled diamond
# pt 11 is a filled upside-down triangle
# pt 15 is a filled pentagon
set style line 1 lc rgbcolor "#b22222" ps 4 pt 15 lw 10 lt 1
set style line 2 lc rgbcolor "#a5c232" ps 4 pt 7 lw 10 lt 1
set style line 3 lc rgbcolor "#754d1e" ps 4 pt 9 lw 10 lt 1
set style line 4 lc rgbcolor "#c27f32" ps 4 pt 11 lw 10 lt 1
set style line 5 lc rgbcolor "#8a8a8a" ps 4 pt 12 lw 10 lt 1
set style line 6 lc rgbcolor "#4b0082" ps 4 pt 8 lw 10 lt 1
set style line 7 lc rgbcolor "#000000" ps 4 pt 4 lw 10 lt 1
set style line 8 lc rgbcolor "#64751e" ps 4 pt 1 lw 10 lt 1
set style line 12 lc rgbcolor "#a5c232" lw 10 lt 3
set style line 13 lc rgbcolor "#754d1e" lw 10 lt 3
set style line 14 lc rgbcolor "#c27f32" lw 10 lt 3
set style line 15 lc rgbcolor "#8a8a8a" lw 10 lt 3
set style line 19 lc rgbcolor "#b0b0b0" lw 10 lt 3

set datafile missing "-"
