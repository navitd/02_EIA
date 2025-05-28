#this code does what tanveer's excel does but it is not neeed - I don't read the values from tanveer's file'




def get_obs_value(file_name, year, text, sector):
    #right now it reads from SUT, tanveer's file, but I woud like to do it in load_Data -where I upload compensation of employees data'
    # Load the SUT sheet
    df = pd.read_excel(file_name, sheet_name='SUT', engine='openpyxl')
    
    # Ensure relevant columns exist
    required_columns = ['Y', 'JL', 'K', 'OBS_VALUE']
    for col in required_columns:
        if col not in df.columns:
            raise ValueError(f"Column '{col}' not found in SUT sheet.")
    
    # Filter rows based on criteria
    filtered = df[(df['Y'] == year) & (df['JL'] == text) & (df['K'] == sector)]
    
    if filtered.empty:
        return None  # or raise an error if preferred
    
    # Return the OBS_VALUE (first match if multiple)
    return filtered['OBS_VALUE'].iloc[0]