import os
import re
from pathlib import Path
from typing import List, Tuple, Optional
from docx import Document
import PyPDF2
import pandas as pd


def get_default_paths():
    """获取项目默认路径"""
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent
    raw_dir = project_root / "data" / "doc_raw"
    output_dir = project_root / "data" / "docs_cleaned"
    return raw_dir, output_dir


def clean_text(text: str) -> str:
    """化工文档专用清洗：保留专业术语，剔除无意义符号"""
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'第\s*\d+\s*页\s*共\s*\d+\s*页|©\d{4}.*', '', text)
    text = re.sub(r'^\d+\.\s*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9\s\u002E\u002D\u002C\u003B\u0021\u003F\u0028\u0029\u003D\u0394]', '', text)
    text = re.sub(r'(.)\1{2,}', r'\1', text)
    return text.strip()


def extract_from_pdf(pdf_path: Path) -> str:
    """提取PDF文本（兼容扫描件OCR后文本）"""
    with open(pdf_path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        full_text = ""
        for page in reader.pages:
            try:
                text = page.extract_text(extraction_mode="layout") or ""
            except Exception:
                text = page.extract_text() or ""
            full_text += text + "\n"
    try:
        full_text = full_text.encode('utf-8', errors='ignore').decode('utf-8')
    except Exception:
        pass
    return clean_text(full_text)


def extract_from_docx(docx_path: Path) -> str:
    """提取Word文本（保留标题层级）"""
    doc = Document(docx_path)
    full_text = ""
    for para in doc.paragraphs:
        if para.text.strip() and not para.text.strip().startswith("表") and not para.text.strip().startswith("图"):
            full_text += para.text.strip() + "\n"
    return clean_text(full_text)


def extract_from_excel(excel_path: Path) -> str:
    """提取Excel文本：按"故障现象/原因分析/处置步骤"三列切分语义块"""
    try:
        xl_file = pd.ExcelFile(excel_path)
        full_text = ""
        chunk_count = 0

        for sheet_name in xl_file.sheet_names:
            df = pd.read_excel(xl_file, sheet_name=sheet_name)
            columns = df.columns.tolist()
            fault_col = None
            reason_col = None
            action_col = None

            for col in columns:
                col_str = str(col)
                col_lower = col_str.lower()
                if "故障现象" in col_str or "故障" in col_lower:
                    fault_col = col
                elif "原因分析" in col_str or "原因" in col_lower:
                    reason_col = col
                elif "处理措施" in col_str or "处置" in col_lower or "步骤" in col_lower or "措施" in col_lower:
                    action_col = col

            if fault_col and reason_col and action_col:
                for idx, row in df.iterrows():
                    fault = str(row.get(fault_col, ""))
                    reason = str(row.get(reason_col, ""))
                    action = str(row.get(action_col, ""))
                    if fault.strip() and reason.strip() and action.strip():
                        chunk = f"故障现象：{fault}\n原因分析：{reason}\n处置步骤：{action}\n"
                        full_text += chunk
                        chunk_count += 1
            else:
                for col in df.columns:
                    for val in df[col].dropna():
                        if str(val).strip():
                            full_text += str(val) + "\n"

        return clean_text(full_text)
    except Exception as e:
        return ""


def split_into_chunks(text: str, chunk_size: int = 300, overlap: int = 50) -> List[str]:
    """按语义切分：优先在句号/分号/换行处分割，避免切断化工术语和带单位数值"""
    unit_pattern = r'[A-Za-zΔ]+\s*=\s*\d+(\.\d+)?[A-Za-z°]+|\d+(\.\d+)?[A-Za-z°]+'
    text = re.sub(unit_pattern, lambda m: m.group(0).replace(' ', '_SPACE_'), text)
    sentences = re.split(r'(?<=[。；！？])\s+|[\r\n]+', text)
    chunks = []
    current_chunk = ""

    for sent in sentences:
        if len(current_chunk) + len(sent) <= chunk_size:
            current_chunk += sent + " "
        else:
            if current_chunk.strip():
                chunks.append(current_chunk.strip())
            current_chunk = sent + " "

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    final_chunks = []
    for i, chunk in enumerate(chunks):
        chunk = chunk.replace('_SPACE_', ' ')
        if i == 0:
            final_chunks.append(chunk)
        else:
            prev_chunk = chunks[i-1].replace('_SPACE_', ' ')
            unit_match = re.search(unit_pattern, prev_chunk[::-1])
            if unit_match:
                overlap_adjusted = min(overlap, len(prev_chunk) - unit_match.end())
                prev = prev_chunk[-overlap_adjusted:] if len(prev_chunk) > overlap_adjusted else prev_chunk
            else:
                prev = prev_chunk[-overlap:] if len(prev_chunk) > overlap else prev_chunk
            final_chunks.append(prev + " " + chunk)

    return final_chunks


class DocumentProcessor:
    def __init__(self, raw_dir: Path, output_dir: Path):
        self.raw_dir = Path(raw_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def process_all(self) -> List[Tuple[str, str]]:
        """处理目录下所有文档"""
        results = []
        for file_path in self.raw_dir.iterdir():
            if file_path.suffix.lower() in ['.pdf', '.docx', '.xlsx', '.xls']:
                try:
                    chunks = self.process_file(file_path)
                    results.append((file_path.name, chunks))
                except Exception as e:
                    print(f"处理失败 {file_path.name}：{str(e)}")
        return results

    def process_file(self, file_path: Path) -> List[str]:
        """处理单个文件"""
        if file_path.suffix.lower() == '.pdf':
            raw_text = extract_from_pdf(file_path)
        elif file_path.suffix.lower() == '.docx':
            raw_text = extract_from_docx(file_path)
        elif file_path.suffix.lower() in ['.xlsx', '.xls']:
            raw_text = extract_from_excel(file_path)
        else:
            return []

        chunks = split_into_chunks(raw_text)
        with open(self.output_dir / f"{file_path.stem}_chunks.txt", "w", encoding="utf-8") as f:
            for i, c in enumerate(chunks):
                f.write(f"[片段{i+1}]\n{c}\n{'='*50}\n")
        return chunks


if __name__ == "__main__":
    raw_dir, output_dir = get_default_paths()
    print(f"原始文档目录: {raw_dir}")
    print(f"输出目录: {output_dir}")

    processor = DocumentProcessor(raw_dir, output_dir)
    results = processor.process_all()

    total_chunks = sum(len(chunks) for _, chunks in results)
    print(f"\n处理完成！共处理 {len(results)} 个文档，生成 {total_chunks} 个知识片段")
    for name, chunks in results:
        print(f"  - {name}: {len(chunks)} 片段")
