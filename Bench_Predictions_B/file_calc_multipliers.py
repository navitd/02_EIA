def calc_multipliers(country, year, Ldf, Lcdf, Tc, GDP, outputc):        
            # 3. calculate multipliers
            #############################
            mo = Ldf.sum(axis=0)                       #dollar's worth of outcome per 1 dollar's worth of new final demand
            moc_trancated = Lcdf.iloc[:-1].sum(axis=0) #dollar's worth of outcome per 1 dollar's worth of new final demand

            # income multipliers mh
            Ej_by_xj = Tc.iloc[-1,:-1] #hosehold income received per dollar's worth of sector output  
            income_F_multipliers = Ldf.mul(Ej_by_xj, axis=0) #household income recieved per dollar's worth of secotr final demand
            # Ej/xj*Ljk - Ljk is how much output was sold from j to k. and j is the sector that paid the salaries, so Ej/xj is used.
            sum_income_F_multipliers = income_F_multipliers.sum(axis=0) 
        
            #income multipliers second time
            Ej_by_xj = Tc.iloc[-1,:]
            
            # GDP multipliers
            GDPc = OECD.loc['VALU', simple_II_labels + ['HFCE']]
            GDPj_by_xj = safe_divide_vector(GDPc, outputc)

            # summary of multipliers without typeI and typeII - 
            # 6 multipliers output, income, GDP, X sector2sector X simple model, closed model
            # all of the closed model multipliers are trancated (the row and column of salaries and final demand are not included)
            s2s_mo  = Ldf                       # direct + indirect effect
            s2s_moc = Lcdf                      # direct + indirect + iduced effect
            s2s_mh  = Ldf.mul(Ej_by_xj.iloc[ :-1 ], axis=0) 
            s2s_mhc = Lcdf.mul(Ej_by_xj.rename(index={'HFCE': 'employees_compensation'}), axis=0)
            s2s_mg  =  Ldf.mul(GDPj_by_xj.iloc[ :-1 ], axis=0)    
            s2s_mgc = Lcdf.mul(GDPj_by_xj.rename(index={'HFCE': 'employees_compensation'}), axis=0)
            
            return s2s_mo, s2s_moc, s2s_mh, s2s_mhc, s2s_mg, s2s_mgc, Ej_by_xj, GDPj_by_xj



from now on it should be moved to B12_GDPimpact_code_benchmark_plots.py
            ###################################################
            # multipliers: direct, indirect, induced separately
            ###################################################
            n = T.shape[0]
            # direct
            direct_o = pd.DataFrame(np.eye(n), index=s2s_mo.index, columns=s2s_mo.columns)
            direct_h = pd.DataFrame(np.zeros((n, n)), index=Ej_by_xj.iloc[:-1].index, columns=Ej_by_xj.iloc[:-1].index)
            np.fill_diagonal(direct_h.values, Ej_by_xj.values)
            direct_g = pd.DataFrame(np.zeros((n, n)), index=GDPj_by_xj.iloc[:-1].index, columns=GDPj_by_xj.iloc[:-1].index)
            np.fill_diagonal(direct_g.values, GDPj_by_xj.values)
            #indirect
            indirect_o = s2s_mo - direct_o
            #Ej_by_xj*L_minus_I = s2s_mh-Ej_by_xj
            indirect_h  = s2s_mh - direct_h
            #GDPj_by_xj*L_minus_I = s2s_mg-GDPj_by_xj
            indirect_g  = s2s_mg - direct_g
            #induced
            induced_o = s2s_moc.iloc[:-1,:-1] - s2s_mo
            induced_h = s2s_mhc.iloc[:-1,:-1] - s2s_mh
            induced_g = s2s_mgc.iloc[:-1,:-1] - s2s_mg

            

