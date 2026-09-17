
TEXT={
"English":{"scan":"Scan Product","analyze":"Analyze Label","report":"Compliance Report","dashboard":"Dashboard","review":"Review"},
"Hindi + English":{"scan":"स्कैन उत्पाद / Scan Product","analyze":"विश्लेषण करें / Analyze","report":"अनुपालन रिपोर्ट / Compliance Report","dashboard":"डैशबोर्ड / Dashboard","review":"समीक्षा / Review"}
}
def t(key,lang="English"): return TEXT.get(lang,TEXT["English"]).get(key,key)
