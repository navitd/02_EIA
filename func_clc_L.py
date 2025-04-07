import pandas as pd
import numpy as np

def clc_L(T):
    
    
    n = T.shape[0] #number of rows
    identity_matrix = np.eye(n)
    I_minus_T = identity_matrix - T 
    if np.linalg.det(I_minus_T) != 0:
        L = np.linalg.inv(I_minus_T)
        Ldf = pd.DataFrame(L, columns=T.columns, index=T.index)
    else:
        print("Matrix I - T is not invertible.")

    L_minus_I = Ldf - pd.DataFrame(identity_matrix, index=Ldf.index, columns=Ldf.columns)

    return Ldf, L_minus_I