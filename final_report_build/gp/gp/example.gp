set terminal postscript eps color "Helvetica" 24

set title "EXAMPLE - Adaptively Routed RDMA vs RVMA Latency"
set output "rvma_lat.eps"

set key top left
set key Left reverse
set key spacing 1 font ",22" 
set logscale y 2
set logscale x 2 
set xtics rotate by 45 right
set xlabel "Message Size (B)"
set xtics font ",20"
set xtics (4,16,64,256,1024,4096,16384,"64 KiB" 65536,"256 KiB" 262144, "1MiB" 1048576)

set ylabel "Latency (us)"
#if (TIME == 10) set yrange[0:10000]
#if (TIME == 50) set yrange[0:12000]
#if (TIME == 100) set yrange[0:20000]

set style line 1 lc "#006400" lw 5 pt 9 ps 2 dashtype 1
set style line 2 lc 3 lw 5 pt 7 ps 2 dashtype 2
set style line 3 lc "#006400" lw 3 pt 9 ps 2 dashtype 1
set style line 4 lc 3 lw 3 pt 7 ps 2 dashtype 1



#getTitle(n,type) = sprintf(" %d threads %s",n,type)
#getData(nthreads,input) = sprintf("<(./bw-vs-buf.py -numThreads=%d -file=%s)", nthreads,input )

#list = THREAD 

plot "./../data/rdma_gnu.dat" using 1:2:3:4 notitle ls 3 with errorbars, \
     '' using 1:2 title "RDMA" w linespoints ls 1, \
     "./../data/rvma_gnu.dat" using 1:2:3:4 notitle ls 4 with errorbars, \
     '' using 1:2 title "RVMA" w linespoints ls 2

