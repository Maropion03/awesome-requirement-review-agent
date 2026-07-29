import unittest
from io import BytesIO

from docx import Document

from backend.core.parser import DocumentError, parse_document


class ParserTests(unittest.TestCase):
    def test_markdown_is_parsed_in_memory(self):
        text = parse_document("demo.md", "# Demo\n这是足够长的需求说明和验收标准。".encode())
        self.assertIn("验收标准", text)

    def test_docx_is_parsed_in_memory(self):
        document = Document()
        document.add_paragraph("Demo PRD with enough detail for review and acceptance criteria.")
        buffer = BytesIO()
        document.save(buffer)
        self.assertIn("acceptance", parse_document("demo.docx", buffer.getvalue()))

    def test_docx_tables_are_included(self):
        document = Document()
        document.add_paragraph("Demo PRD with enough introductory detail.")
        table = document.add_table(rows=1, cols=2)
        table.cell(0, 0).text = "验收条件"
        table.cell(0, 1).text = "提交后显示成功"
        buffer = BytesIO()
        document.save(buffer)
        parsed = parse_document("demo.docx", buffer.getvalue())
        self.assertIn("验收条件 | 提交后显示成功", parsed)

    def test_oversize_document_is_rejected(self):
        with self.assertRaisesRegex(DocumentError, "3.5MB"):
            parse_document("demo.md", b"a" * 3_500_001)

    def test_excessive_extracted_text_is_rejected(self):
        with self.assertRaisesRegex(DocumentError, "8 万字符"):
            parse_document("demo.md", ("# Demo\n" + "需求" * 40_001).encode())


if __name__ == "__main__":
    unittest.main()
