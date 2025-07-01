import sys
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._n_a_m_e import NameRecord
from fontTools.misc.textTools import Tag
from colorama import just_fix_windows_console, Fore, Style
from pp import pp
import macjapanese

platformIDs = {
	0: 'uni',
	1: 'mac',
	3: 'win',
}

nameIDs = {
	0: '著作権',
	1: 'ファミリー',
	2: 'サブファミリー',
	3: '一意のフォント識別子',
	4: '完全なフォント名',
	5: 'バージョン文字列',
	6: 'PostScript Name',
	7: '商標',
	8: '製造者',
	9: 'デザイナーの名前',
	10: '説明',
	11: 'ベンダーURL',
	12: 'デザイナーURL',
	13: 'ライセンス説明',
	14: 'ライセンス情報URL',
	15: '予約',
	16: '印刷用のファミリー',
	17: '印刷用のサブファミリー',
	18: '(Mac のみ) 互換性のあるフルネーム',
	19: 'サンプルテキスト',
	20: 'PostScript CID findfont 名',
	21: 'WWS ファミリー名',
	22: 'WWS サブファミリー名',
	23: '明るい背景パレット (CPAL テーブル)',
	24: '暗い背景パレット (CPAL テーブル)',
	25: 'バリエーションの PostScript 名の接頭語',
}

macintoshLangIDs = {
	0: 'en',
	11: 'ja',
}

windowsLangIDs = {
	0x0409: 'en-US',
	0x0411: 'ja-JP',
}

def getInfo(record):
	if record.nameID >= 256:
		name = f'カスタム'
	else:
		name = '(unknown)' if record.nameID not in nameIDs.keys() else nameIDs[record.nameID]
	platform = '(unknown)' if record.platformID not in platformIDs.keys() else platformIDs[record.platformID]

	if record.platformID == 0:
		language = '(unknown)'
		encoding = 'UTF-16BE'
	elif record.platformID == 1:
		language = '(unknown)' if record.langID not in macintoshLangIDs.keys() else macintoshLangIDs[record.langID]
		encoding = 'latin-1' if record.platEncID == 0 else 'MacJapanese'
	elif record.platformID == 3:
		language = '(unknown)' if record.langID not in windowsLangIDs.keys() else windowsLangIDs[record.langID]
		encoding = 'UTF-16BE'
	else:
		language = '(unknown)'
		encoding = 'latin-1'

	return name, platform, language, encoding

def decodeName(record) -> str:
	name, platform, language, encoding = getInfo(record)

	if type(record.string) is str:
		return record.string
	elif type(record.string) is Tag:
		return str(record.string)
	elif encoding == 'MacJapanese':
		return macjapanese.decode(record.string)
	else:
		return record.string.decode(encoding)

def createNameRecord(
		nameID: int,
		value: str,
		langID: int = 0x0409, # en-US
		platEncID: int = 1, # Unicode
		platformID: int = 3, # Windows
) -> NameRecord:
	record = NameRecord()
	record.nameID = nameID
	record.platformID = platformID
	record.platEncID = platEncID
	record.langID = langID
	record.string = value
	return record

def prettyNameRecord(record) -> str:
	name, platform, language, encoding = getInfo(record)
	value = decodeName(record)
	s = ''
	s += Fore.LIGHTBLACK_EX + f'[{platform} {language}]'
	s += Fore.CYAN + f' {record.nameID:2d}'
	s += Fore.GREEN + f' {name}: '
	s += Fore.WHITE + f'{value}'
	s += Fore.LIGHTBLACK_EX + f' ({encoding})'
	s += Style.RESET_ALL
	return s

if __name__ == '__main__':
	just_fix_windows_console()

	inputFile = ''

	error = False
	flag = ''
	for index, arg in enumerate(sys.argv):
		if index == 0:
			continue
		if arg[0] == '-':
			print('Unknown flag: -%s' % (flag))
			error = True
			break
		if flag != '':
			pass
		elif inputFile == '':
			inputFile = arg
		else:
			print('Unexpected parameter: %s' % (arg))
			error = True
			break

	if inputFile == '' or error:
		print('フォントの名前情報を表示する')
		print('')
		print('Usage:')
		print('    python name.py <INPUT>')
		sys.exit()

	font = TTFont(inputFile, fontNumber=0)
	for name in font['name'].names:
		print(prettyNameRecord(name))

	if hasattr(font, 'post'):
		print(pp(font['post']))
