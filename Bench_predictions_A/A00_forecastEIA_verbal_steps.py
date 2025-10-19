
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
# comparison of gdp world bank and gdp OECD : 4-11% difference in yearly total GDP
# OECD is always larger 
#compare f to waht I have, compare gdp to waht I  have
#gdp has 4-11% difference between world bank and OECD
# f has no difference.


# 5.5 A07_Tc_Lc_to_csv07.py
# collect dfTc of all years and write to file
# 5.6 A08_Tc_extrap08.py
# 5.6.1 dfTc upload
# A08_Tc_extrap08.py
# 5.6.2 Tc_1country_mean - averaging values of Tc to get the Tc_extrap for future years
# 5.6.3 from Tc_extrap (long) to Tc_wide 46x46
# 5.6.4 calculating Lc_extrap from Tc using the old function - now I have Lc for future years per country

then make it into a function, to be used in graphs

E
fc
Lc = Lc_extrap
L
T
output
GDP
II



# CGARextrap10.py
# 6. apply old graphs files to new (extrapolated) data
# what I have:
# 1995-2010: OECD II + E extrap
# 2011-2020: OECD II + OECD E
# 2021-2040: Lc extrap, E extrap
# extrap = extrapolated, mainly by gdp data from world bank. there's ARIMA in gdp and linear extrapolation in japan gdp

#f extrapolation
#A06.A collecting HFCE, fother 1995-2020 collecting sector information but fother is 1 vector
#
#A06.B dfother_final_demand has tot
# writing to A06_dfother_final_demand
# previousely part 1
#A06.C  fother_sector / fother_tot
# previouisely part 2









