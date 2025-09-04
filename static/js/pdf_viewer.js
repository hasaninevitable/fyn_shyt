// pdf_viewer.js

// Read data from the global window object
const { url, pageNumber, bbox } = window.PDF_DATA;

const canvas = document.getElementById("pdf-canvas");
const ctx = canvas.getContext("2d");
const highlightRect = document.getElementById("highlight-rect");

// Setting the worker URL for PDF.js
pdfjsLib.GlobalWorkerOptions.workerSrc =
  "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js";

pdfjsLib.getDocument(url).promise.then(pdfDoc => {
  pdfDoc.getPage(pageNumber).then(page => {
    const viewport = page.getViewport({ scale: 1.5 });

    // Resize canvas to fit the PDF page viewport
    canvas.width = viewport.width;
    canvas.height = viewport.height;

    // Render the PDF page into the canvas context
    page.render({
      canvasContext: ctx,
      viewport: viewport
    }).promise.then(() => {
      if (bbox && bbox.length === 4) {
        // bbox is expected as array: [x0, y0, x1, y1]
        // Transform PDF coords to viewport coords for highlighting
        const [x0, y0, x1, y1] = bbox;

        // pdf coordinates use bottom-left origin; canvas top-left
        // so invert y to match coordinates by viewport height
        const rect = {
          x: x0 * viewport.scale,
          y: viewport.height - y1 * viewport.scale,
          width: (x1 - x0) * viewport.scale,
          height: (y1 - y0) * viewport.scale
        };

        // Position and display the highlight div
        highlightRect.style.left = `${rect.x}px`;
        highlightRect.style.top = `${rect.y}px`;
        highlightRect.style.width = `${rect.width}px`;
        highlightRect.style.height = `${rect.height}px`;
        highlightRect.style.display = "block";
      } else {
        highlightRect.style.display = "none";
      }
    });
  });
});

console.log("PDF loaded:", url);
console.log("Rendering page:", pageNumber);
console.log("Bounding box for highlight:", bbox);
