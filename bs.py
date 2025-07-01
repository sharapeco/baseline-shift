import sys
import os
from typing import Union
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables import G_P_O_S_, G_S_U_B_
from fontTools.ttLib.tables.otTables import Coverage, Feature, FeatureRecord, LangSys, Lookup, Script, ScriptRecord, SinglePos, ValueRecord
from colorama import just_fix_windows_console, Fore, Style

from gpos import createGPOSTable
from nameEditor import NameEditor, Edit, Op
from pp import pp

def showHelp() -> None:
	print('べースラインを調整するための Bs00–Bs99, BS00–BS99 フィーチャーを追加します。')
	print('')
	print('Usage:')
	print('    bs [OPTIONS] <INPUT>')
	print('')
	print('Options:')
	print('    -o <PATH>    出力パスを指定してフォントを出力する')
	print('    -O           フォントを出力する (元の名前に bs を追加)')
	print('    -W           Webフォントを出力する (元の名前に bs を追加)')
	print('    -h, --help   詳細なヘルプを表示する')

def showDetailedHelp() -> None:
	print('')
	print('詳細:')
	print('')
	print('存在しないフィーチャーを追加してベースラインシフトを実現します。')
	print('  Bs00–Bs99: 下方向に 0.5em まで 0.005em 単位でシフトする')
	print('  BS00–BS99: 上方向に 0.5em まで 0.005em 単位でシフトする')
	print('ここで 00 は 100 の意味です。')

TableType = Union[G_P_O_S_.table_G_P_O_S_, G_S_U_B_.table_G_S_U_B_]

class BaselineModBuilder:
	def __init__(self, font: TTFont, verbose: bool = False) -> None:
		self.font = font
		self.verbose = verbose
		self.gpos: G_P_O_S_.table_G_P_O_S_ = self.getGPOSTable()
		self.upm: int = self.font['head'].unitsPerEm

	def run(self) -> None:
		"""ベースラインシフトのフィーチャーを追加する"""
		langSys = self.getDefaultScriptDefaultLangSys()

		coverage = self.createCoverage()

		# 1から100まで繰り返し
		for i in range(1, 101):
			self.addBaselineFeature(langSys, coverage, i)

		# -1から-100まで繰り返し
		for i in range(-1, -101, -1):
			self.addBaselineFeature(langSys, coverage, i)

	def addBaselineFeature(self, langSys: LangSys, coverage: Coverage, index: int) -> None:
		"""ベースラインシフトのフィーチャーを追加する"""

		# フィーチャータグ
		if index < 0:
			tag = f'Bs{(-index % 100):02d}'
		else:
			tag = f'BS{(index % 100):02d}'

		# シフト量を決める
		shiftAmount = int(index * 0.005 * self.upm)
		print(f'«{index}» Feature {tag} のシフト量: {shiftAmount} UPM')

		value = ValueRecord()
		value.YPlacement = shiftAmount

		subTable = SinglePos()
		subTable.Format = 1
		subTable.Coverage = coverage
		subTable.ValueFormat = 2 # y placement
		subTable.Value = value

		lookup = Lookup()
		lookup.LookupType = 1  # Single Positioning
		lookup.LookupFlag = 0
		lookup.SubTableCount = 1
		lookup.SubTable = [subTable]

		# 追加する予定の Lookup のインデックス
		lookupIndex = len(self.gpos.LookupList.Lookup)

		self.gpos.LookupList.Lookup.append(lookup)
		self.gpos.LookupList.LookupCount += 1

		if self.verbose:
			print(f'{Fore.GREEN}Lookup [{lookupIndex}] を追加しました ({tag}){Style.RESET_ALL}')

		feature = Feature()
		feature.FeatureParams = None
		feature.LookupCount = 1
		feature.LookupListIndex = [lookupIndex]

		featureRecord = FeatureRecord()
		featureRecord.FeatureTag = tag
		featureRecord.Feature = feature

		featureIndex = len(self.gpos.FeatureList.FeatureRecord)

		self.gpos.FeatureList.FeatureRecord.append(featureRecord)
		self.gpos.FeatureList.FeatureCount += 1

		if self.verbose:
			print(f'{Fore.GREEN}Feature [{featureIndex}] を追加しました ({tag}){Style.RESET_ALL}')

		langSys.FeatureIndex.append(featureIndex)
		langSys.FeatureCount += 1

		if self.verbose:
			print(f'{Fore.GREEN}LangSys に FeatureIndex {featureIndex} を追加しました ({tag}){Style.RESET_ALL}')

	def createCoverage(self) -> Coverage:
		"""カバレッジテーブルを作成する"""
		coverage = Coverage()
		coverage.format = 1
		coverage.glyphs = []

		# 全グリフを追加
		for glyph in self.font.getGlyphOrder():
			if glyph not in coverage.glyphs:
				coverage.glyphs.append(glyph)

		if self.verbose:
			glyphCount = len(coverage.glyphs)
			print(f'{Fore.GREEN}Coverage テーブルを作成しました (グリフ数: {glyphCount}){Style.RESET_ALL}')

		return coverage

	def getGPOSTable(self) -> G_P_O_S_.table_G_P_O_S_:
		"""GPOS テーブルを取得する"""
		if 'GPOS' not in self.font:
			self.font['GPOS'] = createGPOSTable()
		return self.font['GPOS'].table

	def getDefaultScriptDefaultLangSys(self) -> LangSys:
		"""デフォルトのスクリプトのデフォルト言語システムを取得する

		ここに新しいフィーチャーを追加していく。
		"""
		scriptRecord = self.findDefaultScriptRecord()
		if scriptRecord is None:
			scriptRecord = self.createScriptRecord()

		langSys = self.findDefaultLangSys(scriptRecord)
		if langSys is None:
			langSys = self.createDefaultLangSys(scriptRecord)

		return langSys

	def createScriptRecord(self) -> ScriptRecord:
		"""新しいスクリプトレコードを作成する"""
		langSys = LangSys()
		langSys.featureCount = 0
		langSys.featureIndex = []
		langSys.lookupOrder = None
		langSys.ReqFeatureIndex = 65535

		script = Script()
		script.defaultLangSys = None
		script.langSysCount = 0
		script.langSysRecords = []

		scriptRecord = ScriptRecord()
		scriptRecord.ScriptTag = 'DFLT'
		scriptRecord.Script = script

		self.gpos.ScriptList.ScriptRecord.append(scriptRecord)
		self.gpos.ScriptList.ScriptCount += 1

		if self.verbose:
			print(f'{Fore.GREEN}GPOS テーブルに ScriptRecord を追加しました{Style.RESET_ALL}')

		return scriptRecord

	def findDefaultScriptRecord(self) -> Union[ScriptRecord, None]:
		"""デフォルトのスクリプトレコードを取得する"""
		for index, script in enumerate(self.gpos.ScriptList.ScriptRecord):
			if script.ScriptTag == 'DFLT':
				if self.verbose:
					print(f'{Fore.GREEN}既存の DFLT Script を見つけました (index: {index}){Style.RESET_ALL}')
				return script
		return None

	def findDefaultLangSys(self, scriptRecord: ScriptRecord) -> Union[LangSys, None]:
		"""デフォルトの言語システムを取得する"""
		if scriptRecord.Script.DefaultLangSys is not None:
			if self.verbose:
				print(f'{Fore.GREEN}既存の DFLT LangSys を見つけました{Style.RESET_ALL}')
			return scriptRecord.Script.DefaultLangSys
		return None

