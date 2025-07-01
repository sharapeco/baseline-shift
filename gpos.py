from fontTools.ttLib.tables import G_P_O_S_
from fontTools.ttLib.tables.otTables import FeatureList, GPOS, LangSys, LookupList, Script, ScriptList, ScriptRecord

def createGPOSTable() -> G_P_O_S_.table_G_P_O_S_:
	"""空の GPOS テーブルを作成する"""
	featureList = FeatureList()
	featureList.FeatureCount = 0
	featureList.FeatureRecord = []

	lookupList = LookupList()
	lookupList.LookupCount = 0
	lookupList.Lookup = []

	langSys = LangSys()
	langSys.FeatureCount = 0
	langSys.FeatureIndex = []
	langSys.LookupOrder = None
	langSys.ReqFeatureIndex = 0xFFFF

	script = Script()
	script.DefaultLangSys = langSys
	script.LangSysCount = 0
	script.LangSysRecord = []

	scriptRecord = ScriptRecord()
	scriptRecord.Script = script
	scriptRecord.ScriptTag = 'DFLT'

	scriptList = ScriptList()
	scriptList.ScriptCount = 1
	scriptList.ScriptRecord = [scriptRecord]

	table = GPOS()
	table.Version = 0x00010000
	table.FeatureList = featureList
	table.LookupList = lookupList
	table.ScriptList = scriptList

	gpos = G_P_O_S_.table_G_P_O_S_()
	gpos.table = table
	gpos.tableTag = 'GPOS'
	return gpos
