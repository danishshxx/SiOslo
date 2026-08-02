from fastapi import UploadFile

def parse_sales_csv(file: UploadFile):
    """
    TODO: Jay bakal ngisi logic parsing CSV pakai Pandas di sini.
    Sementara di-return list kosong dulu biar server nggak error pas di-import.
    """
    return []