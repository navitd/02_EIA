
# 1. ARIMA_gdp04.py ->ARIMA_gdp_JPN_adj04.py
# 1.1 upload worldbank GDP data + ARIMA forecast 16 years ahead
# 1.2 print to excel GDP+forecast GDP. print in excel the name of the program that makes it.

# 2.multivariate_E_extrap03.py 
# 2.1. predict compensation of employees E vector from GDP
# 2.2 print to excel E+forecast E. print in excel the name of the program that makes it.

# 3. Esectors_from_Etot05.py
# 3.1 predict _sectors_ E
# 3.2 print to excel E+forecast E. print in excel the name of the program that makes it.
# apan gdp goes to the negative after 2037. I should correct the gdp extrapolation and run all the files again
# corrected gdp extrapolation of japan alone. made a linear function with a and b parameters
#    ran all files again, print to excel
# ARIMA_gdp_JPN_adj04.py corrects for japan

# 4. dfother_extrap06.py
# 4.1 upload final demand F from OECD and use ratio with gdp to forecast forward
# I don't need forecasted input-output tables, just final demand (other vectors)
# 4.2 print to excel F+forecast F. print in excel the name of the program that makes it.

# now I have all E and all F
# go back to the graphs I need to make, and see where these get into play

# 5. Lcextrap07.py
# upload gpd
# Eextrap+data
# fextrap+data
#for country
#for year
#OECD
#combine with above
#calculate L 
# comparison of gdp world bank and gdp OECD : 4-11% difference in yearly total GDP
# OECD is always larger 
#compare f to waht I have, compare gdp to waht I  have
#gdp has 4-11% difference between world bank and OECD
# f has no difference.

then make it into a function, to be used in graphs
create Lc for future years!!!
E
fc
Lc = Lc_extrap
L
T
output
GDP
II

# I can not have the same treatment. with future years I start from T or L
# 2 different uploading systems, for data and for extrap, once I get to L everything is the same?

# The files of future years should match the files of OECD for smooth transition?


# CGARextrap10.py
# 6. apply old graphs files to new (extrapolated) data
# what I have:
# 1995-2010: OECD II + E extrap
# 2011-2020: OECD II + OECD E
# 2021-2040: Lc extrap, E extrap
# extrap = extrapolated, mainly by gdp data from world bank. there's ARIMA in gdp and linear extrapolation in japan gdp





below is a general summery of Bench marking, taken from Lcextrap07.py before I removed plotting from it.

copy here Lcestrap07.py before I remove copy from here








