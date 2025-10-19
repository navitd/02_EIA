


B00 verbal explanation (current file)

B01 no such file

B02 no such file

B03 Arima_gdp - all countries go through Arima, but Japan goes to the negative

B03 ARIMA gdp JPN adj - japan adjusted by a linear graph

B04 multivariate E extrap: extrapolating E based on the ration with gdp. assuming Etot/gdptot stays conatant

B05 Esectors from Etot

#divergence from A version
#B06 collect data 1995-2020: f, fother, Tc, output, GDPj_by_xj and everything else I may need later
#save to one file
#the problem: need separate functions for Tc and vectors
#another problem: need different name so that not confused with data colelction for graphs
#harmonise: years are numbers not strings
#decided series or dataframes ( prefer dataframes ) for all vectors

#collect also tot for everything. tot meaning summation over sectors to get vtot
#no need to do this with T

run 1995-2020 after checks


B07 calculation of bases for Tc (easy), and all other vectors
bases are the fixed ratio vsector/vtot

no B8, B9


B10 extracting actual extrapolated data from all the above

B11 comparing for 2020 - extrapolated and real data. should be the same if all bases rely on 2020 alone.all

B12 plot benchmarking graphs