from recommender import load_data

df = load_data()
for _, r in df[df["name"].isin(["เชียงคาน", "แพะเมืองผี"])].iterrows():
    print(r["name"], "->", repr(r["image_url"]))