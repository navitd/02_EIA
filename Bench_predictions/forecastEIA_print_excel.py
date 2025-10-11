
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

#what are the files with the graphs? they are in textbook_EIA or other folders?

# 5. Lcextrap07.py
# 5.1 upload dfother to learn the future years
#     upload dfEextrap
#     add dfEextrap to 1995-2010 missing data
# 5.2 upload old T to use in future years II
# I can not have the same treatment. with future years I start from T or L
# 2 different uploading systems, for data and for extrap, once I get to L everything is the same?
# 5.3 create II and in a different file L, Lc, T, Tc for all years
# The files of future years should match the files of OECD for smooth transition?


# CGARextrap08.py
# 6. apply old graphs files to new (extrapolated) data
# what I have:
# 1995-2010: OECD II + E extrap
# 2011-2020: OECD II + OECD E
# 2021-2040: Lc extrap, E extrap
# extrap = extrapolated, mainly by gdp data from world bank. there's ARIMA in gdp and linear extrapolation in japan gdp
