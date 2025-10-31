
dfGDP_4graph
first_year, last_year,
varname = 'GDP'
cagr_title = f'Average GDP CAGR for ICT sectors ({first_year}–{last_year})'
stacked_shares_title = f'Stacked Average ICT GDP Share by Country, {first_year}-{last_year}'
ICTsectors
ICT_factors
highlighted
xlsx_filename = f"Bench_predictions_B/B10_graph1_GDP_data {first_year}-{last_year}.xlsx"
worksheet_name = f"GDP shares {first_year}-{last_year}"
name = 'GDP'
ICT = 'ICT'
GDP_shares, ICT_GDP_shares
fig2, GDP_ICT_share_category

if 1:
    #GDP share stacked, not average but comparison between 2011 and 2020
    if 0:
        GDP_shares, ICT_GDP_shares = get_share(dfGDP, first_year, last_year, ICTsectors,'GDP')
        plot_share_compare_frist_last_year(GDP_shares, first_year, last_year, 'GDP', f'ICT GDP {first_year} and {last_year} Share by Country')

    
    start_col = package_print_shares_to_excel(xlsx_filename, worksheet_name,dfGDP, GDP_shares, ICT_GDP_shares, GDP_ICT_share_category , name, ICT, highlighted, ICT_factors)
    

    start_row = 5 #the first row where the graphs is embedded
    embed_plots_in_excel(
    xlsx_filename,
    worksheet_name,
    start_col, start_row,
    ICT_cagr=ICT_GDP_cagr,
    shares=GDP_shares,
    ICT_factors=ICT_factors,
    cagr_title=cagr_title,
    shares_title=stacked_shares_title,
    value_column=name,
    highlighted=highlighted
)
    # the problem is that I keep on transferring variable from function to function and if I by mistake transfer the wrong variable GDP intead of output I'll be in trouble
    #it should be one function that does it all.
    #it should be one function that does it all and returns the variables out.
    B10_graphs1_and_excel2 embeds figures in excel, figures are too big, and variables are passed from function to function. need one function that does it all, but the little function sshould sill work."


    print('graphs GDP 1 and 2 are done')