def join_dataframes(df1, df2, join_type='left'):
    """
    Join two dataframes by their index.
    it is assumed that index is the same and that column names are unique
    """
    df = df1.join(df2, how=join_type)
    return df


def slice_dataframe_by_columns(df, selected_columns):
    """Slice by columns only"""
    return slice_dataframe(df, start_row='', end_row='', selected_columns=selected_columns)


def slice_dataframe(df, start_row='', end_row='', selected_columns=''):
    """Helper method to handle slicing"""
    if selected_columns:
        if start_row:
            return df.ix[start_row:end_row, selected_columns]
        return df.ix[:, selected_columns]
    return df.ix[start_row:end_row]