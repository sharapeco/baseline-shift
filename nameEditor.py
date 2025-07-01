from enum import Enum
import re
from typing import  List, Set, Optional, Union
from fontTools.ttLib import TTFont
from fontTools.ttLib.ttFont import newTable
from name import decodeName

Pattern = Union[str, re.Pattern[str]]

class Op(Enum):
	SUB = 1
	REPLACE = 2

class Edit:
	"""
		名前を編集する

		```
		# 一部を置換する
		Edit(1, Op.SUB, r'foo', 'bar')
		# 全部置換する
		Edit(2, Op.REPLACE, 'Medium')
		```
	"""
	def __init__(self, nameIDs: Union[int, List[int], Set[int]], op: Op, pattern: Pattern, replacement: Optional[str] = None) -> None:
		if isinstance(nameIDs, int):
			nameIDs = {nameIDs}
		elif isinstance(nameIDs, list):
			nameIDs = set(nameIDs)
		elif isinstance(nameIDs, set):
			pass
		else:
			raise ValueError(f'Invalid nameIDs type: {type(nameIDs)}')

		self.nameIDs: Set[int] = nameIDs
		self.op: Op = op
		self.pattern: Pattern = pattern
		self.replacement: Optional[str] = replacement

class NameEditor:
	def __init__(self, operations: List[Edit]) -> None:
		self.operations: List[Edit] = operations

	def edit(self, font: TTFont) -> None:
		"""フォント情報を変更する"""
		self.removeUnsupportedLangNames(font)

		for record in font['name'].names:
			value = decodeName(record)
			for op in self.operations:
				if record.nameID not in op.nameIDs:
					continue
				if op.op == Op.REPLACE:
					record.string = value = op.pattern
				elif op.op == Op.SUB:
					record.string = value = re.sub(op.pattern, op.replacement, value)

	def removeUnsupportedLangNames(self, font: TTFont) -> None:
		"""サポートしない言語の名前を削除する"""
		newNameRecords = []
		for record in font['name'].names:
			# 3: Windows のみ
			if record.platformID != 3:
				continue
			# 0x409: 英語, 0x411: 日本語 のみ
			if record.langID not in {0x409, 0x411}:
				continue
			newNameRecords.append(record)

		newNameTable = newTable('name')
		newNameTable.names = newNameRecords
		font['name'] = newNameTable
