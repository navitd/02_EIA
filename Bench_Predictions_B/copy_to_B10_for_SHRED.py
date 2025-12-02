

SHRED=1
if SHREAD:
    print('graphs output 1 and 2 are done')

    # Canada, 2030
    df_can_2030 = dfoutput[(dfoutput['country'] == 'CAN') &
                        (dfoutput['year'] == 2030)]

    plt.plot(df_can_2030['sector'], df_can_2030['E'], marker='o')
    plt.xlabel("Sector")
    plt.ylabel("E")
    plt.title("Output by sector for Canada in 2030")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()