"""ICIO (ISIC Rev.4) sector codes -> short readable labels."""

ISIC = {
    "A01_02": "Agriculture", "A03": "Fishing",
    "B05_06": "Mining: energy", "B07_08": "Mining: metals/other", "B09": "Mining support",
    "C10T12": "Food, bev. & tobacco", "C13T15": "Textiles & apparel", "C16": "Wood products",
    "C17_18": "Paper & printing", "C19": "Coke & petroleum", "C20": "Chemicals",
    "C21": "Pharmaceuticals", "C22": "Rubber & plastics", "C23": "Non-metallic minerals",
    "C24": "Basic metals", "C25": "Fabricated metals", "C26": "Computers & electronics",
    "C27": "Electrical equipment", "C28": "Machinery NEC", "C29": "Motor vehicles",
    "C30": "Other transport eq.", "C31T33": "Other mfg & repair",
    "D": "Electricity & gas", "E": "Water & waste", "F": "Construction",
    "G": "Wholesale & retail", "H49": "Land transport", "H50": "Water transport",
    "H51": "Air transport", "H52": "Warehousing", "H53": "Postal & courier",
    "I": "Hotels & restaurants", "J58T60": "Publishing & media", "J61": "Telecommunications",
    "J62_63": "IT services", "K": "Finance & insurance", "L": "Real estate",
    "M": "Professional svc", "N": "Administrative svc", "O": "Public admin & defence",
    "P": "Education", "Q": "Health & social work", "R": "Arts & recreation",
    "S": "Other services", "T": "Household activities", "U": "Extraterritorial",
}


def label(code):
    return ISIC.get(code, code)
