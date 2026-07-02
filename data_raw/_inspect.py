import pyreadr

result = pyreadr.read_r("data_raw/Madrid_Sale.RData")
print("Keys:", list(result.keys()))

df = list(result.values())[0]
print(f"Shape: {df.shape}")
print(f"Columns ({len(df.columns)}):")
for c in df.columns:
    sample_val = df[c].dropna().iloc[0] if len(df) and len(df[c].dropna()) else "N/A"
    print(f"  {c}: {df[c].dtype}  (sample: {sample_val})")

print()
print("First 3 rows (key cols):")
cols = ["ASSETID", "PRICE", "UNITPRICE", "CONSTRUCTEDAREA", "ROOMNUMBER", "LONGITUDE", "LATITUDE"]
print(df[cols].head(3).to_string())

# Check Madrid-only filter & nulls
madrid = df[df["LONGITUDE"].between(-4.0, -3.0) & df["LATITUDE"].between(40.0, 41.0)]
print(f"\nMadrid area rows: {len(madrid)}")
print(f"PRICE nulls: {df['PRICE'].isna().sum()} / {len(df)}")
print(f"UNITPRICE nulls: {df['UNITPRICE'].isna().sum()} / {len(df)}")
print(f"CONSTRUCTEDAREA nulls: {df['CONSTRUCTEDAREA'].isna().sum()} / {len(df)}")
print(f"PRICE range: {df['PRICE'].min():.0f} - {df['PRICE'].max():.0f}")
print(f"UNITPRICE range: {df['UNITPRICE'].min():.1f} - {df['UNITPRICE'].max():.1f}")
print(f"CONSTRUCTEDAREA range: {df['CONSTRUCTEDAREA'].min():.1f} - {df['CONSTRUCTEDAREA'].max():.1f}")
