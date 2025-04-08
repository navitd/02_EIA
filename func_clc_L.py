import pandas as pd
import numpy as np

def clc_L(T):
    
    n = T.shape[0]
    identity_matrix = np.eye(n)
    I_minus_T = identity_matrix - T.to_numpy()

    if np.linalg.det(I_minus_T) != 0:
        L = np.linalg.inv(I_minus_T)
        Ldf = pd.DataFrame(L, columns=T.columns, index=T.index)
        L_minus_I = Ldf - pd.DataFrame(identity_matrix, index=T.index, columns=T.columns)
        return Ldf, L_minus_I
    else:
        print("Matrix I - T is not invertible.")
        raise ValueError("Stopping execution due to non-invertible matrix.")