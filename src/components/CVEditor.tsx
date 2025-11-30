import { useState, useRef, useEffect } from 'react';
import { flushSync } from 'react-dom';
import { Save, CheckCircle2, Sparkles, Loader2, Eye, Edit, FileText, Download, Wand2, X, Bold, Italic, List, AlignLeft, Code, Palette, RefreshCw, Settings, AlignCenter, AlignRight, Type, Underline, ListOrdered, Link, Undo, Redo, Eraser, Highlighter, Copy, ClipboardCheck } from 'lucide-react';
import { applicationsAPI } from '../api/client';
import Editor from '@monaco-editor/react';
import { downloadStringAsFile } from '../utils/documentExport';
import { FullScreenLoader } from './FullScreenLoader';

interface CVEditorProps {
  cvId: string;
  initialHtml: string;
  jobTitle?: string;
  company?: string;
  jobId?: string;
  onSave?: (html: string, status: 'draft' | 'final') => void;
  onClose?: () => void;
}

export const CVEditor = ({
  cvId,
  initialHtml,
  jobTitle,
  company,
  jobId,
  onSave,
  onClose
}: CVEditorProps) => {
  const [htmlContent, setHtmlContent] = useState(initialHtml);
  const [isPreview, setIsPreview] = useState(false);
  const [editMode, setEditMode] = useState<'visual' | 'html' | 'css'>('visual');
  const [cssContent, setCssContent] = useState('');
  const [saving, setSaving] = useState(false);
  const [validating, setValidating] = useState(false);
  const [assisting, setAssisting] = useState(false);
  const [refining, setRefining] = useState(false);
  const [regenerating, setRegenerating] = useState(false);
  const [showRegenerateConfirm, setShowRegenerateConfirm] = useState(false);
  const [agentSteps, setAgentSteps] = useState<any[]>([]);
  const [currentStep, setCurrentStep] = useState<string | undefined>();
  const [status, setStatus] = useState<'draft' | 'final'>('draft');
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [downloadingPreview, setDownloadingPreview] = useState<'html' | 'pdf' | null>(null);
  const [validationResult, setValidationResult] = useState<any>(null);
  const [selectedText, setSelectedText] = useState('');
  const [showCustomDialog, setShowCustomDialog] = useState(false);
  const [customInstruction, setCustomInstruction] = useState('');
  const [showAIWriteDialog, setShowAIWriteDialog] = useState(false);
  const [aiWriteInstruction, setAIWriteInstruction] = useState('');
  const [formatUpdateTrigger, setFormatUpdateTrigger] = useState(0);
  const [isEditorFocused, setIsEditorFocused] = useState(false);
  const [currentFontSize, setCurrentFontSize] = useState<string>('3');
  const [copiedFormat, setCopiedFormat] = useState<{
    styles: CSSStyleDeclaration;
    element: HTMLElement | null;
  } | null>(null);
  const iframeRef = useRef<HTMLIFrameElement>(null);
  const previewIframeRef = useRef<HTMLIFrameElement>(null);
  const selectedRangeRef = useRef<Range | null>(null);
  const isUpdatingFromIframeRef = useRef<boolean>(false);
  
  // Listen for format state updates
  useEffect(() => {
    const handleFormatUpdate = () => {
      setFormatUpdateTrigger(prev => prev + 1);
    };
    window.addEventListener('formatStateUpdate', handleFormatUpdate);
    return () => window.removeEventListener('formatStateUpdate', handleFormatUpdate);
  }, []);

  // Get current font size from selection
  const getCurrentFontSize = (): string => {
    if (!iframeRef.current || editMode !== 'visual') return '3';
    
    const iframe = iframeRef.current;
    const iframeDoc = iframe.contentDocument || iframe.contentWindow?.document || null;
    
    if (iframeDoc) {
      const selection = iframeDoc.getSelection();
      if (selection && selection.rangeCount > 0) {
        const range = selection.getRangeAt(0);
        let element: HTMLElement | null = null;
        
        const container = range.commonAncestorContainer;
        if (container.nodeType === Node.TEXT_NODE && container.parentElement) {
          element = container.parentElement as HTMLElement;
        } else if (container.nodeType === Node.ELEMENT_NODE) {
          element = container as HTMLElement;
        }
        
        // Walk up to find element with font-size style (check inline styles first)
        while (element && element !== iframeDoc.body) {
          // Check inline style first (most specific)
          const inlineFontSize = element.style.fontSize;
          if (inlineFontSize) {
            const sizeInPx = parseFloat(inlineFontSize);
            if (sizeInPx <= 10) return '1';
            else if (sizeInPx <= 12) return '2';
            else if (sizeInPx <= 14) return '3';
            else if (sizeInPx <= 18) return '4';
            else if (sizeInPx <= 24) return '5';
            else if (sizeInPx <= 36) return '6';
            else return '7';
          }
          
          // Check computed styles
          const computedStyles = iframeDoc.defaultView?.getComputedStyle(element);
          if (computedStyles) {
            const fontSize = computedStyles.fontSize;
            if (fontSize && fontSize !== '16px') { // 16px is usually browser default
              // Convert pixel size to dropdown value
              const sizeInPx = parseFloat(fontSize);
              if (sizeInPx <= 10) return '1';
              else if (sizeInPx <= 12) return '2';
              else if (sizeInPx <= 14) return '3';
              else if (sizeInPx <= 18) return '4';
              else if (sizeInPx <= 24) return '5';
              else if (sizeInPx <= 36) return '6';
              else return '7';
            }
          }
          element = element.parentElement;
        }
      }
    }
    return '3'; // default
  };

  // Update current font size when selection changes (debounced to prevent forced reflows)
  useEffect(() => {
    if (editMode === 'visual' && formatUpdateTrigger >= 0) {
      // Use requestAnimationFrame to batch layout reads and prevent forced reflows
      const rafId = requestAnimationFrame(() => {
        const fontSize = getCurrentFontSize();
        setCurrentFontSize(fontSize);
      });
      return () => cancelAnimationFrame(rafId);
    }
  }, [formatUpdateTrigger, editMode]);

  // Extract CSS styles from HTML
  const extractStyles = (html: string): string => {
    try {
      const parser = new DOMParser();
      const doc = parser.parseFromString(html, 'text/html');
      const styles = doc.querySelectorAll('style');
      return Array.from(styles).map(style => style.innerHTML).join('\n');
    } catch {
      return '';
    }
  };

  const normalizeImprovedHtml = (html: string): string => {
    if (!html) return '';
    let trimmed = html.trim();
    if (trimmed.startsWith('```')) {
      const lines = trimmed.split('\n');
      if (lines.length > 2) {
        lines.shift();
        if (lines[lines.length - 1].startsWith('```')) {
          lines.pop();
        }
        trimmed = lines.join('\n').trim();
      } else {
        trimmed = trimmed.replace(/```/g, '').trim();
      }
    }
    return trimmed;
  };

  const buildDownloadFilename = (format: 'html' | 'pdf') => {
    const job = (jobTitle || 'tailored_cv')
      .replace(/[^a-z0-9]/gi, '_')
      .toLowerCase()
      .substring(0, 30);
    const companyName = (company || 'role')
      .replace(/[^a-z0-9]/gi, '_')
      .toLowerCase()
      .substring(0, 20);
    const suffix = companyName || 'preview';
    return `cv_${job}_${suffix}.${format}`;
  };

  /**
   * Remove page break markup from HTML content
   */
  const cleanHtmlForExport = (html: string): string => {
    if (!html) return html;

    const parser = new DOMParser();
    const doc = parser.parseFromString(html, 'text/html');

    // Remove page break indicator elements
    const selectorsToRemove = [
      '.preview-page-indicator',
      '.preview-page-separator',
      '.preview-page-line',
      '.preview-page-label',
      '.preview-page-count',
      '#preview-page-warning',
      '.page-break-indicator',
      '.page-break-label',
      '.page-break-line',
      '.page-sheet-separator'
    ];

    selectorsToRemove.forEach(selector => {
      doc.querySelectorAll(selector).forEach(el => el.remove());
    });

    // Remove page break styles and preview-specific styles from style tags
    const styleTags = doc.querySelectorAll('style');
    styleTags.forEach(style => {
      if (style.textContent) {
        // Remove CSS rules related to page break indicators
        let css = style.textContent;
        
        // Remove rules for preview page elements (more precise regex)
        css = css.replace(/\.preview-page-[a-z-]+\s*\{[^}]*\}/g, '');
        css = css.replace(/#preview-page-warning\s*\{[^}]*\}/g, '');
        css = css.replace(/\.page-break-[a-z-]+\s*\{[^}]*\}/g, '');
        css = css.replace(/\.page-sheet-separator\s*\{[^}]*\}/g, '');
        
        // Remove page-break-after: always from any selector (keep other page-break rules like page-break-inside: avoid)
        css = css.replace(/page-break-after:\s*always;?/g, '');
        
        // Remove grey background and padding from body (preview-specific)
        css = css.replace(/body\s*\{[^}]*background:\s*#e5e7eb[^}]*\}/g, '');
        css = css.replace(/body\s*\{[^}]*background:\s*#e5e7eb[^}]*\}/gi, '');
        
        // Remove padding and margin from body that are preview-specific
        css = css.replace(/body\s*\{[^}]*padding:\s*20px[^}]*\}/g, '');
        css = css.replace(/body\s*\{[^}]*margin:\s*0[^}]*\}/g, '');
        
        // Remove box-shadow from containers (preview effect)
        css = css.replace(/box-shadow:\s*0\s+4px\s+12px\s+rgba\(0,0,0,0\.2\)[^;]*;?/g, '');
        
        // Remove margin from containers that create spacing between pages
        css = css.replace(/margin:\s*0\s+auto\s+40px\s+auto[^;]*;?/g, '');
        
        // Clean up empty selectors (selectors with empty or only whitespace content)
        css = css.replace(/[^{}]*\{\s*\}/g, '');
        
        // Clean up multiple newlines
        css = css.replace(/\n\s*\n+/g, '\n');
        css = css.trim();
        
        style.textContent = css;
      }
    });

    // Override body styles to ensure clean export
    const body = doc.body || doc.querySelector('body');
    if (body) {
      // Remove inline styles that might have grey background
      const bodyStyle = body.getAttribute('style') || '';
      if (bodyStyle) {
        let newStyle = bodyStyle
          .replace(/background[^;]*;?/gi, '')
          .replace(/padding[^;]*;?/gi, '')
          .replace(/margin[^;]*;?/gi, '')
          .trim();
        if (newStyle) {
          body.setAttribute('style', newStyle);
        } else {
          body.removeAttribute('style');
        }
      }
    }

    // Remove margin and box-shadow from container elements
    doc.querySelectorAll('.container, body > div:first-child').forEach(el => {
      const style = el.getAttribute('style') || '';
      if (style) {
        let newStyle = style
          .replace(/margin[^;]*;?/gi, '')
          .replace(/box-shadow[^;]*;?/gi, '')
          .trim();
        if (newStyle) {
          el.setAttribute('style', newStyle);
        } else {
          el.removeAttribute('style');
        }
      }
    });

    // Remove page-break-after attribute from elements
    doc.querySelectorAll('[style*="page-break-after"]').forEach(el => {
      const style = el.getAttribute('style');
      if (style) {
        const newStyle = style.replace(/page-break-after:\s*always;?/gi, '').trim();
        if (newStyle) {
          el.setAttribute('style', newStyle);
        } else {
          el.removeAttribute('style');
        }
      }
    });

    // Get cleaned HTML
    let cleanedHtml = '';
    if (doc.body) {
      cleanedHtml = doc.body.innerHTML;
    } else {
      // If no body, get the document element
      cleanedHtml = doc.documentElement.innerHTML;
    }

    // Include styles if they exist
    const styles = Array.from(doc.querySelectorAll('style'))
      .map(style => style.outerHTML)
      .join('\n');

    // Add clean export styles to ensure no grey background or margins
    const exportStyles = `
      <style>
        body {
          background: white !important;
          margin: 0 !important;
          padding: 0 !important;
        }
        body > .container,
        body > div:first-child {
          margin: 0 !important;
          box-shadow: none !important;
        }
      </style>
    `;

    // Reconstruct clean HTML
    if (styles) {
      return `<!DOCTYPE html>\n<html>\n<head>\n<meta charset="UTF-8">\n${styles}\n${exportStyles}\n</head>\n<body>\n${cleanedHtml}\n</body>\n</html>`;
    } else {
      return `<!DOCTYPE html>\n<html>\n<head>\n<meta charset="UTF-8">\n${exportStyles}\n</head>\n<body>\n${cleanedHtml}\n</body>\n</html>`;
    }
  };

  const handlePreviewDownload = async (format: 'html' | 'pdf') => {
    if (!htmlContent) {
      setMessage({
        type: 'error',
        text: 'No CV content available to export yet.'
      });
      setTimeout(() => setMessage(null), 5000);
      return;
    }

    try {
      setDownloadingPreview(format);
      
      // Clean HTML content by removing page break markup (same for both HTML and PDF)
      let cleanedHtml: string;
      try {
        cleanedHtml = cleanHtmlForExport(htmlContent);
        // Validate cleaned HTML is not empty
        if (!cleanedHtml || cleanedHtml.trim().length === 0) {
          throw new Error('Cleaned HTML is empty');
        }
      } catch (cleanError: any) {
        console.error('HTML cleaning error:', cleanError);
        // If cleaning fails, use original HTML as fallback
        cleanedHtml = htmlContent;
        console.warn('Using original HTML due to cleaning error');
      }

      if (format === 'html') {
        const filename = buildDownloadFilename('html');
        // HTML download
        downloadStringAsFile(cleanedHtml, filename, 'text/html;charset=utf-8');
        setMessage({
          type: 'success',
          text: 'CV downloaded as HTML!'
        });
        setTimeout(() => setMessage(null), 4000);
      } else {
        // PDF download - use backend service
        const filename = buildDownloadFilename('pdf');
        
        console.log('Starting PDF export via backend...', {
          cvId,
          endpoint: `/applications/prepare/cv/${cvId}/export-pdf`,
          note: 'Backend will read HTML from backend/data/cv folder'
        });
        
        try {
          // Send current HTML content to backend to ensure latest edits are included
          // This ensures unsaved edits are included in the PDF
          const pdfBlob = await applicationsAPI.exportCVToPDF(cvId, cleanedHtml);
          console.log('PDF received from backend:', {
            size: pdfBlob?.size,
            type: pdfBlob?.type
          });
          
          // Check if response is actually a PDF
          if (pdfBlob && pdfBlob.size > 0) {
            const url = window.URL.createObjectURL(pdfBlob);
            const link = document.createElement('a');
            link.href = url;
            link.download = filename;
            document.body.appendChild(link);
            link.click();

            setTimeout(() => {
              document.body.removeChild(link);
              window.URL.revokeObjectURL(url);
            }, 100);

            setMessage({
              type: 'success',
              text: 'CV downloaded as PDF!'
            });
            setTimeout(() => setMessage(null), 4000);
          } else {
            throw new Error('Invalid PDF response from server');
          }
        } catch (pdfError: any) {
          console.error('PDF generation error:', pdfError);
          console.error('Error response:', pdfError.response);
          console.error('Error status:', pdfError.response?.status);
          console.error('Error data:', pdfError.response?.data);
          
          // Try to extract detailed error message
          let errorDetail = 'Unknown error';
          
          // Check if error message is already set (from API client parsing)
          if (pdfError.message && pdfError.message !== 'Unknown error') {
            errorDetail = pdfError.message;
          } else if (pdfError.response?.data) {
            if (typeof pdfError.response.data === 'string') {
              errorDetail = pdfError.response.data;
            } else if (pdfError.response.data.detail) {
              errorDetail = pdfError.response.data.detail;
            } else if (pdfError.response.data.message) {
              errorDetail = pdfError.response.data.message;
            }
          } else if (pdfError.message) {
            errorDetail = pdfError.message;
          }
          
          // Add status code info if available
          if (pdfError.response?.status) {
            errorDetail = `[Status ${pdfError.response.status}] ${errorDetail}`;
          }
          
          throw new Error(
            `PDF generation failed: ${errorDetail}. ` +
            `Please try downloading the HTML version instead.`
          );
        }
      }
    } catch (error: any) {
      console.error('Preview download error:', error);
      const errorMsg = error?.response?.data?.detail || 
                      error?.message || 
                      `Failed to download ${format.toUpperCase()}. Please try again.`;
      setMessage({
        type: 'error',
        text: errorMsg
      });
      setTimeout(() => setMessage(null), 7000);
    } finally {
      setDownloadingPreview(null);
    }
  };

  const initializePreviewIframe = (iframe: HTMLIFrameElement) => {
    const iframeDoc = iframe.contentDocument || iframe.contentWindow?.document;
    if (!iframeDoc || !iframeDoc.body) {
      return () => {};
    }

    const ensurePreviewStyles = () => {
      if (iframeDoc.getElementById('cv-preview-style')) {
        return;
      }
      const style = iframeDoc.createElement('style');
      style.id = 'cv-preview-style';
      style.textContent = `
        body {
          background: #e5e7eb !important;
          padding: 20px !important;
          margin: 0 !important;
          min-height: 100% !important;
          box-sizing: border-box !important;
        }
        body > .container,
        body > div:first-child {
          background: white !important;
          width: 210mm !important;
          max-width: 210mm !important;
          min-height: 281mm !important;
          margin: 0 auto 40px auto !important;
          padding: 8mm 10mm !important;
          box-shadow: 0 4px 12px rgba(0,0,0,0.2) !important;
          position: relative !important;
          page-break-after: always;
          overflow: hidden;
        }
        .section {
          page-break-inside: avoid;
        }
        .item {
          page-break-inside: avoid;
        }
        .preview-page-indicator {
          pointer-events: none !important;
          z-index: 9999;
        }
        .preview-page-line {
          position: absolute;
          left: -12px;
          right: -12px;
          height: 2px;
          background: repeating-linear-gradient(
            to right,
            #cbd5e1 0px,
            #cbd5e1 8px,
            transparent 8px,
            transparent 16px
          );
          opacity: 0.85;
        }
        .preview-page-label {
          position: absolute;
          left: 50%;
          transform: translateX(-50%);
          background: rgba(15, 23, 42, 0.8);
          color: #fff;
          padding: 6px 16px;
          border-radius: 9999px;
          font-size: 12px;
          font-weight: 600;
          box-shadow: 0 4px 12px rgba(15, 23, 42, 0.25);
          white-space: nowrap;
        }
        .preview-page-count {
          position: absolute;
          right: 12px;
          background: rgba(37, 99, 235, 0.9);
          color: #fff;
          padding: 4px 12px;
          border-radius: 9999px;
          font-size: 11px;
          font-weight: 600;
          box-shadow: 0 3px 8px rgba(37, 99, 235, 0.35);
        }
        .preview-page-separator {
          position: absolute;
          left: -20px;
          right: -20px;
          height: 50px;
          background: linear-gradient(
            to bottom,
            rgba(229, 231, 235, 0) 0%,
            rgba(229, 231, 235, 0.6) 20%,
            rgba(229, 231, 235, 0.8) 50%,
            rgba(229, 231, 235, 0.6) 80%,
            rgba(229, 231, 235, 0) 100%
          );
          pointer-events: none;
          z-index: 1;
          box-shadow: 
            0 -2px 8px rgba(0, 0, 0, 0.1),
            0 2px 8px rgba(0, 0, 0, 0.1);
        }
        .preview-page-separator::before {
          content: '';
          position: absolute;
          left: 0;
          right: 0;
          top: 50%;
          height: 1px;
          background: rgba(148, 163, 184, 0.4);
          transform: translateY(-50%);
        }
        #preview-page-warning {
          position: fixed;
          top: 20px;
          left: 50%;
          transform: translateX(-50%);
          background: #ef4444;
          color: #fff;
          padding: 10px 18px;
          border-radius: 9999px;
          font-weight: 600;
          box-shadow: 0 12px 30px rgba(239, 68, 68, 0.4);
        }
        @media print {
          body {
            background: #fff !important;
            padding: 0 !important;
          }
          .preview-page-indicator,
          .preview-page-separator,
          #preview-page-warning {
            display: none !important;
          }
          body > .container,
          body > div:first-child {
            box-shadow: none !important;
            margin: 0 auto !important;
          }
        }
      `;
      iframeDoc.head.appendChild(style);
    };

    const updatePreviewLayout = () => {
      if (!iframeDoc.body) {
        return;
      }

      let container: HTMLElement | null = iframeDoc.querySelector('.container');
      if (!container) {
        const firstChild = iframeDoc.body.firstElementChild;
        if (firstChild && firstChild instanceof HTMLElement) {
          container = firstChild;
        } else {
          container = iframeDoc.body;
        }
      }

      if (container !== iframeDoc.body) {
        container.style.background = '#ffffff';
        container.style.width = '210mm';
        container.style.maxWidth = '210mm';
        container.style.minHeight = '281mm';
        container.style.margin = '0 auto 40px auto';
        container.style.padding = '8mm 10mm';
        container.style.boxShadow = '0 12px 30px rgba(15, 23, 42, 0.15)';
        container.style.position = 'relative';
        container.style.pageBreakAfter = 'always';
      }

      iframeDoc.querySelectorAll('.preview-page-indicator').forEach(el => el.remove());
      iframeDoc.querySelectorAll('.preview-page-separator').forEach(el => el.remove());
      iframeDoc.getElementById('preview-page-warning')?.remove();

      const pageHeightPx = (281 * 96) / 25.4;
      const containerHeight = container.scrollHeight || container.offsetHeight || 0;
      const totalPages = Math.max(1, Math.ceil(containerHeight / pageHeightPx));

      if (totalPages > 1) {
        for (let pageNum = 1; pageNum < totalPages; pageNum++) {
          const pageTop = pageNum * pageHeightPx;

          // Create visual separator to make pages look like separate sheets
          const separator = iframeDoc.createElement('div');
          separator.className = 'preview-page-separator';
          separator.style.top = `${pageTop - 25}px`;
          container.appendChild(separator);

          const breakLine = iframeDoc.createElement('div');
          breakLine.className = 'preview-page-indicator preview-page-line';
          breakLine.style.top = `${pageTop}px`;
          container.appendChild(breakLine);

          const pageLabel = iframeDoc.createElement('div');
          pageLabel.className = 'preview-page-indicator preview-page-label';
          pageLabel.style.top = `${pageTop - 14}px`;
          pageLabel.textContent = `Page ${pageNum + 1} starts`;
          container.appendChild(pageLabel);
        }

        for (let pageNum = 1; pageNum <= totalPages; pageNum++) {
          const badge = iframeDoc.createElement('div');
          badge.className = 'preview-page-indicator preview-page-count';
          const pageBottom = Math.min(pageNum * pageHeightPx - 24, containerHeight - 24);
          badge.style.top = `${pageBottom}px`;
          badge.textContent = `Page ${pageNum} / ${totalPages}`;
          container.appendChild(badge);
        }

        if (totalPages > 2) {
          const warning = iframeDoc.createElement('div');
          warning.id = 'preview-page-warning';
          warning.textContent = `⚠ CV currently spans ${totalPages} pages`;
          iframeDoc.body.appendChild(warning);
        }
      }

      const bodyHeight = iframeDoc.body.scrollHeight;
      const minHeight = (297 * 96) / 25.4 + 60;
      iframe.style.height = Math.max(bodyHeight + 20, minHeight) + 'px';
      iframe.style.width = `calc(210mm + 40px)`;
    };

    ensurePreviewStyles();
    iframeDoc.body.style.background = '#e5e7eb';
    iframeDoc.body.style.margin = '0';
    iframeDoc.body.style.padding = '20px';
    iframeDoc.body.style.minHeight = '100%';
    iframeDoc.body.style.boxSizing = 'border-box';

    let updateTimeout: ReturnType<typeof setTimeout> | null = null;
    const scheduleUpdate = (delay = 150) => {
      if (updateTimeout) {
        clearTimeout(updateTimeout);
      }
      updateTimeout = setTimeout(() => {
        requestAnimationFrame(() => {
          updatePreviewLayout();
        });
      }, delay);
    };

    scheduleUpdate(100);

    const observer = new MutationObserver(() => scheduleUpdate());
    observer.observe(iframeDoc.body, {
      childList: true,
      subtree: true,
      attributes: true,
      characterData: true
    });

    const resizeListener = () => scheduleUpdate(50);
    window.addEventListener('resize', resizeListener);

    return () => {
      observer.disconnect();
      window.removeEventListener('resize', resizeListener);
      if (updateTimeout) {
        clearTimeout(updateTimeout);
      }
    };
  };

  const syncIframeDocumentToState = (doc: Document) => {
    if (!doc.documentElement) {
      return;
    }
    const newHtml = `<!DOCTYPE html>
<html lang="en">
${doc.documentElement.innerHTML}`;
    isUpdatingFromIframeRef.current = true;
    setHtmlContent(newHtml);
    // Use requestAnimationFrame for faster, smoother updates
    requestAnimationFrame(() => {
      isUpdatingFromIframeRef.current = false;
    });
  };

  const insertStreamPlaceholder = (doc: Document, range: Range, snapshotHtml: string): HTMLElement => {
    const placeholder = doc.createElement('span');
    placeholder.setAttribute('data-ai-stream-placeholder', 'true');
    placeholder.style.display = 'contents';
    if (snapshotHtml) {
      placeholder.innerHTML = snapshotHtml;
    } else if (range.toString()) {
      placeholder.textContent = range.toString();
    }
    range.deleteContents();
    range.insertNode(placeholder);
    return placeholder;
  };

  const applyImprovedHtmlLegacy = (
    doc: Document,
    rangeSnapshot: Range | null,
    improvedHtml: string,
    selectedTextSnapshot: string,
    selectionHtmlSnapshot: string
  ): boolean => {
    let insertionSuccess = false;

    if (rangeSnapshot) {
      try {
        if (
          doc.contains(rangeSnapshot.startContainer) &&
          doc.contains(rangeSnapshot.endContainer)
        ) {
          const selection = doc.getSelection();
          if (selection) {
            selection.removeAllRanges();
            selection.addRange(rangeSnapshot);
          }
          rangeSnapshot.deleteContents();

          const tempDiv = doc.createElement('div');
          tempDiv.innerHTML = improvedHtml;
          const fragment = doc.createDocumentFragment();
          while (tempDiv.firstChild) {
            fragment.appendChild(tempDiv.firstChild);
          }
          rangeSnapshot.insertNode(fragment);
          rangeSnapshot.collapse(false);
          if (selection) {
            selection.removeAllRanges();
            selection.addRange(rangeSnapshot);
          }
          insertionSuccess = true;
        }
      } catch (rangeError) {
        console.error('Range-based insertion failed:', rangeError);
      }
    }

    if (insertionSuccess) {
      return true;
    }

    try {
      const bodyElement = doc.body;
      const bodyHtml = bodyElement?.innerHTML || '';
      const bodyText = bodyElement?.innerText || bodyElement?.textContent || '';

      if (selectionHtmlSnapshot && bodyHtml.includes(selectionHtmlSnapshot)) {
        const newBodyHtml = bodyHtml.replace(selectionHtmlSnapshot, improvedHtml);
        bodyElement.innerHTML = newBodyHtml;
        insertionSuccess = true;
        return true;
      }

      const normalizeText = (text: string) => text.replace(/\s+/g, ' ').trim();
      const normalizedSelectedText = normalizeText(selectedTextSnapshot);
      const normalizedBodyText = normalizeText(bodyText);

      if (normalizedSelectedText && normalizedBodyText.includes(normalizedSelectedText)) {
        const escapedSelectedText = selectedTextSnapshot.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        const regex = new RegExp(escapedSelectedText.replace(/\s+/g, '\\s+'), 'i');
        const match = bodyHtml.match(regex);
        if (match && match.index !== undefined) {
          const newBodyHtml =
            bodyHtml.substring(0, match.index) +
            improvedHtml +
            bodyHtml.substring(match.index + match[0].length);
          bodyElement.innerHTML = newBodyHtml;
          insertionSuccess = true;
        }
      }

      if (!insertionSuccess && selectedTextSnapshot) {
        const replaced = bodyHtml.replace(selectedTextSnapshot, improvedHtml);
        if (replaced !== bodyHtml) {
          bodyElement.innerHTML = replaced;
          insertionSuccess = true;
        }
      }
    } catch (fallbackError) {
      console.error('Fallback replacement failed:', fallbackError);
      insertionSuccess = false;
    }

    return insertionSuccess;
  };

  // Setup contentEditable iframe for visual editing
  useEffect(() => {
    // Skip if we're updating from within the iframe (to prevent re-initialization)
    if (isUpdatingFromIframeRef.current) {
      console.log('Skipping iframe re-initialization - update from within iframe');
      return;
    }
    
    if (iframeRef.current && editMode === 'visual' && !isPreview) {
      const iframe = iframeRef.current;
      let updateTimeout: NodeJS.Timeout;
      let isUpdating = false;
      
      const setupIframe = () => {
        const iframeDoc = iframe.contentDocument || iframe.contentWindow?.document || null;
        
        if (iframeDoc) {
          // Check if already initialized
          const isInitialized = iframeDoc.body?.hasAttribute('data-initialized');
          
          if (!isInitialized) {
            // Write the full HTML to iframe
            iframeDoc.open();
            iframeDoc.write(htmlContent);
            iframeDoc.close();
            
            // Wait for iframe to be ready
            setTimeout(() => {
              if (iframeDoc.body) {
                // Set up iframe content - no scrolling inside iframe
                iframeDoc.documentElement.style.height = 'auto';
                iframeDoc.documentElement.style.overflow = 'visible';
                iframeDoc.body.contentEditable = 'true';
                iframeDoc.body.setAttribute('data-initialized', 'true');
                iframeDoc.body.style.outline = 'none';
                iframeDoc.body.style.height = 'auto';
                iframeDoc.body.style.overflowY = 'visible';
                iframeDoc.body.style.margin = '0';
                iframeDoc.body.style.padding = '0';
                iframeDoc.body.style.minHeight = '100%';
                
                // Add page break visualization CSS
                const style = iframeDoc.createElement('style');
                style.textContent = `
                  /* A4 page visualization for editor */
                  /* A4 dimensions: 210mm × 297mm */
                  body {
                    background: #e5e7eb !important;
                    padding: 20px !important;
                    position: relative;
                  }
                  
                  /* Wrap content in page-like container */
                  body > .container,
                  body > div:first-child {
                    background: white !important;
                    width: 210mm !important;
                    max-width: 210mm !important;
                    min-height: 281mm !important; /* 297mm - 16mm margins */
                    margin: 0 auto 40px auto !important;
                    padding: 8mm 10mm !important;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.2) !important;
                    position: relative !important;
                    page-break-after: always;
                    overflow: hidden;
                  }
                  
                  /* Ensure page break indicators are always visible */
                  .page-break-indicator,
                  .page-break-label {
                    display: block !important;
                    visibility: visible !important;
                    opacity: 1 !important;
                  }
                  
                  /* Print styles - remove editor-only styling */
                  @media print {
                    body {
                      background: white !important;
                      padding: 0 !important;
                    }
                    .page-break-indicator,
                    .page-break-label {
                      display: none !important;
                    }
                    body > .container,
                    body > div:first-child {
                      box-shadow: none !important;
                      margin: 0 !important;
                    }
                  }
                  
                  /* Ensure proper page break behavior */
                  .section {
                    page-break-inside: avoid;
                  }
                  .item {
                    page-break-inside: avoid;
                  }
                `;
                iframeDoc.head.appendChild(style);
                
                // Function to create visual page sheets
                const updatePageBreakIndicators = () => {
                  // Try multiple ways to find the container
                  let container: HTMLElement | null = null;
                  
                  // First try .container class
                  const containerByClass = iframeDoc.querySelector('.container');
                  if (containerByClass && containerByClass instanceof HTMLElement) {
                    container = containerByClass;
                  } else {
                    // Try body's first child
                    const firstChild = iframeDoc.body.firstElementChild;
                    if (firstChild && firstChild instanceof HTMLElement) {
                      container = firstChild;
                    } else {
                      // Fallback to body itself
                      container = iframeDoc.body;
                    }
                  }
                  
                  if (!container) {
                    console.warn('Page break indicators: Container not found');
                    return;
                  }
                  
                  // Remove existing indicators
                  const existingIndicators = iframeDoc.querySelectorAll('.page-break-indicator, .page-break-label, .page-sheet-separator');
                  existingIndicators.forEach(el => el.remove());
                  
                  // Get actual content height (batch layout reads)
                  // Use requestAnimationFrame to ensure layout is stable before reading
                  let containerHeight = 0;
                  // Try to read layout properties in a single batch
                  if (container) {
                    containerHeight = container.scrollHeight || container.offsetHeight || 0;
                  }
                  if (!containerHeight && iframeDoc.body) {
                    containerHeight = iframeDoc.body.scrollHeight;
                  }
                  
                  // A4 page: 297mm height, with 8mm top and bottom margins = 281mm content area
                  const pageHeightMm = 281; // Content area height
                  const pageHeightPx = (pageHeightMm * 96) / 25.4; // Approximately 1061px
                  
                  // Calculate number of pages
                  const totalPages = Math.max(1, Math.ceil(containerHeight / pageHeightPx));
                  
                  // Ensure container has relative positioning
                  if (container !== iframeDoc.body) {
                    container.style.position = 'relative';
                  }
                  
                  // If content exceeds 1 page, add visual separators to create sheet effect
                  if (totalPages > 1) {
                    // Add CSS for page sheet visualization
                    const sheetStyle = iframeDoc.createElement('style');
                    sheetStyle.id = 'page-sheet-style';
                    if (iframeDoc.getElementById('page-sheet-style')) {
                      iframeDoc.getElementById('page-sheet-style')?.remove();
                    }
                    sheetStyle.textContent = `
                      /* Create visual page separations */
                      body > .container,
                      body > div:first-child {
                        position: relative !important;
                      }
                      
                      /* Add spacing between visual pages */
                      .page-sheet-separator {
                        position: absolute;
                        left: 0;
                        right: 0;
                        height: 40px;
                        pointer-events: none;
                        z-index: 100;
                      }
                      
                      /* Visual page break line */
                      .page-break-line {
                        position: absolute;
                        left: 0;
                        right: 0;
                        height: 2px;
                        background: repeating-linear-gradient(
                          to right,
                          #cbd5e1 0px,
                          #cbd5e1 8px,
                          transparent 8px,
                          transparent 16px
                        );
                        pointer-events: none;
                        z-index: 50;
                      }
                    `;
                    iframeDoc.head.appendChild(sheetStyle);
                    
                    // Create visual separators between pages
                    for (let pageNum = 1; pageNum < totalPages; pageNum++) {
                      const pageTop = pageNum * pageHeightPx;
                      
                      // Create separator space
                      const separator = iframeDoc.createElement('div');
                      separator.className = 'page-sheet-separator';
                      separator.style.cssText = `
                        top: ${pageTop}px;
                        background: transparent;
                      `;
                      container.appendChild(separator);
                      
                      // Create visual break line
                      const breakLine = iframeDoc.createElement('div');
                      breakLine.className = 'page-break-line';
                      breakLine.style.cssText = `
                        top: ${pageTop + 20}px;
                      `;
                      container.appendChild(breakLine);
                      
                      // Add page label
                      const pageLabel = iframeDoc.createElement('div');
                      pageLabel.className = 'page-break-label';
                      pageLabel.style.cssText = `
                        position: absolute;
                        top: ${pageTop + 8}px;
                        left: 50%;
                        transform: translateX(-50%);
                        background: rgba(31, 111, 235, 0.9);
                        color: white;
                        padding: 6px 16px;
                        font-size: 12px;
                        border-radius: 6px;
                        z-index: 9999;
                        pointer-events: none;
                        font-weight: 600;
                        white-space: nowrap;
                        box-shadow: 0 2px 8px rgba(0,0,0,0.2);
                      `;
                      pageLabel.textContent = `Page ${pageNum + 1} starts here`;
                      container.appendChild(pageLabel);
                    }
                    
                    // Add page number labels at bottom of each page
                    for (let pageNum = 1; pageNum <= totalPages; pageNum++) {
                      const pageBottom = pageNum * pageHeightPx - 20;
                      const pageLabel = iframeDoc.createElement('div');
                      pageLabel.className = 'page-break-label';
                      pageLabel.style.cssText = `
                        position: absolute;
                        top: ${pageBottom}px;
                        right: 20px;
                        background: rgba(31, 111, 235, 0.8);
                        color: white;
                        padding: 4px 12px;
                        font-size: 11px;
                        border-radius: 4px;
                        z-index: 9999;
                        pointer-events: none;
                        font-weight: 600;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
                      `;
                      pageLabel.textContent = `Page ${pageNum} of ${totalPages}`;
                      container.appendChild(pageLabel);
                    }
                    
                    // Show warning if content exceeds 2 pages
                    if (totalPages > 2) {
                      const warningLabel = iframeDoc.createElement('div');
                      warningLabel.className = 'page-break-label';
                      warningLabel.style.cssText = `
                        position: fixed;
                        top: 20px;
                        left: 50%;
                        transform: translateX(-50%);
                        background: #ff6b6b;
                        color: white;
                        padding: 8px 16px;
                        font-size: 12px;
                        border-radius: 6px;
                        z-index: 10000;
                        pointer-events: none;
                        font-weight: 600;
                        white-space: nowrap;
                        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
                      `;
                      warningLabel.textContent = `⚠ Content Exceeds 2 Pages (${totalPages} pages total)`;
                      iframeDoc.body.appendChild(warningLabel);
                    }
                    
                    // Adjust container to add spacing between visual pages
                    // This creates the "separate sheets" effect
                    container.style.marginBottom = '40px';
                    
                    // Add extra spacing after each page break visually
                    // We'll use CSS to create the effect
                    const pageSpacingStyle = iframeDoc.createElement('style');
                    pageSpacingStyle.id = 'page-spacing-style';
                    if (iframeDoc.getElementById('page-spacing-style')) {
                      iframeDoc.getElementById('page-spacing-style')?.remove();
                    }
                    pageSpacingStyle.textContent = `
                      /* Create visual page separation by adding background breaks */
                      body {
                        background: linear-gradient(
                          to bottom,
                          #e5e7eb 0%,
                          #e5e7eb ${pageHeightPx}px,
                          transparent ${pageHeightPx}px,
                          transparent ${pageHeightPx + 40}px
                        ) !important;
                        background-size: 100% ${pageHeightPx + 40}px !important;
                        background-repeat: repeat-y !important;
                      }
                    `;
                    iframeDoc.head.appendChild(pageSpacingStyle);
                  } else {
                    // Single page - ensure it looks like a sheet
                    container.style.boxShadow = '0 4px 12px rgba(0,0,0,0.2)';
                    container.style.margin = '0 auto 40px auto';
                  }
                  
                  // console.log(`Page sheets updated: ${totalPages} pages, container height: ${containerHeight}px, page height: ${pageHeightPx}px`);
                };
                
                // Function to resize iframe to match content (batched with requestAnimationFrame)
                const resizeIframe = () => {
                  if (iframe && iframeDoc.body) {
                    // Use requestAnimationFrame to batch layout reads
                    requestAnimationFrame(() => {
                      const bodyHeight = iframeDoc.body.scrollHeight;
                      const bodyWidth = iframeDoc.body.scrollWidth;
                      // Set iframe height to match content, with minimum of one page
                      const minHeight = (297 * 96) / 25.4; // One A4 page in pixels
                      // Minimum width: A4 width (210mm) + 40px padding (20px on each side)
                      const minWidth = (210 * 96) / 25.4 + 40; // A4 width in pixels + padding
                      iframe.style.height = Math.max(bodyHeight + 40, minHeight) + 'px';
                      iframe.style.width = Math.max(bodyWidth, minWidth) + 'px';
                    });
                  }
                };
                
                // Debounce functions to prevent excessive layout reads
                let updatePageBreakTimeout: NodeJS.Timeout | null = null;
                let resizeIframeTimeout: NodeJS.Timeout | null = null;
                
                const debouncedUpdatePageBreak = () => {
                  if (updatePageBreakTimeout) clearTimeout(updatePageBreakTimeout);
                  updatePageBreakTimeout = setTimeout(() => {
                    requestAnimationFrame(() => {
                      updatePageBreakIndicators();
                    });
                  }, 200); // Debounce to 200ms
                };
                
                const debouncedResizeIframe = () => {
                  if (resizeIframeTimeout) clearTimeout(resizeIframeTimeout);
                  resizeIframeTimeout = setTimeout(() => {
                    resizeIframe();
                  }, 200); // Debounce to 200ms
                };
                
                // Initial check and resize
                setTimeout(() => {
                  requestAnimationFrame(() => {
                    updatePageBreakIndicators();
                    resizeIframe();
                  });
                }, 500);
                
                // Update on content changes (debounced to prevent forced reflows)
                const observer = new MutationObserver(() => {
                  debouncedUpdatePageBreak();
                  debouncedResizeIframe();
                });
                
                const container = iframeDoc.querySelector('.container') || iframeDoc.body.firstElementChild;
                if (container) {
                  observer.observe(container, {
                    childList: true,
                    subtree: true,
                    attributes: true,
                    characterData: true
                  });
                  
                  // Also observe body for size changes
                  observer.observe(iframeDoc.body, {
                    childList: true,
                    subtree: true,
                    attributes: true,
                    characterData: true
                  });
                }
                
                // Resize on window resize (debounced)
                const resizeHandler = () => {
                  debouncedResizeIframe();
                };
                window.addEventListener('resize', resizeHandler);
                
                // Store cleanup functions
                const cleanup = () => {
                  window.removeEventListener('resize', resizeHandler);
                  observer.disconnect();
                  if (updatePageBreakTimeout) clearTimeout(updatePageBreakTimeout);
                  if (resizeIframeTimeout) clearTimeout(resizeIframeTimeout);
                };
                
                // Listen for changes with debouncing
                const handleInput = () => {
                  // Don't process input if editing is locked (AI processing)
                  if (iframeDoc.body?.hasAttribute('data-ai-locked')) {
                    return;
                  }
                  
                  if (isUpdating) return;
                  
                  clearTimeout(updateTimeout);
                  updateTimeout = setTimeout(() => {
                    const newHtml = `<!DOCTYPE html>
<html lang="en">
${iframeDoc.documentElement.innerHTML}`;
                    // Only update if different to prevent loops
                    if (newHtml !== htmlContent) {
                      isUpdating = true;
                      setHtmlContent(newHtml);
                      setTimeout(() => { isUpdating = false; }, 100);
                    }
                  }, 300);
                };
                
                iframeDoc.addEventListener('input', handleInput);
                iframeDoc.addEventListener('blur', handleInput);
                
                // Handle text selection for AI assist (debounced to prevent forced reflows)
                let selectionTimeout: NodeJS.Timeout | null = null;
                const handleSelection = () => {
                  // Debounce selection handling to prevent excessive getComputedStyle calls
                  if (selectionTimeout) clearTimeout(selectionTimeout);
                  selectionTimeout = setTimeout(() => {
                    const selection = iframeDoc.getSelection();
                    if (selection && selection.toString().trim() && selection.rangeCount > 0) {
                      setSelectedText(selection.toString());
                      // Store the range for later use (using ref to avoid serialization issues)
                      selectedRangeRef.current = selection.getRangeAt(0).cloneRange();
                    } else {
                      setSelectedText('');
                      selectedRangeRef.current = null;
                    }
                    // Trigger format state update to refresh format indicators (batched)
                    requestAnimationFrame(() => {
                      window.dispatchEvent(new Event('formatStateUpdate'));
                    });
                  }, 150); // Debounce to 150ms
                };
                
                iframeDoc.addEventListener('selectionchange', handleSelection);
                iframeDoc.addEventListener('keyup', handleSelection);
                iframeDoc.addEventListener('mouseup', handleSelection);
                
                // Track focus state for AI Write button
                let focusCheckInterval: NodeJS.Timeout | null = null;
                let lastFocusState = false;
                
                const checkFocus = () => {
                  const activeElement = document.activeElement;
                  const iframeWindow = iframe.contentWindow;
                  
                  // Check if iframe or its document has focus
                  const hasFocus = !!(
                    activeElement === iframe ||
                    (iframeWindow && iframeWindow.document.hasFocus()) ||
                    (iframeDoc.activeElement && iframeDoc.activeElement !== iframeDoc.body)
                  );
                  
                  // Only update state if focus actually changed to prevent flashing
                  if (hasFocus !== lastFocusState) {
                    lastFocusState = hasFocus;
                    setIsEditorFocused(hasFocus);
                  }
                };
                
                const handleFocus = () => {
                  if (!lastFocusState) {
                    lastFocusState = true;
                    setIsEditorFocused(true);
                  }
                };
                
                const handleBlur = () => {
                  // Delay blur check to allow clicking buttons
                  setTimeout(() => {
                    const activeElement = document.activeElement;
                    // Don't blur if focus moved to UI elements (buttons, dialogs, inputs)
                    if (activeElement && (
                      activeElement.tagName === 'BUTTON' ||
                      activeElement.closest('.fixed') || // Dialog
                      activeElement.closest('textarea') ||
                      activeElement.closest('input')
                    )) {
                      return;
                    }
                    checkFocus();
                  }, 200);
                };
                
                // Track clicks and keyboard events in the editor to set focus
                const handleInteraction = () => {
                  if (!lastFocusState) {
                    lastFocusState = true;
                    setIsEditorFocused(true);
                  }
                };
                
                // Set up event listeners
                iframeDoc.addEventListener('focus', handleFocus, true);
                iframeDoc.addEventListener('blur', handleBlur, true);
                iframeDoc.addEventListener('click', handleInteraction, true);
                iframeDoc.addEventListener('keydown', handleInteraction, true);
                iframe.addEventListener('focus', handleFocus);
                iframe.addEventListener('blur', handleBlur);
                iframe.addEventListener('click', handleInteraction);
                
                // Periodic check for focus state (fallback) - increased interval to reduce flashing
                focusCheckInterval = setInterval(checkFocus, 1000);
                
                // Initial focus check
                const initialFocus = !!(
                  document.activeElement === iframe ||
                  (iframe.contentWindow && iframe.contentWindow.document.hasFocus()) ||
                  (iframeDoc.activeElement && iframeDoc.activeElement !== iframeDoc.body)
                );
                lastFocusState = initialFocus;
                setIsEditorFocused(initialFocus);
                
                // Add keyboard shortcuts
                const handleKeyDown = (e: KeyboardEvent) => {
                  // Ctrl+B for bold
                  if (e.ctrlKey && e.key === 'b') {
                    e.preventDefault();
                    try {
                      iframeDoc.execCommand('bold', false);
                      const inputEvent = new Event('input', { bubbles: true });
                      iframeDoc.body.dispatchEvent(inputEvent);
                    } catch (err) {
                      console.error('Error executing bold:', err);
                    }
                    setTimeout(handleSelection, 0);
                  }
                  // Ctrl+I for italic
                  if (e.ctrlKey && e.key === 'i') {
                    e.preventDefault();
                    try {
                      iframeDoc.execCommand('italic', false);
                      const inputEvent = new Event('input', { bubbles: true });
                      iframeDoc.body.dispatchEvent(inputEvent);
                    } catch (err) {
                      console.error('Error executing italic:', err);
                    }
                    setTimeout(handleSelection, 0);
                  }
                  // Ctrl+U for underline
                  if (e.ctrlKey && e.key === 'u') {
                    e.preventDefault();
                    try {
                      iframeDoc.execCommand('underline', false);
                      const inputEvent = new Event('input', { bubbles: true });
                      iframeDoc.body.dispatchEvent(inputEvent);
                    } catch (err) {
                      console.error('Error executing underline:', err);
                    }
                    setTimeout(handleSelection, 0);
                  }
                  // Ctrl+Z for undo
                  if (e.ctrlKey && e.key === 'z' && !e.shiftKey) {
                    e.preventDefault();
                    try {
                      iframeDoc.execCommand('undo', false);
                      const inputEvent = new Event('input', { bubbles: true });
                      iframeDoc.body.dispatchEvent(inputEvent);
                    } catch (err) {
                      console.error('Error executing undo:', err);
                    }
                    setTimeout(handleSelection, 0);
                  }
                  // Ctrl+Y or Ctrl+Shift+Z for redo
                  if ((e.ctrlKey && e.key === 'y') || (e.ctrlKey && e.shiftKey && e.key === 'z')) {
                    e.preventDefault();
                    try {
                      iframeDoc.execCommand('redo', false);
                      const inputEvent = new Event('input', { bubbles: true });
                      iframeDoc.body.dispatchEvent(inputEvent);
                    } catch (err) {
                      console.error('Error executing redo:', err);
                    }
                    setTimeout(handleSelection, 0);
                  }
                };
                
                iframeDoc.addEventListener('keydown', handleKeyDown);
                
                // Return cleanup function
                return () => {
                  cleanup();
                  clearTimeout(updateTimeout);
                  if (selectionTimeout) clearTimeout(selectionTimeout);
                  if (focusCheckInterval) {
                    clearInterval(focusCheckInterval);
                  }
                  iframeDoc.removeEventListener('input', handleInput);
                  iframeDoc.removeEventListener('blur', handleInput);
                  iframeDoc.removeEventListener('selectionchange', handleSelection);
                  iframeDoc.removeEventListener('keyup', handleSelection);
                  iframeDoc.removeEventListener('mouseup', handleSelection);
                  iframeDoc.removeEventListener('keydown', handleKeyDown);
                  iframeDoc.removeEventListener('focus', handleFocus, true);
                  iframeDoc.removeEventListener('blur', handleBlur, true);
                  iframeDoc.removeEventListener('click', handleInteraction, true);
                  iframeDoc.removeEventListener('keydown', handleInteraction, true);
                  iframe.removeEventListener('focus', handleFocus);
                  iframe.removeEventListener('blur', handleBlur);
                  iframe.removeEventListener('click', handleInteraction);
                  setIsEditorFocused(false);
                };
              }
            }, 100);
          }
        }
        return undefined;
      };
      
      // Wait for iframe to load
      let cleanupFunctions: Array<() => void> = [];
      
      if (iframe.contentDocument?.readyState === 'complete') {
        const cleanup = setupIframe();
        if (cleanup) cleanupFunctions.push(cleanup);
      } else {
        iframe.addEventListener('load', () => {
          const cleanup = setupIframe();
          if (cleanup) cleanupFunctions.push(cleanup);
        }, { once: true });
      }
      
      return () => {
        clearTimeout(updateTimeout);
        iframe.removeEventListener('load', setupIframe);
        cleanupFunctions.forEach(fn => fn());
      };
    }
  }, [editMode, isPreview, htmlContent]);

  useEffect(() => {
    if (initialHtml) {
      const styles = extractStyles(initialHtml);
      setCssContent(styles);
      setHtmlContent(initialHtml);
    }
  }, [initialHtml]);

  // Update HTML when CSS changes
  const handleCssChange = (value: string | undefined) => {
    if (value !== undefined && editMode === 'css') {
      setCssContent(value);
      // Reconstruct HTML with new CSS
      const parser = new DOMParser();
      const doc = parser.parseFromString(htmlContent, 'text/html');
      const bodyContent = doc.body.innerHTML;
      const newHtml = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style>
${value}
  </style>
</head>
<body>
  ${bodyContent}
</body>
</html>`;
      setHtmlContent(newHtml);
    }
  };

  // Update HTML when Monaco editor changes
  const handleHtmlChange = (value: string | undefined) => {
    if (value !== undefined && editMode === 'html') {
      setHtmlContent(value);
      // Extract and update CSS if HTML contains style tags
      const styles = extractStyles(value);
      if (styles) {
        setCssContent(styles);
      }
    }
  };

  const handleSave = async (saveStatus: 'draft' | 'final' = status) => {
    try {
      setSaving(true);
      setMessage(null);
      
      let finalHtml = htmlContent;
      
      // If in visual mode, get latest from iframe
      if (editMode === 'visual' && iframeRef.current) {
        const iframe = iframeRef.current;
        const iframeDoc = iframe.contentDocument || iframe.contentWindow?.document || null;
        
        if (iframeDoc && iframeDoc.documentElement) {
          // Get the full HTML from iframe, preserving head and body
          const headContent = iframeDoc.head ? iframeDoc.head.innerHTML : '';
          const bodyContent = iframeDoc.body ? iframeDoc.body.innerHTML : '';
          
          finalHtml = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  ${headContent}
</head>
<body>
  ${bodyContent}
</body>
</html>`;
        }
      }
      
      const result = await applicationsAPI.saveCVDraft(cvId, finalHtml, saveStatus);
      
      if (result.success) {
        setStatus(saveStatus);
        setHtmlContent(finalHtml);
        setMessage({
          type: 'success',
          text: `CV saved as ${saveStatus}!`
        });
        onSave?.(finalHtml, saveStatus);
        setTimeout(() => setMessage(null), 3000);
      }
    } catch (err: any) {
      setMessage({
        type: 'error',
        text: err.response?.data?.detail || err.message || 'Failed to save CV'
      });
      setTimeout(() => setMessage(null), 5000);
    } finally {
      setSaving(false);
    }
  };

  // Helper function to get current HTML content from editor
  const getCurrentHtmlContent = (): string => {
    try {
      // If in visual mode, get latest from iframe
      if (editMode === 'visual' && iframeRef.current) {
        const iframe = iframeRef.current;
        
        // Check if iframe is loaded
        if (iframe.contentDocument?.readyState !== 'complete' && 
            iframe.contentWindow?.document?.readyState !== 'complete') {
          console.warn('Iframe not ready, using htmlContent state');
          return htmlContent || initialHtml || '';
        }
        
        const iframeDoc = iframe.contentDocument || iframe.contentWindow?.document || null;
        
        if (iframeDoc && iframeDoc.documentElement && iframeDoc.body) {
          // Get the full HTML from iframe, preserving head and body
          const headContent = iframeDoc.head ? iframeDoc.head.innerHTML : '';
          const bodyContent = iframeDoc.body ? iframeDoc.body.innerHTML : '';
          
          // Check if body has actual content (not just empty or whitespace)
          if (bodyContent && bodyContent.trim().length > 0) {
            const fullHtml = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  ${headContent}
</head>
<body>
  ${bodyContent}
</body>
</html>`;
            console.log('Retrieved content from iframe, length:', fullHtml.length);
            return fullHtml;
          } else {
            console.warn('Iframe body is empty, falling back to htmlContent state');
          }
        } else {
          console.warn('Iframe document or body not accessible, falling back to htmlContent state');
        }
      }
      
      // For HTML mode, use htmlContent directly (Monaco editor updates it via onChange)
      // For CSS mode, we need to inject CSS into HTML if it's not already there
      if (editMode === 'css' && cssContent) {
        // Try to inject CSS into HTML if there's a <style> tag or create one
        let htmlWithCss = htmlContent || initialHtml || '';
        if (htmlWithCss && !htmlWithCss.includes('<style>') && !htmlWithCss.includes('<link')) {
          // Inject CSS into head
          if (htmlWithCss.includes('</head>')) {
            htmlWithCss = htmlWithCss.replace('</head>', `<style>${cssContent}</style></head>`);
          } else if (htmlWithCss.includes('<body>')) {
            htmlWithCss = htmlWithCss.replace('<body>', `<head><style>${cssContent}</style></head><body>`);
          } else {
            htmlWithCss = `<head><style>${cssContent}</style></head><body>${htmlWithCss}</body>`;
          }
        }
        console.log('Using htmlContent with CSS injected, length:', htmlWithCss.length);
        return htmlWithCss;
      }
      
      // Fallback to htmlContent state if iframe access fails
      const fallbackContent = htmlContent || initialHtml || '';
      console.log('Using htmlContent state, length:', fallbackContent.length);
      return fallbackContent;
    } catch (error) {
      console.error('Error getting current HTML content:', error);
      // Fallback to htmlContent state
      const fallbackContent = htmlContent || initialHtml || '';
      console.log('Error fallback, using htmlContent state, length:', fallbackContent.length);
      return fallbackContent;
    }
  };

  const handleValidate = async () => {
    try {
      setValidating(true);
      setMessage(null);
      setValidationResult(null);
      
      // Small delay to ensure iframe is ready in visual mode
      if (editMode === 'visual' && iframeRef.current) {
        await new Promise(resolve => setTimeout(resolve, 100));
      }
      
      // Get current HTML content from editor
      let finalHtml = getCurrentHtmlContent();
      
      // If we got empty content and we're in visual mode, try one more time after a short delay
      if ((!finalHtml || finalHtml.trim().length === 0) && editMode === 'visual' && iframeRef.current) {
        console.warn('First attempt got empty content, retrying after delay...');
        await new Promise(resolve => setTimeout(resolve, 200));
        finalHtml = getCurrentHtmlContent();
      }
      
      if (!finalHtml || finalHtml.trim().length === 0) {
        setMessage({
          type: 'error',
          text: 'No content found to validate. Please ensure the CV has content and try again.'
        });
        setTimeout(() => setMessage(null), 5000);
        return;
      }
      
      // Extract text content length for validation
      const textContent = finalHtml.replace(/<[^>]+>/g, '');
      const textLength = textContent.length;
      
      console.log('Validating CV:', {
        editMode,
        htmlLength: finalHtml.length,
        textLength: textLength,
        hasIframe: !!iframeRef.current,
        iframeReady: iframeRef.current?.contentDocument?.readyState,
        firstChars: finalHtml.substring(0, 100),
        textPreview: textContent.substring(0, 200)
      });
      
      if (textLength < 200) {
        console.warn('⚠️ WARNING: CV content is very short - validation may flag this as incomplete');
      }
      
      const result = await applicationsAPI.validateCV(cvId, finalHtml);
      
      if (result.success) {
        setValidationResult(result.validation);
        const validation = result.validation;
        const score = validation.quality_score || 0;
        const issues = validation.issues || [];
        
        console.log('Validation result:', { score, issuesCount: issues.length });
        
        if (score >= 8 && issues.length === 0) {
          setMessage({
            type: 'success',
            text: `Validation passed! Quality score: ${score}/10`
          });
        } else {
          setMessage({
            type: 'error',
            text: `Quality score: ${score}/10. Found ${issues.length} issue(s)`
          });
        }
        setTimeout(() => setMessage(null), 5000);
      } else {
        setMessage({
          type: 'error',
          text: result.error || 'Validation failed'
        });
        setTimeout(() => setMessage(null), 5000);
      }
    } catch (err: any) {
      console.error('Validation error:', err);
      setMessage({
        type: 'error',
        text: err.response?.data?.detail || err.message || 'Failed to validate CV'
      });
      setTimeout(() => setMessage(null), 5000);
    } finally {
      setValidating(false);
    }
  };

  const handleRefine = async () => {
    try {
      setRefining(true);
      setMessage(null);
      
      // Save current content first
      await applicationsAPI.saveCVDraft(cvId, htmlContent, 'draft');
      
      // Call refine API
      const result = await applicationsAPI.refineCV(cvId);
      
      if (result.success) {
        // The refine API returns html_content in the result
        const refinedHtml = result.html_content || result.htmlContent || result.html;
        
        if (refinedHtml) {
          // Update HTML content with refined version
          setHtmlContent(refinedHtml);
          
          // Update CSS if available
          const styles = extractStyles(refinedHtml);
          if (styles) {
            setCssContent(styles);
          }
          
          // Reset iframe to show new content
          if (iframeRef.current && editMode === 'visual') {
            const iframe = iframeRef.current;
            const iframeDoc = iframe.contentDocument || iframe.contentWindow?.document || null;
            if (iframeDoc && iframeDoc.body) {
              iframeDoc.body.removeAttribute('data-initialized');
            }
          }
          
          setMessage({
            type: 'success',
            text: 'CV refined successfully!'
          });
          setTimeout(() => setMessage(null), 5000);
        } else {
          setMessage({
            type: 'error',
            text: 'Refined CV content not found in response'
          });
          setTimeout(() => setMessage(null), 5000);
        }
      } else {
        setMessage({
          type: 'error',
          text: result.error || 'Failed to refine CV'
        });
        setTimeout(() => setMessage(null), 5000);
      }
    } catch (err: any) {
      setMessage({
        type: 'error',
        text: err.response?.data?.detail || err.message || 'Failed to refine CV'
      });
      setTimeout(() => setMessage(null), 5000);
    } finally {
      setRefining(false);
    }
  };

  const handleRegenerate = async () => {
    if (!jobId) {
      setMessage({
        type: 'error',
        text: 'Job ID is required to regenerate CV. Please go back and try again.'
      });
      setTimeout(() => setMessage(null), 5000);
      return;
    }

    try {
      setRegenerating(true);
      setAgentSteps([]);
      setCurrentStep(undefined);
      setMessage(null);
      setShowRegenerateConfirm(false);
      
      // Use streaming endpoint for real-time step updates during regeneration
      await applicationsAPI.prepareCVStream(
        jobId,
        // onStepUpdate - called when a step starts or completes
        (update: any) => {
          console.log('Regeneration step update received:', update);
          
          if (update.type === 'step_start') {
            // Step is starting
            setCurrentStep(update.step);
          } else if (update.type === 'step_complete' && update.step_data) {
            // Step completed - add to agent steps
            setAgentSteps(prev => {
              // Check if step already exists (for refinement rounds)
              const existingIndex = prev.findIndex(
                s => s.step === update.step_data.step && 
                s.refinement_round === update.step_data.refinement_round
              );
              
              if (existingIndex >= 0) {
                // Update existing step
                const newSteps = [...prev];
                newSteps[existingIndex] = update.step_data;
                return newSteps;
              } else {
                // Add new step
                return [...prev, update.step_data];
              }
            });
            
            // Update current step to next expected step
            const expectedSteps = ['analyze_job', 'analyze_cv', 'create_strategy', 'generate_content', 'validate_output', 'refine_output'];
            const currentStepIndex = expectedSteps.indexOf(update.step_data.step);
            if (currentStepIndex >= 0 && currentStepIndex < expectedSteps.length - 1) {
              setCurrentStep(expectedSteps[currentStepIndex + 1]);
            }
          }
        },
        // onComplete - called when regeneration is complete
        (result: any) => {
          console.log('CV Regeneration Complete (CVEditor):', result);
          
          // Set final agent steps
          if (result.agent_steps) {
            setAgentSteps(result.agent_steps);
          }
          
          if (result.success && result.html_content) {
            // Update HTML content with newly generated CV
            const newHtml = result.html_content;
            setHtmlContent(newHtml);
            
            // Update CSS if available
            const styles = extractStyles(newHtml);
            if (styles) {
              setCssContent(styles);
            }
            
            // Reset iframe to show new content
            if (iframeRef.current && editMode === 'visual') {
              const iframe = iframeRef.current;
              const iframeDoc = iframe.contentDocument || iframe.contentWindow?.document || null;
              if (iframeDoc && iframeDoc.body) {
                iframeDoc.body.removeAttribute('data-initialized');
              }
            }
            
            setMessage({
              type: 'success',
              text: 'CV regenerated successfully! All previous edits have been replaced with a fresh CV.'
            });
            setTimeout(() => setMessage(null), 5000);
          } else {
            setMessage({
              type: 'error',
              text: result.error || 'Failed to regenerate CV'
            });
            setTimeout(() => setMessage(null), 5000);
          }
        },
        // onError - called on error
        (error: string) => {
          console.error('CV Regeneration Error (CVEditor):', error);
          setMessage({
            type: 'error',
            text: error
          });
          setTimeout(() => setMessage(null), 5000);
        }
      );
    } catch (err: any) {
      console.error('CV Regeneration Exception (CVEditor):', err);
      setMessage({
        type: 'error',
        text: err.response?.data?.detail || err.message || 'Failed to regenerate CV'
      });
      setTimeout(() => setMessage(null), 5000);
    } finally {
      setRegenerating(false);
      setCurrentStep(undefined);
    }
  };

  // Lock/unlock editing during AI processing
  const lockEditing = (iframeDoc: Document) => {
    if (!iframeDoc || !iframeDoc.body) return;
    
    // Disable contentEditable
    iframeDoc.body.contentEditable = 'false';
    iframeDoc.body.setAttribute('data-ai-locked', 'true');
    
    // Add overlay to prevent interactions
    let overlay = iframeDoc.getElementById('ai-processing-overlay');
    if (!overlay) {
      overlay = iframeDoc.createElement('div');
      overlay.id = 'ai-processing-overlay';
      overlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0, 0, 0, 0.02);
        z-index: 999999;
        pointer-events: all;
        cursor: wait;
      `;
      iframeDoc.body.appendChild(overlay);
    }
    
    // Disable pointer events on body
    iframeDoc.body.style.pointerEvents = 'none';
    iframeDoc.body.style.userSelect = 'none';
    iframeDoc.body.style.cursor = 'wait';
    
    // Prevent keyboard and mouse events with capture phase
    // Note: We don't prevent all events - just user interaction events
    // setTimeout callbacks are not events, so they should still work
    const preventInteraction = (e: Event) => {
      // Only prevent if it's a user interaction event, not system events
      const target = e.target as HTMLElement;
      if (target && target.hasAttribute('data-ai-stream-placeholder')) {
        // Allow updates to our placeholder element
        return;
      }
      e.preventDefault();
      e.stopPropagation();
      e.stopImmediatePropagation();
      return false;
    };
    
    // Store handlers on the document for cleanup
    const handlers = [
      { event: 'keydown', handler: preventInteraction },
      { event: 'keyup', handler: preventInteraction },
      { event: 'keypress', handler: preventInteraction },
      { event: 'mousedown', handler: preventInteraction },
      { event: 'mouseup', handler: preventInteraction },
      { event: 'click', handler: preventInteraction },
      { event: 'input', handler: preventInteraction },
      { event: 'paste', handler: preventInteraction },
      { event: 'cut', handler: preventInteraction },
      { event: 'contextmenu', handler: preventInteraction },
    ];
    
    handlers.forEach(({ event, handler }) => {
      iframeDoc.addEventListener(event, handler, { capture: true, passive: false });
    });
    
    // Store handlers for cleanup
    (iframeDoc as any).__aiLockHandlers = handlers;
  };

  const unlockEditing = (iframeDoc: Document) => {
    if (!iframeDoc || !iframeDoc.body) return;
    
    // Remove event listeners
    const handlers = (iframeDoc as any).__aiLockHandlers;
    if (handlers) {
      handlers.forEach(({ event, handler }: { event: string; handler: (e: Event) => boolean }) => {
        iframeDoc.removeEventListener(event, handler, { capture: true } as any);
      });
      delete (iframeDoc as any).__aiLockHandlers;
    }
    
    // Re-enable contentEditable
    iframeDoc.body.contentEditable = 'true';
    iframeDoc.body.removeAttribute('data-ai-locked');
    
    // Remove overlay
    const overlay = iframeDoc.getElementById('ai-processing-overlay');
    if (overlay) {
      overlay.remove();
    }
    
    // Re-enable pointer events
    iframeDoc.body.style.pointerEvents = '';
    iframeDoc.body.style.userSelect = '';
    iframeDoc.body.style.cursor = '';
  };

  const handleAIAssist = async (intent: string, customInstruction?: string) => {
    // Performance logging
    const perfLog: Array<{step: string, timestamp: number, elapsed: number}> = [];
    const startTime = performance.now();
    const logStep = (step: string) => {
      const now = performance.now();
      const elapsed = now - startTime;
      perfLog.push({step, timestamp: now, elapsed});
      console.log(`[AI Action Perf] ${step} | Elapsed: ${elapsed.toFixed(2)}ms | Time: ${new Date().toISOString()}`);
    };
    
    logStep('START: handleAIAssist called');
    setAssisting(true);
    let placeholder: HTMLElement | null = null;
    let iframeDoc: Document | null = null;
    let selectionHtmlSnapshot = '';
    const selectedTextSnapshot = selectedText;
    let legacyRange: Range | null = selectedRangeRef.current ? selectedRangeRef.current.cloneRange() : null;
    
    // Create abort controller for request cancellation
    const abortController = new AbortController();
    const abortSignal = abortController.signal;
    
    // Timeout constants
    const REQUEST_TIMEOUT = 60000; // 60 seconds
    const MAX_RETRIES = 2;
    const RETRY_DELAY = 1000; // 1 second base delay

    try {
      logStep('VALIDATION: Starting validation checks');
      if (!selectedTextSnapshot || !selectedRangeRef.current) {
        setMessage({
          type: 'error',
          text: 'Please select text to improve'
        });
        setTimeout(() => setMessage(null), 3000);
        setAssisting(false);
        return;
      }

      setMessage(null);

      if (editMode !== 'visual') {
        setMessage({
          type: 'error',
          text: 'AI assist is only available in Visual mode. Switch to Visual mode and select text.'
        });
        setTimeout(() => setMessage(null), 5000);
        return;
      }

      if (!iframeRef.current) {
        setMessage({
          type: 'error',
          text: 'Editor is not ready yet'
        });
        setTimeout(() => setMessage(null), 3000);
        return;
      }

      const iframe = iframeRef.current;
      iframeDoc = iframe.contentDocument || iframe.contentWindow?.document || null;

      if (!iframeDoc) {
        setMessage({
          type: 'error',
          text: 'Unable to access document'
        });
        setTimeout(() => setMessage(null), 3000);
        return;
      }

      // Clean up any leftover placeholders or highlights from previous AI actions
      if (iframeDoc) {
        try {
          const doc = iframeDoc; // Capture for TypeScript
          const oldPlaceholders = doc.querySelectorAll('[data-ai-stream-placeholder="true"]');
          oldPlaceholders.forEach(oldPlaceholder => {
            const parent = oldPlaceholder.parentNode;
            if (parent) {
              // Replace placeholder with its text content
              const textNode = doc.createTextNode(oldPlaceholder.textContent || '');
              parent.replaceChild(textNode, oldPlaceholder);
              parent.normalize();
            }
          });
          
          const oldHighlights = doc.querySelectorAll('.ai-processing-highlight');
          oldHighlights.forEach(highlight => {
            const parent = highlight.parentNode;
            if (parent) {
              parent.replaceChild(doc.createTextNode(highlight.textContent || ''), highlight);
              parent.normalize();
            }
          });
        } catch (cleanupError) {
          console.warn('[AI Assist] Error cleaning up previous placeholders:', cleanupError);
        }
      }
      logStep('CLEANUP: Cleanup completed');

      logStep('LOCK: Locking editing');
      // Lock editing immediately
      lockEditing(iframeDoc);
      logStep('LOCK: Editing locked');

      // Ensure we have a valid selection range after cleanup
      // Refresh selection if needed (cleanup might have affected it)
      if (!selectedRangeRef.current || selectedRangeRef.current.collapsed) {
        // Try to get current selection from iframe
        const selection = iframeDoc.getSelection();
        if (selection && selection.rangeCount > 0 && !selection.getRangeAt(0).collapsed) {
          selectedRangeRef.current = selection.getRangeAt(0).cloneRange();
        } else {
          setMessage({
            type: 'error',
            text: 'Please select text to improve'
          });
          setTimeout(() => setMessage(null), 3000);
          setAssisting(false);
          unlockEditing(iframeDoc);
          return;
        }
      }

      // Verify the range is still valid (not pointing to removed elements)
      try {
        const testRange = selectedRangeRef.current.cloneRange();
        testRange.collapsed; // Access to check if range is valid
      } catch (rangeError) {
        // Range is invalid, try to get current selection
        const selection = iframeDoc.getSelection();
        if (selection && selection.rangeCount > 0 && !selection.getRangeAt(0).collapsed) {
          selectedRangeRef.current = selection.getRangeAt(0).cloneRange();
        } else {
          setMessage({
            type: 'error',
            text: 'Selection is no longer valid. Please select text again.'
          });
          setTimeout(() => setMessage(null), 3000);
          setAssisting(false);
          unlockEditing(iframeDoc);
          return;
        }
      }

      logStep('SELECTION: Selection validated and cloned');
      const selectionRange = selectedRangeRef.current.cloneRange();
      
      logStep('HIGHLIGHT: Starting highlight');
      // Highlight the selected text with yellow background and grey text color for identification
      try {
        const selection = iframeDoc.getSelection();
        if (selection && selection.rangeCount > 0) {
          const range = selection.getRangeAt(0);
          const highlightSpan = iframeDoc.createElement('span');
          highlightSpan.style.backgroundColor = '#fef08a'; // Yellow highlight
          highlightSpan.style.color = '#6b7280'; // Grey text color for identification
          highlightSpan.style.padding = '2px 0';
          highlightSpan.className = 'ai-processing-highlight';
          try {
            range.surroundContents(highlightSpan);
          } catch (e) {
            // If surroundContents fails, try a different approach
            const contents = range.extractContents();
            highlightSpan.appendChild(contents);
            range.insertNode(highlightSpan);
          }
        }
      } catch (highlightError) {
        console.warn('[AI Assist] Failed to highlight selection:', highlightError);
      }
      logStep('HIGHLIGHT: Highlight completed');

      // Show processing message
      setMessage({
        type: 'success',
        text: 'Processing with AI...'
      });

      logStep('CAPTURE: Capturing selection HTML');
      try {
        const selectionContainer = iframeDoc.createElement('div');
        selectionContainer.appendChild(selectionRange.cloneContents());
        selectionHtmlSnapshot = selectionContainer.innerHTML || selectedTextSnapshot;
      } catch (selectionError) {
        console.warn('[AI Assist] Failed to capture selection HTML, using text fallback');
        selectionHtmlSnapshot = selectedTextSnapshot;
      }
      logStep('CAPTURE: Selection HTML captured');

      const finalIntent = customInstruction || intent;

      logStep('PLACEHOLDER: Creating placeholder');
      // Create placeholder for the improved text
      try {
        const placeholderRange = selectionRange.cloneRange();
        placeholder = insertStreamPlaceholder(
          iframeDoc,
          placeholderRange,
          selectionHtmlSnapshot || selectedTextSnapshot
        );
        placeholder.className = 'ai-processing-placeholder';
        placeholder.style.backgroundColor = '#fef08a';
        placeholder.style.padding = '2px 0';
        placeholder.innerHTML = ''; // Empty - badge shows processing state instead
        legacyRange = null;
      } catch (placeholderError) {
        console.warn('[AI Assist] Unable to insert placeholder');
        placeholder = null;
      }
      logStep('PLACEHOLDER: Placeholder created');

      let improvedHtml = '';
      let lastError: Error | null = null;

      logStep('API_REQUEST: Starting API request with retry logic');
      // Use non-streaming method with retries
      for (let attempt = 0; attempt <= MAX_RETRIES; attempt++) {
        if (attempt > 0) {
          // Exponential backoff
          const delay = RETRY_DELAY * Math.pow(2, attempt - 1);
          await new Promise(resolve => setTimeout(resolve, delay));
          setMessage({
            type: 'error',
            text: `Retrying... (attempt ${attempt + 1}/${MAX_RETRIES + 1})`
          });
        }

        try {
          const apiStartTime = performance.now();
          logStep(`API_REQUEST: Attempt ${attempt + 1}/${MAX_RETRIES + 1} - Sending request`);
          const result = await Promise.race([
            applicationsAPI.aiAssistCV(
              cvId,
              selectionHtmlSnapshot || selectedTextSnapshot,
              finalIntent,
              undefined,
              REQUEST_TIMEOUT,
              abortSignal
            ),
            new Promise<never>((_, reject) => {
              setTimeout(() => reject(new Error('Request timed out')), REQUEST_TIMEOUT);
            })
          ]);
          const apiEndTime = performance.now();
          logStep(`API_REQUEST: Attempt ${attempt + 1} - Response received (${(apiEndTime - apiStartTime).toFixed(2)}ms)`);

          if (!result.success || !result.improved_html) {
            throw new Error(result.error || 'Failed to improve text');
          }

          logStep('NORMALIZE: Normalizing improved HTML');
          improvedHtml = normalizeImprovedHtml(result.improved_html);
          logStep('NORMALIZE: HTML normalized');
          lastError = null;
          break; // Success, exit retry loop
        } catch (requestError: any) {
          lastError = requestError;
          if (attempt === MAX_RETRIES) {
            console.error('[AI Assist] Request failed after all retries:', requestError);
          }
          
          // Don't retry if it's a cancellation
          if (requestError.message?.includes('cancelled') || 
              requestError.message?.includes('aborted') ||
              abortSignal.aborted) {
            throw requestError;
          }
          
          // If this was the last attempt, throw the error
          if (attempt === MAX_RETRIES) {
            throw new Error(
              lastError?.message || 
              'Failed to improve text after multiple attempts. Please try again or select a smaller portion.'
            );
          }
        }
      }

      if (!improvedHtml) {
        console.error('[AI Assist] No improved HTML received');
        throw new Error('Failed to get improved text from AI');
      }
      logStep('API_REQUEST: All API requests completed');

      logStep('HIGHLIGHT_REMOVE: Removing highlight');
      // Remove highlight from selection (if it still exists)
      // Only remove highlights that don't contain the placeholder (placeholder replacement will handle those)
      if (iframeDoc) {
        try {
          const doc = iframeDoc; // Capture for TypeScript
          const highlights = doc.querySelectorAll('.ai-processing-highlight');
          const hasPlaceholder = !!doc.querySelector('[data-ai-stream-placeholder="true"]');
          
          highlights.forEach(highlight => {
            // Skip highlights that contain the placeholder - they'll be handled during replacement
            if (highlight.querySelector('[data-ai-stream-placeholder="true"]')) {
              return;
            }
            
            // Only remove highlights if there's no placeholder (meaning placeholder wasn't created)
            if (!hasPlaceholder) {
              const parent = highlight.parentNode;
              if (parent) {
                parent.replaceChild(doc.createTextNode(highlight.textContent || ''), highlight);
                parent.normalize();
              }
            }
          });
        } catch (e) {
        console.warn('[AI Assist] Failed to remove highlight:', e);
      }
    }
    logStep('HIGHLIGHT_REMOVE: Highlight removal completed');

    logStep('DOM_REPLACE: Starting DOM replacement');
    // Apply the improved HTML directly (no animation)
      if (placeholder) {
        const placeholderRef = placeholder;
        
        if (placeholderRef && placeholderRef.parentNode && iframeDoc) {
          try {
            // First, check if placeholder is inside a highlight and remove the highlight wrapper
            let actualPlaceholder = placeholderRef;
            let highlightWrapper = placeholderRef.closest('.ai-processing-highlight');
            if (highlightWrapper && highlightWrapper !== placeholderRef) {
              const highlightParent = highlightWrapper.parentNode;
              if (highlightParent) {
                // Move placeholder out of highlight
                while (highlightWrapper.firstChild) {
                  highlightParent.insertBefore(highlightWrapper.firstChild, highlightWrapper);
                }
                highlightParent.removeChild(highlightWrapper);
                // The placeholder should still be in the same position, no need to query again
                if (!actualPlaceholder.parentNode) {
                  // Only query if we lost the reference
                  actualPlaceholder = iframeDoc.querySelector('[data-ai-stream-placeholder="true"]') as HTMLElement;
                  if (!actualPlaceholder) {
                    throw new Error('Placeholder lost after unwrapping highlight');
                  }
                }
              }
            }
            
            // Use a reliable replacement method - batch DOM operations
            const tempDiv = iframeDoc.createElement('div');
            tempDiv.innerHTML = improvedHtml;
            
            const parent = actualPlaceholder.parentNode;
            if (!parent) {
              throw new Error('Placeholder has no parent');
            }
            
            // Batch insert all children at once for better performance
            const fragment = iframeDoc.createDocumentFragment();
            while (tempDiv.firstChild) {
              fragment.appendChild(tempDiv.firstChild);
            }
            parent.insertBefore(fragment, actualPlaceholder);
            // Remove the placeholder
            parent.removeChild(actualPlaceholder);
            logStep('DOM_REPLACE: DOM replacement completed');
            
            logStep('UI_UPDATE: Starting UI state update');
            // Update UI state immediately - force immediate render with flushSync
            // This ensures the UI updates before any async operations
            setSelectedText('');
            selectedRangeRef.current = null;
            
            // Use flushSync to force immediate React render for critical UI updates
            flushSync(() => {
              // Clear processing state FIRST to update UI immediately
              setAssisting(false);
              setShowCustomDialog(false);
              setCustomInstruction('');
              // Update message immediately to replace "Processing with AI..."
              setMessage({
                type: 'success',
                text: 'Text improved successfully!'
              });
            });
            
            // Unlock editing immediately
            if (iframeDoc) {
              unlockEditing(iframeDoc);
            }
            logStep('UI_UPDATE: UI state updated (flushSync completed)');
            
            // Clear success message after 10 seconds (with fade-out animation)
            setTimeout(() => setMessage(null), 10000);
            
            logStep('SYNC: Scheduling background sync');
            // Sync in background using requestAnimationFrame for smooth update
            // This happens after UI state is already updated
            requestAnimationFrame(() => {
              const syncStart = performance.now();
              if (iframeDoc) {
                syncIframeDocumentToState(iframeDoc);
                const syncEnd = performance.now();
                console.log(`[AI Action Perf] SYNC: Background sync completed | Duration: ${(syncEnd - syncStart).toFixed(2)}ms`);
              }
            });
            
            // Log final summary
            const endTime = performance.now();
            const totalTime = endTime - startTime;
            console.log(`[AI Action Perf] ===== SUMMARY =====`);
            console.log(`[AI Action Perf] Total time: ${totalTime.toFixed(2)}ms (${(totalTime / 1000).toFixed(2)}s)`);
            perfLog.forEach((log, idx) => {
              const prevTime = idx > 0 ? perfLog[idx - 1].timestamp : startTime;
              const stepDuration = log.timestamp - prevTime;
              console.log(`[AI Action Perf] ${log.step} | Step duration: ${stepDuration.toFixed(2)}ms | Cumulative: ${log.elapsed.toFixed(2)}ms`);
            });
            console.log(`[AI Action Perf] ===================`);
          } catch (e) {
            console.warn('[AI Assist] Error in replacement, trying outerHTML fallback');
            // Fallback to outerHTML
            try {
              placeholderRef.outerHTML = improvedHtml;
              
              // Update UI state immediately - force immediate render
              setSelectedText('');
              selectedRangeRef.current = null;
              
              // Use flushSync to force immediate React render
              flushSync(() => {
                setAssisting(false);
                setShowCustomDialog(false);
                setCustomInstruction('');
                // Update message immediately to replace "Processing with AI..."
                setMessage({
                  type: 'success',
                  text: 'Text improved successfully!'
                });
              });
              
              // Unlock editing immediately
              if (iframeDoc) {
                unlockEditing(iframeDoc);
              }
              
              // Clear success message after 3 seconds
              setTimeout(() => setMessage(null), 3000);
              
              // Sync immediately after fallback
              requestAnimationFrame(() => {
                if (iframeDoc) {
                  syncIframeDocumentToState(iframeDoc);
                }
              });
            } catch (e2) {
              console.error('[AI Assist] Failed to replace placeholder:', e2);
              throw new Error('Failed to replace placeholder with improved text');
            }
          }
        } else {
          console.error('[AI Assist] Placeholder element is not available');
          throw new Error('Placeholder element is not available');
        }
      } else if (iframeDoc) {
        const applied = applyImprovedHtmlLegacy(
          iframeDoc,
          legacyRange,
          improvedHtml,
          selectedTextSnapshot,
          selectionHtmlSnapshot || selectedTextSnapshot
        );

        if (!applied) {
          throw new Error('Failed to apply improved text. Please try selecting a smaller portion.');
        }
        
        // Update UI state immediately - force immediate render
        setSelectedText('');
        selectedRangeRef.current = null;
        
        // Use flushSync to force immediate React render
        flushSync(() => {
          setAssisting(false);
          setShowCustomDialog(false);
          setCustomInstruction('');
          // Update message immediately to replace "Processing with AI..."
          setMessage({
            type: 'success',
            text: 'Text improved successfully!'
          });
        });
        
        // Unlock editing immediately
        if (iframeDoc) {
          unlockEditing(iframeDoc);
        }
        
        // Clear success message after 3 seconds
        setTimeout(() => setMessage(null), 3000);
        
        // Sync immediately after applying
        if (iframeDoc) {
          requestAnimationFrame(() => {
            if (iframeDoc) {
              syncIframeDocumentToState(iframeDoc);
            }
          });
        }
      } else {
        // Fallback: sync iframe if it exists
        if (iframeDoc) {
          requestAnimationFrame(() => {
            if (iframeDoc) {
              syncIframeDocumentToState(iframeDoc);
            }
          });
        }
      }
    } catch (err: any) {
      console.error('[AI Assist] AI assist error:', err);
      
      // Remove highlight on error
      if (iframeDoc) {
        try {
          const highlights = iframeDoc.querySelectorAll('.ai-processing-highlight');
          highlights.forEach(highlight => {
            const parent = highlight.parentNode;
            if (parent) {
              parent.replaceChild(document.createTextNode(highlight.textContent || ''), highlight);
              parent.normalize();
            }
          });
        } catch (e) {
          console.warn('Failed to remove highlight on error:', e);
        }
      }
      
      // Restore original content on error
      if (placeholder && selectionHtmlSnapshot) {
        try {
          placeholder.outerHTML = selectionHtmlSnapshot;
        } catch (restoreError) {
          console.error('Failed to restore original content:', restoreError);
        }
      }
      
      // Provide user-friendly error messages
      let errorMessage = 'Failed to assist with CV';
      if (err.message) {
        if (err.message.includes('timeout') || err.message.includes('timed out')) {
          errorMessage = 'Request timed out. The AI service may be slow. Please try again or select a smaller portion.';
        } else if (err.message.includes('cancelled') || err.message.includes('aborted')) {
          errorMessage = 'Request was cancelled.';
        } else if (err.message.includes('network') || err.message.includes('fetch')) {
          errorMessage = 'Network error. Please check your connection and try again.';
        } else {
          errorMessage = err.message;
        }
      } else if (err.response?.data?.detail) {
        errorMessage = err.response.data.detail;
      }
      
      setMessage({
        type: 'error',
        text: errorMessage
      });
      setTimeout(() => setMessage(null), 7000);
    } finally {
      // Cleanup - only if not already done (in case of early success)
      // These are idempotent, so safe to call multiple times
      if (iframeDoc) {
        unlockEditing(iframeDoc);
      }
      // Only update if still in processing state (handles error cases)
      // Success cases already cleared these states above
      setAssisting(false);
      setShowCustomDialog(false);
      setCustomInstruction('');
    }
  };

  const handleCustomInstruction = () => {
    if (!customInstruction.trim()) {
      setMessage({
        type: 'error',
        text: 'Please enter an instruction'
      });
      setTimeout(() => setMessage(null), 3000);
      return;
    }
    handleAIAssist('custom', customInstruction);
  };

  const handleAIWrite = async () => {
    if (!aiWriteInstruction.trim()) {
      setMessage({
        type: 'error',
        text: 'Please enter what you want to write'
      });
      setTimeout(() => setMessage(null), 3000);
      return;
    }

    if (editMode !== 'visual') {
      setMessage({
        type: 'error',
        text: 'AI Write is only available in Visual mode'
      });
      setTimeout(() => setMessage(null), 3000);
      return;
    }

    if (!iframeRef.current) {
      setMessage({
        type: 'error',
        text: 'Editor is not ready yet'
      });
      setTimeout(() => setMessage(null), 3000);
      return;
    }

    const iframe = iframeRef.current;
    const iframeDoc = iframe.contentDocument || iframe.contentWindow?.document || null;

    if (!iframeDoc) {
      setMessage({
        type: 'error',
        text: 'Unable to access document'
      });
      setTimeout(() => setMessage(null), 3000);
      return;
    }

    setAssisting(true);
    setShowAIWriteDialog(false);
    setMessage({
      type: 'success',
      text: 'Generating content with AI...'
    });

    try {
      // Get cursor position
      const selection = iframeDoc.getSelection();
      let insertRange: Range | null = null;
      
      if (selection && selection.rangeCount > 0) {
        insertRange = selection.getRangeAt(0).cloneRange();
      } else {
        // If no selection, insert at end of body
        insertRange = iframeDoc.createRange();
        insertRange.selectNodeContents(iframeDoc.body);
        insertRange.collapse(false); // Collapse to end
      }

      // Lock editing
      lockEditing(iframeDoc);

      // Call backend to generate content
      const result = await applicationsAPI.aiAssistCV(
        cvId,
        '', // Empty selection - we're writing new content
        'write', // Special intent for writing new content
        { instruction: aiWriteInstruction },
        60000
      );

      if (!result.success || !result.improved_html) {
        throw new Error(result.error || 'Failed to generate content');
      }

      const generatedHtml = normalizeImprovedHtml(result.improved_html);

      // Insert the generated content at cursor position
      if (insertRange) {
        // Create a temporary container to parse the HTML
        const tempDiv = iframeDoc.createElement('div');
        tempDiv.innerHTML = generatedHtml;
        
        // Insert all nodes from the temp div
        const fragment = iframeDoc.createDocumentFragment();
        while (tempDiv.firstChild) {
          fragment.appendChild(tempDiv.firstChild);
        }
        
        insertRange.insertNode(fragment);
        
        // Move cursor to end of inserted content
        insertRange.collapse(false);
        selection?.removeAllRanges();
        selection?.addRange(insertRange);
      }

      // Update UI state immediately with flushSync
      flushSync(() => {
        setAssisting(false);
        setAIWriteInstruction('');
        // Update message immediately to replace "Generating content with AI..."
        setMessage({
          type: 'success',
          text: 'Content generated successfully!'
        });
      });

      unlockEditing(iframeDoc);

      // Clear success message after 10 seconds (with fade-out animation)
      setTimeout(() => setMessage(null), 10000);

      // Sync iframe to state
      requestAnimationFrame(() => {
        if (iframeDoc) {
          syncIframeDocumentToState(iframeDoc);
        }
      });
    } catch (err: any) {
      console.error('[AI Write] Error:', err);
      unlockEditing(iframeDoc);
      
      let errorMessage = 'Failed to generate content';
      if (err.message) {
        if (err.message.includes('timeout')) {
          errorMessage = 'Request timed out. Please try again.';
        } else if (err.message.includes('network')) {
          errorMessage = 'Network error. Please check your connection.';
        } else {
          errorMessage = err.message;
        }
      }
      
      setMessage({
        type: 'error',
        text: errorMessage
      });
      setTimeout(() => setMessage(null), 7000);
      setAssisting(false);
    }
  };

  // Execute formatting commands in iframe
  const executeCommand = (command: string, showUI: boolean = false, value: string | null = null) => {
    if (!iframeRef.current || editMode !== 'visual') return;
    
    const iframe = iframeRef.current;
    const iframeDoc = iframe.contentDocument || iframe.contentWindow?.document || null;
    
    if (iframeDoc) {
      // Focus the iframe first
      iframe.focus();
      iframeDoc.body.focus();
      
      // Get current selection
      const selection = iframeDoc.getSelection();
      
      // If no selection, try to select the word at cursor
      if (selection && selection.rangeCount === 0) {
        const range = iframeDoc.createRange();
        const walker = iframeDoc.createTreeWalker(
          iframeDoc.body,
          NodeFilter.SHOW_TEXT,
          null
        );
        
        let node = walker.nextNode();
        if (node) {
          range.setStart(node, 0);
          range.setEnd(node, node.textContent?.length || 0);
          selection.removeAllRanges();
          selection.addRange(range);
        }
      }
      
      try {
        // Handle fontSize specially - use inline styles instead of deprecated font tag
        if (command === 'fontSize' && value !== null) {
          if (selection && selection.rangeCount > 0) {
            const range = selection.getRangeAt(0);
            
            // Map execCommand font size values to actual pixel sizes
            const sizeMap: { [key: string]: string } = {
              '1': '8px',
              '2': '10px',
              '3': '12px',
              '4': '14px',
              '5': '18px',
              '6': '24px',
              '7': '36px'
            };
            
            const fontSize = sizeMap[value] || '12px';
            
            // Create a span with the font size style
            const span = iframeDoc.createElement('span');
            span.style.fontSize = fontSize;
            
            try {
              if (range.collapsed) {
                // If no selection, insert at cursor
                range.insertNode(span);
                span.appendChild(iframeDoc.createTextNode('\u200B')); // Zero-width space
                range.setStartAfter(span);
                range.collapse(true);
                selection.removeAllRanges();
                selection.addRange(range);
              } else {
                // Wrap the selection with the span
                range.surroundContents(span);
              }
            } catch (err) {
              // If surroundContents fails, extract and wrap
              const contents = range.extractContents();
              span.appendChild(contents);
              range.insertNode(span);
            }
            // Update font size state immediately
            setCurrentFontSize(value);
          }
        } else if (value !== null) {
          iframeDoc.execCommand(command, showUI, value);
        } else {
          iframeDoc.execCommand(command, showUI);
        }
        
        // Trigger input event to save changes
        const inputEvent = new Event('input', { bubbles: true });
        iframeDoc.body.dispatchEvent(inputEvent);
      } catch (err) {
        console.error('Error executing command:', err);
      }
    }
  };

  // Check if formatting is active (uses formatUpdateTrigger to force re-evaluation)
  const isFormatActive = (command: string): boolean => {
    // Use formatUpdateTrigger to force re-evaluation when selection changes
    if (formatUpdateTrigger >= 0) {
      // This will be evaluated on each render
    }
    
    if (!iframeRef.current || editMode !== 'visual') return false;
    
    const iframe = iframeRef.current;
    const iframeDoc = iframe.contentDocument || iframe.contentWindow?.document || null;
    
    if (iframeDoc) {
      try {
        return iframeDoc.queryCommandState(command);
      } catch {
        return false;
      }
    }
    return false;
  };

  // Copy formatting from selected text
  const copyFormat = () => {
    if (!iframeRef.current || editMode !== 'visual') return;
    
    const iframe = iframeRef.current;
    const iframeDoc = iframe.contentDocument || iframe.contentWindow?.document || null;
    
    if (iframeDoc) {
      const selection = iframeDoc.getSelection();
      if (selection && selection.rangeCount > 0) {
        const range = selection.getRangeAt(0);
        
        // Get the element that contains the selection
        let element: HTMLElement | null = null;
        const container = range.commonAncestorContainer;
        
        // If container is a text node, get its parent
        if (container.nodeType === Node.TEXT_NODE && container.parentElement) {
          element = container.parentElement as HTMLElement;
        } 
        // If container is an element node, use it directly
        else if (container.nodeType === Node.ELEMENT_NODE) {
          element = container as HTMLElement;
        }
        
        // Walk up the DOM tree to find a block-level or inline element
        // Stop at body or when we find a meaningful formatting container
        while (element && element !== iframeDoc.body) {
          const tagName = element.tagName.toLowerCase();
          // Stop at meaningful elements (not just generic containers)
          if (tagName !== 'html' && tagName !== 'head') {
            break;
          }
          element = element.parentElement;
        }
        
        // If we still don't have a good element, try to get from startContainer
        if (!element || element === iframeDoc.body) {
          const startContainer = range.startContainer;
          if (startContainer.nodeType === Node.TEXT_NODE && startContainer.parentElement) {
            element = startContainer.parentElement as HTMLElement;
          } else if (startContainer.nodeType === Node.ELEMENT_NODE) {
            element = startContainer as HTMLElement;
          }
        }
        
        // Always try to get computed styles, even from body (which has default formatting)
        if (element) {
          const computedStyles = iframeDoc.defaultView?.getComputedStyle(element) || null;
          if (computedStyles) {
            setCopiedFormat({
              styles: computedStyles,
              element: element
            });
            setMessage({ type: 'success', text: 'Format copied' });
            setTimeout(() => setMessage(null), 2000);
          } else {
            setMessage({ type: 'error', text: 'Unable to copy format' });
            setTimeout(() => setMessage(null), 2000);
          }
        } else {
          setMessage({ type: 'error', text: 'Please select text to copy format' });
          setTimeout(() => setMessage(null), 2000);
        }
      } else {
        setMessage({ type: 'error', text: 'Please select text to copy format' });
        setTimeout(() => setMessage(null), 2000);
      }
    }
  };

  // Paste formatting to selected text
  const pasteFormat = () => {
    if (!iframeRef.current || editMode !== 'visual' || !copiedFormat) {
      if (!copiedFormat) {
        setMessage({ type: 'error', text: 'No format copied. Select text and copy format first.' });
        setTimeout(() => setMessage(null), 2000);
      }
      return;
    }
    
    const iframe = iframeRef.current;
    const iframeDoc = iframe.contentDocument || iframe.contentWindow?.document || null;
    
    if (iframeDoc) {
      const selection = iframeDoc.getSelection();
      if (selection && selection.rangeCount > 0) {
        // Focus the iframe first
        iframe.focus();
        iframeDoc.body.focus();
        
        // Apply formatting using execCommand for better compatibility
        const styles = copiedFormat.styles;
        
        // Apply font weight (bold)
        if (styles.fontWeight && (styles.fontWeight === 'bold' || parseInt(styles.fontWeight) >= 600)) {
          iframeDoc.execCommand('bold', false);
        }
        
        // Apply font style (italic)
        if (styles.fontStyle === 'italic') {
          iframeDoc.execCommand('italic', false);
        }
        
        // Apply underline
        if (styles.textDecoration && styles.textDecoration.includes('underline')) {
          iframeDoc.execCommand('underline', false);
        }
        
        // Apply text color
        if (styles.color && styles.color !== 'rgb(0, 0, 0)') {
          iframeDoc.execCommand('foreColor', false, styles.color);
        }
        
        // Apply background color (highlight)
        if (styles.backgroundColor && styles.backgroundColor !== 'rgba(0, 0, 0, 0)' && styles.backgroundColor !== 'transparent') {
          iframeDoc.execCommand('backColor', false, styles.backgroundColor);
        }
        
        // Apply font size
        if (styles.fontSize) {
          // Convert font size to execCommand format (1-7)
          const fontSize = parseFloat(styles.fontSize);
          let sizeValue = '3'; // default
          if (fontSize <= 10) sizeValue = '1';
          else if (fontSize <= 12) sizeValue = '2';
          else if (fontSize <= 14) sizeValue = '3';
          else if (fontSize <= 18) sizeValue = '4';
          else if (fontSize <= 24) sizeValue = '5';
          else if (fontSize <= 36) sizeValue = '6';
          else sizeValue = '7';
          iframeDoc.execCommand('fontSize', false, sizeValue);
        }
        
        // Apply font family if different from default
        if (styles.fontFamily && styles.fontFamily !== 'serif' && styles.fontFamily !== 'sans-serif') {
          iframeDoc.execCommand('fontName', false, styles.fontFamily.split(',')[0].replace(/['"]/g, '').trim());
        }
        
        // Trigger input event to save changes
        const inputEvent = new Event('input', { bubbles: true });
        iframeDoc.body.dispatchEvent(inputEvent);
        
        setMessage({ type: 'success', text: 'Format pasted' });
        setTimeout(() => setMessage(null), 2000);
      } else {
        setMessage({ type: 'error', text: 'Please select text to paste format' });
        setTimeout(() => setMessage(null), 2000);
      }
    }
  };

  useEffect(() => {
    if (!isPreview) {
      return;
    }

    const iframe = previewIframeRef.current;
    if (!iframe) {
      return;
    }

    let cleanup: (() => void) | undefined;

    const setupPreview = () => {
      cleanup?.();
      cleanup = initializePreviewIframe(iframe);
    };

    iframe.addEventListener('load', setupPreview);

    if (iframe.contentDocument && iframe.contentDocument.readyState === 'complete') {
      setupPreview();
    }

    return () => {
      iframe.removeEventListener('load', setupPreview);
      if (cleanup) {
        cleanup();
      }
    };
  }, [isPreview, htmlContent]);

  const aiIntents = [
    { key: 'improve_tone', label: 'Improve Tone', icon: Sparkles },
    { key: 'shorten', label: 'Shorten', icon: X },
    { key: 'clarify', label: 'Clarify', icon: Edit },
    { key: 'professionalize', label: 'Professionalize', icon: Wand2 }
  ];


  return (
    <div className="flex flex-col h-full bg-gray-50">
      {/* Full Screen Loader for Regenerate CV */}
      {regenerating && (
        <FullScreenLoader 
          type="cv" 
          message="Regenerating your tailored CV..." 
          agentSteps={agentSteps}
          currentStep={currentStep}
        />
      )}
      
      {/* Header */}
      <div className="bg-white border-b border-gray-200 p-4 flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-gray-900">Edit & Polish CV</h2>
          <p className="text-sm text-gray-600">{jobTitle} at {company}</p>
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        )}
      </div>

      {/* Toolbar */}
      <div className="bg-white border-b border-gray-200">
        {/* First Row: Preview, Mode Toggle, AI Actions, Validate, Refine, Save */}
        <div className="p-3 flex items-center gap-2 flex-nowrap overflow-x-auto">
          <button
            onClick={() => setIsPreview(!isPreview)}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium transition flex-shrink-0 whitespace-nowrap ${
              isPreview
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            {isPreview ? <Edit className="h-4 w-4 inline mr-1" /> : <Eye className="h-4 w-4 inline mr-1" />}
            {isPreview ? 'Edit' : 'Preview'}
          </button>

          {isPreview ? (
            <>
              <div className="h-6 w-px bg-gray-300 flex-shrink-0" />
              <span className="text-sm text-gray-600 flex-shrink-0">Export current preview:</span>
              <button
                onClick={() => handlePreviewDownload('html')}
                disabled={downloadingPreview !== null}
                className="px-3 py-1.5 rounded-lg text-sm font-medium bg-gray-100 text-gray-700 hover:bg-gray-200 disabled:opacity-60 disabled:cursor-not-allowed flex items-center gap-1 whitespace-nowrap flex-shrink-0"
              >
                {downloadingPreview === 'html' ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <FileText className="h-4 w-4" />
                )}
                Save HTML
              </button>
              <button
                onClick={() => handlePreviewDownload('pdf')}
                disabled={downloadingPreview !== null}
                className="px-3 py-1.5 rounded-lg text-sm font-medium bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-60 disabled:cursor-not-allowed flex items-center gap-1 whitespace-nowrap flex-shrink-0"
              >
                {downloadingPreview === 'pdf' ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Download className="h-4 w-4" />
                )}
                Save PDF
              </button>
            </>
          ) : (
            <>
              <div className="h-6 w-px bg-gray-300 flex-shrink-0" />

              <button
                onClick={() => {
                  const modes: Array<'visual' | 'html' | 'css'> = ['visual', 'html', 'css'];
                  const currentIndex = modes.indexOf(editMode);
                  const nextIndex = (currentIndex + 1) % modes.length;
                  setEditMode(modes[nextIndex]);
                }}
                className={`px-3 py-1.5 rounded-lg text-sm font-medium transition flex-shrink-0 ${
                  editMode !== 'visual'
                    ? 'bg-indigo-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {editMode === 'visual' ? (
                  <>
                    <Code className="h-4 w-4 inline mr-1" />
                    HTML/CSS
                  </>
                ) : editMode === 'html' ? (
                  <>
                    <Code className="h-4 w-4 inline mr-1" />
                    HTML
                  </>
                ) : (
                  <>
                    <Palette className="h-4 w-4 inline mr-1" />
                    CSS
                  </>
                )}
              </button>

              {editMode === 'visual' && isEditorFocused && (
                <>
                  <div className="h-6 w-px bg-gray-300 flex-shrink-0" />
                  <button
                    onClick={() => setShowAIWriteDialog(true)}
                    disabled={assisting}
                    className="px-3 py-1.5 rounded-lg text-sm font-medium bg-blue-100 text-blue-700 hover:bg-blue-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1 whitespace-nowrap flex-shrink-0"
                  >
                    {assisting ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Sparkles className="h-4 w-4" />
                    )}
                    AI Write
                  </button>
                  {selectedText && (
                    <>
                      <div className="h-6 w-px bg-gray-300 flex-shrink-0" />
                      <span className="text-sm text-gray-600 whitespace-nowrap flex-shrink-0">AI Actions:</span>
                      <div className="flex items-center gap-2 flex-nowrap flex-shrink-0">
                        {aiIntents.map(({ key, label, icon: Icon }) => (
                          <button
                            key={key}
                            onClick={() => handleAIAssist(key)}
                            disabled={assisting}
                            className="px-3 py-1.5 rounded-lg text-sm font-medium bg-purple-100 text-purple-700 hover:bg-purple-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1 whitespace-nowrap flex-shrink-0"
                          >
                            {assisting ? (
                              <Loader2 className="h-4 w-4 animate-spin" />
                            ) : (
                              <Icon className="h-4 w-4" />
                            )}
                            {label}
                          </button>
                        ))}
                        <button
                          onClick={() => setShowCustomDialog(true)}
                          disabled={assisting}
                          className="px-3 py-1.5 rounded-lg text-sm font-medium bg-indigo-100 text-indigo-700 hover:bg-indigo-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1 whitespace-nowrap flex-shrink-0"
                        >
                          <Settings className="h-4 w-4" />
                          Customize
                        </button>
                      </div>
                    </>
                  )}
                  <div className="h-6 w-px bg-gray-300 flex-shrink-0" />
                </>
              )}

              <button
                onClick={handleRefine}
                disabled={refining}
                className="px-3 py-1.5 rounded-lg text-sm font-medium bg-orange-100 text-orange-700 hover:bg-orange-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1 whitespace-nowrap flex-shrink-0"
              >
                {refining ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <RefreshCw className="h-4 w-4" />
                )}
                Refine CV
              </button>

              {jobId && (
                <>
                  <div className="h-6 w-px bg-gray-300 flex-shrink-0" />
                  <button
                    onClick={() => setShowRegenerateConfirm(true)}
                    disabled={regenerating}
                    className="px-3 py-1.5 rounded-lg text-sm font-medium bg-red-100 text-red-700 hover:bg-red-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1 whitespace-nowrap flex-shrink-0"
                  >
                    {regenerating ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <RefreshCw className="h-4 w-4" />
                    )}
                    Regenerate CV
                  </button>
                </>
              )}

              <div className="h-6 w-px bg-gray-300 flex-shrink-0" />

              <button
                onClick={handleValidate}
                disabled={validating}
                className="px-3 py-1.5 rounded-lg text-sm font-medium bg-green-100 text-green-700 hover:bg-green-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1 whitespace-nowrap flex-shrink-0"
              >
                {validating ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <CheckCircle2 className="h-4 w-4" />
                )}
                Validate
              </button>
            </>
          )}
        </div>
        
        {/* Second Row: Formatting Toolbar (only in visual mode) */}
        {editMode === 'visual' && (
          <div className="px-3 pb-3 flex items-center gap-2 flex-wrap border-t border-gray-100">
            <span className="text-sm text-gray-600">Format:</span>
            
            {/* Text Style */}
            <button
              onClick={() => executeCommand('bold')}
              className={`p-2 rounded transition-colors ${
                isFormatActive('bold') 
                  ? 'bg-blue-100 text-blue-700' 
                  : 'hover:bg-gray-100'
              }`}
              title="Bold (Ctrl+B)"
            >
              <Bold className="h-4 w-4" />
            </button>
            
            <button
              onClick={() => executeCommand('italic')}
              className={`p-2 rounded transition-colors ${
                isFormatActive('italic') 
                  ? 'bg-blue-100 text-blue-700' 
                  : 'hover:bg-gray-100'
              }`}
              title="Italic (Ctrl+I)"
            >
              <Italic className="h-4 w-4" />
            </button>
            
            <button
              onClick={() => executeCommand('underline')}
              className={`p-2 rounded transition-colors ${
                isFormatActive('underline') 
                  ? 'bg-blue-100 text-blue-700' 
                  : 'hover:bg-gray-100'
              }`}
              title="Underline (Ctrl+U)"
            >
              <Underline className="h-4 w-4" />
            </button>
            
            <div className="h-6 w-px bg-gray-300" />
            
            {/* Lists */}
            <button
              onClick={() => executeCommand('insertUnorderedList')}
              className="p-2 rounded hover:bg-gray-100 transition-colors"
              title="Bullet List"
            >
              <List className="h-4 w-4" />
            </button>
            
            <button
              onClick={() => executeCommand('insertOrderedList')}
              className="p-2 rounded hover:bg-gray-100 transition-colors"
              title="Numbered List"
            >
              <ListOrdered className="h-4 w-4" />
            </button>
            
            <div className="h-6 w-px bg-gray-300" />
            
            {/* Alignment */}
            <button
              onClick={() => executeCommand('justifyLeft')}
              className={`p-2 rounded transition-colors ${
                isFormatActive('justifyLeft') 
                  ? 'bg-blue-100 text-blue-700' 
                  : 'hover:bg-gray-100'
              }`}
              title="Align Left"
            >
              <AlignLeft className="h-4 w-4" />
            </button>
            
            <button
              onClick={() => executeCommand('justifyCenter')}
              className={`p-2 rounded transition-colors ${
                isFormatActive('justifyCenter') 
                  ? 'bg-blue-100 text-blue-700' 
                  : 'hover:bg-gray-100'
              }`}
              title="Align Center"
            >
              <AlignCenter className="h-4 w-4" />
            </button>
            
            <button
              onClick={() => executeCommand('justifyRight')}
              className={`p-2 rounded transition-colors ${
                isFormatActive('justifyRight') 
                  ? 'bg-blue-100 text-blue-700' 
                  : 'hover:bg-gray-100'
              }`}
              title="Align Right"
            >
              <AlignRight className="h-4 w-4" />
            </button>
            
            <div className="h-6 w-px bg-gray-300" />
            
            {/* Font Size */}
            <div className="flex items-center gap-1 border border-gray-300 rounded px-2 py-1">
              <Type className="h-4 w-4 text-gray-600" />
              <select
                value={currentFontSize}
                onChange={(e) => {
                  setCurrentFontSize(e.target.value);
                  executeCommand('fontSize', false, e.target.value);
                }}
                className="text-sm border-0 outline-none bg-transparent cursor-pointer"
              >
                <option value="1">8pt</option>
                <option value="2">10pt</option>
                <option value="3">12pt</option>
                <option value="4">14pt</option>
                <option value="5">18pt</option>
                <option value="6">24pt</option>
                <option value="7">36pt</option>
              </select>
            </div>
            
            {/* Text Color */}
            <div className="flex items-center gap-1">
              <Palette className="h-4 w-4 text-gray-600" />
              <input
                type="color"
                onChange={(e) => executeCommand('foreColor', false, e.target.value)}
                className="w-8 h-8 border border-gray-300 rounded cursor-pointer"
                defaultValue="#000000"
                title="Text Color"
              />
            </div>
            
            {/* Highlight Color */}
            <div className="flex items-center gap-1">
              <Highlighter className="h-4 w-4 text-gray-600" />
              <input
                type="color"
                onChange={(e) => executeCommand('backColor', false, e.target.value)}
                className="w-8 h-8 border border-gray-300 rounded cursor-pointer"
                defaultValue="#ffff00"
                title="Highlight Color"
              />
            </div>
            
            <div className="h-6 w-px bg-gray-300" />
            
            {/* Link */}
            <button
              onClick={() => {
                const url = prompt('Enter URL:');
                if (url) {
                  executeCommand('createLink', false, url);
                }
              }}
              className="p-2 rounded hover:bg-gray-100 transition-colors"
              title="Insert Link"
            >
              <Link className="h-4 w-4" />
            </button>
            
            <button
              onClick={() => executeCommand('unlink')}
              className="p-2 rounded hover:bg-gray-100 transition-colors"
              title="Remove Link"
            >
              <Link className="h-4 w-4" style={{ transform: 'rotate(45deg)' }} />
            </button>
            
            <div className="h-6 w-px bg-gray-300" />
            
            {/* Undo/Redo */}
            <button
              onClick={() => executeCommand('undo')}
              className="p-2 rounded hover:bg-gray-100 transition-colors"
              title="Undo (Ctrl+Z)"
            >
              <Undo className="h-4 w-4" />
            </button>
            
            <button
              onClick={() => executeCommand('redo')}
              className="p-2 rounded hover:bg-gray-100 transition-colors"
              title="Redo (Ctrl+Y)"
            >
              <Redo className="h-4 w-4" />
            </button>
            
            <div className="h-6 w-px bg-gray-300" />
            
            {/* Clear Formatting */}
            <button
              onClick={() => executeCommand('removeFormat')}
              className="p-2 rounded hover:bg-gray-100 transition-colors"
              title="Clear Formatting"
            >
              <Eraser className="h-4 w-4" />
            </button>
            
            <div className="h-6 w-px bg-gray-300" />
            
            {/* Format Copier */}
            <button
              onClick={copyFormat}
              className={`p-2 rounded transition-colors ${
                copiedFormat 
                  ? 'bg-green-100 text-green-700 hover:bg-green-200' 
                  : 'hover:bg-gray-100'
              }`}
              title="Copy Format"
            >
              <Copy className="h-4 w-4" />
            </button>
            
            <button
              onClick={pasteFormat}
              className={`p-2 rounded transition-colors ${
                copiedFormat 
                  ? 'hover:bg-blue-100 text-blue-700' 
                  : 'hover:bg-gray-100 opacity-50 cursor-not-allowed'
              }`}
              title={copiedFormat ? "Paste Format" : "Paste Format (No format copied)"}
              disabled={!copiedFormat}
            >
              <ClipboardCheck className="h-4 w-4" />
            </button>
            
            <div className="flex-1" />
            
            <div className="h-6 w-px bg-gray-300" />
            
            <button
              onClick={() => handleSave('draft')}
              disabled={saving}
              className="px-4 py-1.5 rounded-lg text-sm font-medium bg-gray-600 text-white hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1 whitespace-nowrap flex-shrink-0"
            >
              {saving ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Save className="h-4 w-4" />
              )}
              Save Draft
            </button>

            <button
              onClick={() => handleSave('final')}
              disabled={saving}
              className="px-4 py-1.5 rounded-lg text-sm font-medium bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1 whitespace-nowrap flex-shrink-0"
            >
              {saving ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <CheckCircle2 className="h-4 w-4" />
              )}
              Save Final
            </button>
          </div>
        )}
      </div>

      {/* AI Processing Badge - Floating on top of editor */}
      {assisting && (
        <div className="fixed top-24 left-1/2 transform -translate-x-1/2 z-50 pointer-events-none">
          <div className="relative inline-flex items-center gap-3 px-6 py-3 bg-gradient-to-r from-purple-600 via-indigo-600 to-blue-600 rounded-full shadow-lg animate-pulse">
            {/* Animated sparkles */}
            <div className="absolute inset-0 rounded-full bg-gradient-to-r from-purple-400 via-indigo-400 to-blue-400 opacity-50 animate-ping"></div>
            
            {/* Spinning loader */}
            <Loader2 className="h-5 w-5 text-white animate-spin relative z-10" />
            
            {/* Text */}
            <span className="text-white font-semibold text-sm relative z-10 flex items-center gap-2">
              <Sparkles className="h-4 w-4 animate-pulse" />
              AI Processing...
            </span>
            
            {/* Glowing effect */}
            <div className="absolute inset-0 rounded-full bg-gradient-to-r from-purple-400/20 via-indigo-400/20 to-blue-400/20 blur-xl"></div>
          </div>
        </div>
      )}

      {/* Success Badge - Floating on top of editor */}
      {message && !assisting && message.type === 'success' && (
        <div className="fixed top-24 left-1/2 transform -translate-x-1/2 z-50 pointer-events-none">
          <div className="relative inline-flex items-center gap-3 px-6 py-3 bg-gradient-to-r from-green-500 via-emerald-500 to-teal-500 rounded-full shadow-lg animate-fade-out">
            {/* Animated sparkles */}
            <div className="absolute inset-0 rounded-full bg-gradient-to-r from-green-400 via-emerald-400 to-teal-400 opacity-30 animate-ping"></div>
            
            {/* Success icon */}
            <CheckCircle2 className="h-5 w-5 text-white relative z-10" />
            
            {/* Text */}
            <span className="text-white font-semibold text-sm relative z-10 flex items-center gap-2">
              <Sparkles className="h-4 w-4" />
              {message.text}
            </span>
            
            {/* Glowing effect */}
            <div className="absolute inset-0 rounded-full bg-gradient-to-r from-green-400/20 via-emerald-400/20 to-teal-400/20 blur-xl"></div>
          </div>
        </div>
      )}

      {/* Error Messages (keep as bar for errors) */}
      {message && !assisting && message.type === 'error' && !validationResult && (
        <div className="mx-4 mt-4 p-3 rounded-lg border bg-red-50 border-red-200 text-red-800">
          {message.text}
        </div>
      )}

      {/* Editor/Preview and Validation Results - Side by Side */}
      <div className="flex-1 overflow-hidden flex">
        {/* Editor/Preview */}
        <div className="flex-1 overflow-hidden flex justify-center">
        {isPreview ? (
          <div className="flex-1 flex flex-col bg-white overflow-hidden">
            <div className="flex-1 overflow-y-auto bg-gray-100 flex items-start justify-center p-4">
              <iframe
                ref={previewIframeRef}
                srcDoc={htmlContent}
                className="border-0 rounded"
                style={{
                  width: 'calc(210mm + 40px)',
                  minHeight: '297mm',
                  background: '#e5e7eb',
                  display: 'block'
                }}
                title="CV Preview"
                sandbox="allow-same-origin allow-scripts"
                scrolling="no"
              />
            </div>
          </div>
        ) : editMode === 'html' ? (
          <div className="flex-1 flex flex-col bg-white">
            <div className="flex-1 p-4">
              <Editor
                height="100%"
                defaultLanguage="html"
                value={htmlContent}
                onChange={handleHtmlChange}
                theme="vs-light"
                options={{
                  minimap: { enabled: false },
                  fontSize: 14,
                  wordWrap: 'on',
                  automaticLayout: true,
                  tabSize: 2,
                  formatOnPaste: true,
                  formatOnType: true,
                }}
              />
            </div>
            <div className="bg-yellow-50 border-t border-yellow-200 p-2 text-sm text-yellow-800">
              <strong>HTML Mode:</strong> Edit the raw HTML directly. All formatting and styles are preserved. Switch to Visual mode for easier text editing, or CSS mode to edit styles separately.
            </div>
          </div>
        ) : editMode === 'css' ? (
          <div className="flex-1 flex flex-col bg-white">
            <div className="flex-1 p-4">
              <Editor
                height="100%"
                defaultLanguage="css"
                value={cssContent}
                onChange={handleCssChange}
                theme="vs-light"
                options={{
                  minimap: { enabled: false },
                  fontSize: 14,
                  wordWrap: 'on',
                  automaticLayout: true,
                  tabSize: 2,
                  formatOnPaste: true,
                  formatOnType: true,
                }}
              />
            </div>
            <div className="bg-blue-50 border-t border-blue-200 p-2 text-sm text-blue-800">
              <strong>CSS Mode:</strong> Edit CSS styles directly. Changes are applied immediately to the preview. Use HTML mode to edit content structure, or Visual mode for text editing.
            </div>
          </div>
        ) : (
          <div className="flex-1 flex flex-col bg-white overflow-hidden">
            {/* Scrollable editor area with external scrollbar */}
            <div className="flex-1 overflow-y-auto overflow-x-hidden bg-gray-50 flex items-start justify-center p-4">
              <iframe
                ref={iframeRef}
                className="border-0"
                style={{ 
                  width: 'calc(210mm + 40px)',
                  minHeight: '297mm',
                  height: 'auto',
                  background: '#e5e7eb',
                  display: 'block',
                  margin: '0 auto'
                }}
                title="CV Visual Editor"
                sandbox="allow-same-origin allow-scripts"
                scrolling="no"
              />
            </div>
          </div>
        )}
        </div>

        {/* Validation Results Panel - Side by Side */}
        {validationResult && (
          <div className="w-96 border-l border-gray-200 bg-white flex flex-col flex-shrink-0">
            <div className="flex items-center justify-between p-4 bg-blue-50 border-b border-blue-200">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-5 w-5 text-blue-600" />
                <h3 className="font-semibold text-blue-900">Validation Results</h3>
              </div>
              <button
                onClick={() => setValidationResult(null)}
                className="p-1 hover:bg-blue-100 rounded transition-colors"
                title="Close"
              >
                <X className="h-4 w-4 text-blue-600" />
              </button>
            </div>
            <div className="overflow-y-auto p-4 text-sm text-blue-800 space-y-3">
              <div>
                <p className="font-medium">Quality Score: <span className="text-blue-900 font-bold">{validationResult.quality_score || 0}/10</span></p>
              </div>
              
              {validationResult.quality_feedback && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                  <p className="font-medium text-blue-900 mb-2">Overall Quality Assessment:</p>
                  <p className="text-blue-800 leading-relaxed">{validationResult.quality_feedback}</p>
                </div>
              )}
              
              {validationResult.issues && validationResult.issues.length > 0 && (
                <div>
                  <p className="font-medium mt-2 text-red-700">Issues Found ({validationResult.issues.length}):</p>
                  <ul className="list-disc list-inside ml-2 space-y-1 mt-1">
                    {validationResult.issues.slice(0, 5).map((issue: string, idx: number) => (
                      <li key={idx} className="text-red-600">{issue}</li>
                    ))}
                    {validationResult.issues.length > 5 && (
                      <li className="text-blue-600 italic">... and {validationResult.issues.length - 5} more issue(s)</li>
                    )}
                  </ul>
                </div>
              )}
              
              {validationResult.recommendations && validationResult.recommendations.length > 0 && (
                <div>
                  <p className="font-medium mt-2 text-green-700">Recommendations:</p>
                  <ul className="list-disc list-inside ml-2 space-y-1 mt-1">
                    {validationResult.recommendations.slice(0, 5).map((rec: string, idx: number) => (
                      <li key={idx} className="text-green-600">{rec}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* AI Write Dialog */}
      {showAIWriteDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">AI Write</h3>
              <button
                onClick={() => {
                  setShowAIWriteDialog(false);
                  setAIWriteInstruction('');
                }}
                className="p-1 hover:bg-gray-100 rounded transition-colors"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                What would you like to write?
              </label>
              <textarea
                value={aiWriteInstruction}
                onChange={(e) => setAIWriteInstruction(e.target.value)}
                placeholder="e.g., Write a professional summary for a software engineer, Add a bullet point about leading a team of 5 developers, Write a skills section highlighting Python and React..."
                className="w-full h-32 p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                autoFocus
              />
              <p className="text-xs text-gray-500 mt-2">
                Examples: "Write a professional summary", "Add a bullet point about project management", "Write a skills section"
              </p>
            </div>
            
            <div className="flex items-center justify-end gap-3">
              <button
                onClick={() => {
                  setShowAIWriteDialog(false);
                  setAIWriteInstruction('');
                }}
                className="px-4 py-2 rounded-lg text-sm font-medium bg-gray-100 text-gray-700 hover:bg-gray-200 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleAIWrite}
                disabled={assisting || !aiWriteInstruction.trim()}
                className="px-4 py-2 rounded-lg text-sm font-medium bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 transition-colors"
              >
                {assisting ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>
                    <Sparkles className="h-4 w-4" />
                    Generate
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Custom Instruction Dialog */}
      {showCustomDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Custom AI Instruction</h3>
              <button
                onClick={() => {
                  setShowCustomDialog(false);
                  setCustomInstruction('');
                }}
                className="p-1 hover:bg-gray-100 rounded transition-colors"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            
            <div className="mb-4">
              <p className="text-sm text-gray-600 mb-2">
                Selected text: <span className="font-medium">{selectedText.substring(0, 100)}{selectedText.length > 100 ? '...' : ''}</span>
              </p>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Enter your instruction for improving the selected text:
              </label>
              <textarea
                value={customInstruction}
                onChange={(e) => setCustomInstruction(e.target.value)}
                placeholder="e.g., Make it more technical, Add more action verbs, Emphasize leadership skills, Make it shorter and punchier..."
                className="w-full h-32 p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-none"
                autoFocus
              />
              <p className="text-xs text-gray-500 mt-2">
                Examples: "Make it more concise", "Add quantitative metrics", "Emphasize technical skills", "Use stronger action verbs"
              </p>
            </div>
            
            <div className="flex items-center justify-end gap-3">
              <button
                onClick={() => {
                  setShowCustomDialog(false);
                  setCustomInstruction('');
                }}
                className="px-4 py-2 rounded-lg text-sm font-medium bg-gray-100 text-gray-700 hover:bg-gray-200 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleCustomInstruction}
                disabled={assisting || !customInstruction.trim()}
                className="px-4 py-2 rounded-lg text-sm font-medium bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 transition-colors"
              >
                {assisting ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Processing...
                  </>
                ) : (
                  <>
                    <Wand2 className="h-4 w-4" />
                    Apply
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Regenerate Confirmation Dialog */}
      {showRegenerateConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4 p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Regenerate CV</h3>
              <button
                onClick={() => setShowRegenerateConfirm(false)}
                className="p-1 hover:bg-gray-100 rounded transition-colors"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            
            <div className="mb-6">
              <p className="text-sm text-gray-700 mb-3">
                Are you sure you want to regenerate this CV? This will:
              </p>
              <ul className="list-disc list-inside text-sm text-gray-600 space-y-1 mb-3">
                <li>Remove all your current edits</li>
                <li>Generate a completely fresh CV from scratch</li>
                <li>Replace the current content with the new CV</li>
              </ul>
              <p className="text-sm font-medium text-red-600">
                This action cannot be undone.
              </p>
            </div>
            
            <div className="flex gap-3 justify-end">
              <button
                onClick={() => setShowRegenerateConfirm(false)}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleRegenerate}
                disabled={regenerating}
                className="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
              >
                {regenerating ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Regenerating...
                  </>
                ) : (
                  'Yes, Regenerate CV'
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Status Footer */}
      <div className="bg-white border-t border-gray-200 p-3 flex items-center justify-between text-sm text-gray-600">
        <div className="flex items-center gap-4">
          <span>Status: <strong className={status === 'final' ? 'text-green-600' : 'text-gray-600'}>{status}</strong></span>
          <span>Mode: <strong>{editMode === 'visual' ? 'Visual' : editMode === 'html' ? 'HTML' : 'CSS'}</strong></span>
          <span>Characters: {
            editMode === 'html' ? htmlContent.length : 
            editMode === 'css' ? cssContent.length :
            (htmlContent.length)
          }</span>
        </div>
        <div className="text-xs text-gray-500">
          {editMode === 'visual' 
            ? 'Tip: Select text and use AI actions to improve it, or switch to HTML/CSS mode for precise editing'
            : editMode === 'html'
            ? 'Tip: Edit HTML directly. All styles and formatting are preserved. Use CSS mode to edit styles separately.'
            : 'Tip: Edit CSS styles directly. Changes apply immediately. Use HTML mode for content structure, Visual mode for text editing.'}
        </div>
      </div>
    </div>
  );
};