if __name__ == '__main__':
	just_fix_windows_console()

	input_file = ''
	output_file = ''
	output_auto = False
	output_format = ''  # 出力フォーマット
	show_help = False

	error = False
	flag = ''
	for index, arg in enumerate(sys.argv):
		if index == 0:
			continue
		if arg[0] == '-':
			flag = arg[1:]
			if not (flag in {'o', 'O', 'W', 'h', '-help'}):
				print('Unknown flag: -%s' % (flag))
				error = True
				break
			if flag == 'O':
				output_auto = True
				flag = ''
			elif flag == 'W':
				output_auto = True
				output_format = 'woff2'
				flag = ''
			elif flag == 'h' or flag == '-help':
				show_help = True
				flag = ''
			continue
		if flag != '':
			if flag == 'o':
				output_file = arg
			flag = ''
		else:
			input_file = arg

	if show_help:
		showHelp()
		showDetailedHelp()
		sys.exit()

	if input_file == '' or error:
		showHelp()
		sys.exit()

	if output_file == '' and output_auto:
		directory = os.path.dirname(input_file)
		name, ext = os.path.splitext(os.path.basename(input_file))
		if output_format != '':
			ext = f'.{output_format}'
		output_file = os.path.join(directory, f'{name}-bs{ext}')

	font = TTFont(input_file, fontNumber=0)
	builder = BaselineModBuilder(font, verbose=True)
	builder.run()

	ne = NameEditor([
		# 3: Unique ID
		Edit(3, Op.SUB, r'^', 'bs-'),
		# 6: PostScript Name
		Edit(6, Op.SUB, r'^', 'bs-'),
		# 20: PostScript CID FindFont Name
		Edit(20, Op.SUB, r'^', 'bs-'),
	])
	ne.edit(font)

	if output_file != '':
		font.save(output_file)
