

# graph 3 (backward)
# 30.12.25
# to delete: eventually the package_print_embed_plot_options_impacts and package_print_embed_plot_option should be merged into one function
# I think it can be done presently I don't think there is a difference between them.
def package_print_embed_plot_option_impacts(dfim, varname, first_year, last_year, year_range, countries,
                        ICTsectors, ICTcategories, highlighted, cagr_title, stacked_shares_title,
                        end_years_title, xlsx_filename, worksheet_name, start_row, ICT,
                        embed_or_plot):
    
    title_size=6
    # fig 1:  CAGR 
    cagr = clc_cagr(dfim, first_year, last_year, varname) 
    #varname used to be GDP, output, etc. now I want to be able to choose 
    if embed_or_plot>0:
        # fig1: plot output CAGR
        plot_cagr(cagr, cagr_title)

    varname_shares, ICT_varname_shares = get_share(dfim, varname, first_year, last_year, ICTsectors)
    varname_ICT_share_category = get_share_by_category(ICT_varname_shares, varname, ICTcategories, desired_order)
    if embed_or_plot>0:
        # fig2B: stacked output share
        #this is the average of each category - stacked. 
        #change the following: GDP_ICT_share_category alreadyby category
        _ = plot_stacked_shares(varname_ICT_share_category, varname, ICTcategories, desired_order, stacked_shares_title, highlighted)

    # fig 2C: end years comparison compare first_year with last_year, stacked
    if embed_or_plot>0:
        plot_share_compare_first_last_year(varname_shares, varname, first_year, last_year, end_years_title)
                                            

    # print data to excel (if I take it out of the if statement it will print every time it runs)
    if (embed_or_plot==0) or (embed_or_plot==2):
        # next 10 lines: previousely the function "package print shares to excel"
        start_col = 1
        start_col = create_excel_file_with_title(worksheet_name, xlsx_filename )
        for year in year_range:
            for country in countries: 
                start_col = append_styled_matrix_to_excel(dfim[(dfim.country==country) & (dfim.year==year)], 
                                                          varname, worksheet_name, start_col, xlsx_filename, highlighted, title_size )
                 
        
        start_col = append_styled_matrix_to_excel(varname_shares, varname+'_shares', worksheet_name, start_col, filename=xlsx_filename, highlighted_sectors=highlighted, title_size=title_size)
        start_col = append_styled_matrix_to_excel(ICT_varname_shares, ICT+varname+' shares', worksheet_name, start_col, filename=xlsx_filename, highlighted_sectors=highlighted, title_size=title_size)

        start_col = append_styled_matrix_by_category_to_excel(varname_ICT_share_category, xlsx_filename, worksheet_name, varname+ICT+' by category',start_col, ICTcategories, highlighted, title_size=title_size)
        #                                                     (df,                     filename,      worksheet_name,  matrix_name,              start_col, ICTcategories, highlighted, title_size)

        # embed plots to excel
        col_letter = get_column_letter(start_col)
         
        # === embed1. Create both plots and save to in-memory buffers ===
        # CAGR plot
        fig1 = plot_cagr(cagr, cagr_title)
        buf1 = BytesIO()
        fig1.savefig(buf1, format='png', bbox_inches='tight', dpi=200)
        buf1.seek(0)

        # Stacked shares plot
        fig2 = plot_stacked_shares(varname_ICT_share_category, varname, ICTcategories, desired_order, stacked_shares_title, highlighted)
                                       
                
        
        buf2 = BytesIO()
        fig2.savefig(buf2, format='png', bbox_inches='tight', dpi=200)
        buf2.seek(0)

        # === embed2. Open Excel workbook and worksheet ===
        wb = load_workbook(xlsx_filename)
        ws = wb[worksheet_name]

        # === embed3. Insert both plots ===
        img1 = XLImage(buf1)
        img1.anchor = f"{col_letter}{start_row}"
        ws.add_image(img1)

        img2 = XLImage(buf2)
        img2.anchor = f"{col_letter}{start_row+30}"
        ws.add_image(img2)

        # === embed4. Save the Excel workbook ===
        wb.save(xlsx_filename)
        print(f"✅ Two plots were embedded into '{worksheet_name}' of '{xlsx_filename}'.")

