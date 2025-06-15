import sys
from pathlib import Path
import pandas as pd




def multipliers_by_f(M, fcdf_year2, title):
    fcdf_year2 = fcdf_year2.values.reshape(-1, 1) if isinstance(fcdf_year2, pd.Series) else fcdf_year2
    result = M.values @ fcdf_year2
    result_df = pd.DataFrame(result, index=M.index, columns=[title])
    return result_df