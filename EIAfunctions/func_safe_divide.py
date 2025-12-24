import sys
from pathlib import Path
import os
import pandas as pd
import numpy as np



def safe_divide(II, output):
    # Check if there are NaNs in either II or output
    if II.isna().any().any():
        raise ValueError("Matrix II contains NaN values.")
    if output.isna().any():
        raise ValueError("Output contains NaN values.")
    
    # Replace zeros in outputc with NaN to avoid division by zero
    output_safe = output.replace(0, np.nan)
    
    # Divide II by output, handling NaN values (from division by zero)
    T = II.divide(output_safe, axis=1)
    
    # Replace any NaN values (from division by zero) with zero
    T = T.fillna(0)
    
    return T

def safe_divide_vector(vector, output):
    
    # Replace zeros in outputc with NaN to avoid division by zero
    output_safe = output.replace(0, np.nan)
    # Divide vector by output, handling NaN values (from division by zero)
    coefficient = vector.divide(output_safe, axis=0)
    # Replace any NaN values (from division by zero) with zero
    coefficient = coefficient.fillna(0)
    return coefficient



