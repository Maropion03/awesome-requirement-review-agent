import { getDocument, GlobalWorkerOptions, OPS } from 'pdfjs-dist/build/pdf.mjs'
import workerUrl from 'pdfjs-dist/build/pdf.worker.min.mjs?url'

GlobalWorkerOptions.workerSrc = workerUrl

const MAX_DIAGRAM_PAGES = 4
const IMAGE_OPERATORS = new Set([
  OPS.paintImageXObject,
  OPS.paintInlineImageXObject,
  OPS.paintImageMaskXObject,
])

function cleanText(value) {
  return String(value || '')
    .replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F\u007F]/g, '')
    .replace(/[ \t]+\n/g, '\n')
    .replace(/\n{3,}/g, '\n\n')
    .trim()
}

function extractPageText(items) {
  const lines = []
  let current = ''
  for (const item of items) {
    if (!item?.str) continue
    current += item.str
    if (item.hasEOL) {
      if (current.trim()) lines.push(current.trim())
      current = ''
    }
  }
  if (current.trim()) lines.push(current.trim())
  return cleanText(lines.join('\n'))
}

function canvasToJpeg(canvas) {
  return new Promise((resolve, reject) => {
    canvas.toBlob((blob) => blob ? resolve(blob) : reject(new Error('PDF 页面渲染失败')), 'image/jpeg', 0.8)
  })
}

async function renderPage(page) {
  const viewport = page.getViewport({ scale: 1.8 })
  const canvas = document.createElement('canvas')
  canvas.width = Math.ceil(viewport.width)
  canvas.height = Math.ceil(viewport.height)
  const context = canvas.getContext('2d', { alpha: false })
  if (!context) throw new Error('当前浏览器无法渲染 PDF 页面')
  await page.render({ canvasContext: context, viewport }).promise
  return canvasToJpeg(canvas)
}

export async function preparePdfForReview(file) {
  const bytes = new Uint8Array(await file.arrayBuffer())
  const loadingTask = getDocument({ data: bytes })
  const pdf = await loadingTask.promise
  const pages = []

  try {
    for (let pageNumber = 1; pageNumber <= pdf.numPages; pageNumber += 1) {
      const page = await pdf.getPage(pageNumber)
      const [textContent, operatorList] = await Promise.all([
        page.getTextContent(),
        page.getOperatorList(),
      ])
      const imageCount = operatorList.fnArray.filter((operator) => IMAGE_OPERATORS.has(operator)).length
      pages.push({ pageNumber, page, imageCount, text: extractPageText(textContent.items) })
    }

    const documentText = cleanText(pages.map(({ pageNumber, text }) => `--- 第 ${pageNumber} 页 ---\n${text}`).join('\n\n'))
    if (documentText.length < 20) throw new Error('PDF 未提取到足够文本；扫描件请先完成 OCR')

    const candidates = pages
      .filter((page) => page.imageCount > 0)
      .sort((left, right) => right.imageCount - left.imageCount || left.pageNumber - right.pageNumber)
      .slice(0, MAX_DIAGRAM_PAGES)

    const diagramPages = []
    for (const candidate of candidates) {
      diagramPages.push({
        pageNumber: candidate.pageNumber,
        imageCount: candidate.imageCount,
        blob: await renderPage(candidate.page),
      })
    }

    return { documentText, pageCount: pdf.numPages, diagramPages }
  } finally {
    await loadingTask.destroy()
  }
}

export { cleanText, extractPageText }
