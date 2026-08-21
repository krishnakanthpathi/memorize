import React, { useEffect, useState } from 'react';
import * as Dialog from '@radix-ui/react-dialog';
import {
  X,
  Download,
  ChevronLeft,
  ChevronRight,
  Sparkles,
  FileText,
  Copy,
  Check,
  RotateCcw,
  ZoomIn,
  ZoomOut,
  Maximize2,
  Send,
  Loader2,
  ExternalLink,
} from 'lucide-react';
import { useNotesStore } from '@/store/useNotesStore';
import { documentApi, DocumentDetailsResponse, DocumentMetadata } from '@/services/documentApi';

export const DocumentViewerModal: React.FC = () => {
  const {
    activeDocumentViewer,
    setActiveDocumentViewer,
    notes,
    activeNoteId,
    updateActiveNote,
  } = useNotesStore();

  const activeNote = notes.find((n) => n.id === activeNoteId);

  const [docDetails, setDocDetails] = useState<DocumentDetailsResponse | null>(null);

  const [currentPageIndex, setCurrentPageIndex] = useState<number>(0);
  const [isLoadingDoc, setIsLoadingDoc] = useState<boolean>(false);
  const [zoomLevel, setZoomLevel] = useState<number>(1);
  const [copiedText, setCopiedText] = useState<boolean>(false);
  const [insertedToNote, setInsertedToNote] = useState<boolean>(false);

  // Per-page OCR re-run state
  const [isReRunningOcr, setIsReRunningOcr] = useState<boolean>(false);
  const [isExtractingAllPages, setIsExtractingAllPages] = useState<boolean>(false);
  const [customPrompt, setCustomPrompt] = useState<string>('');
  const [showPromptInput, setShowPromptInput] = useState<boolean>(false);
  const [pageOcrOverride, setPageOcrOverride] = useState<Record<number, string>>({});


  const isOpen = activeDocumentViewer !== null;

  useEffect(() => {
    if (!activeDocumentViewer) {
      setDocDetails(null);
      setCurrentPageIndex(0);
      setZoomLevel(1);
      setPageOcrOverride({});
      return;
    }

    const urlFilename = activeDocumentViewer.url
      ? activeDocumentViewer.url.split('?')[0].split('/').pop()
      : '';
    const docIdentifier =
      activeDocumentViewer.docId ||
      urlFilename ||
      activeDocumentViewer.filename ||
      '';


    if (!docIdentifier) return;

    setIsLoadingDoc(true);
    setCurrentPageIndex(activeDocumentViewer.initialPage ? activeDocumentViewer.initialPage - 1 : 0);

    documentApi
      .getDocumentDetails(docIdentifier)
      .then((data) => {
        setDocDetails(data);
      })
      .catch((err) => {
        console.error('Failed to load document details:', err);
      })
      .finally(() => {
        setIsLoadingDoc(false);
      });
  }, [activeDocumentViewer]);

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isOpen || !docDetails || docDetails.pages.length <= 1) return;
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return;

      if (e.key === 'ArrowLeft') {
        e.preventDefault();
        setCurrentPageIndex((prev) => Math.max(0, prev - 1));
      } else if (e.key === 'ArrowRight') {
        e.preventDefault();
        setCurrentPageIndex((prev) => Math.min(docDetails.pages.length - 1, prev + 1));
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, docDetails]);

  if (!isOpen) return null;

  const pages = docDetails?.pages || [];
  const totalPages = pages.length;
  const currentPage = pages[currentPageIndex] || null;
  const originalFilename =
    docDetails?.document.original_filename ||
    activeDocumentViewer.filename ||
    'Document.pdf';
  const downloadUrl =
    docDetails?.document.download_url ||
    (activeDocumentViewer.url ? `/api/media/download/${activeDocumentViewer.url.split('/').pop()}` : '#');

  const currentPageOcr =
    pageOcrOverride[currentPageIndex] !== undefined
      ? pageOcrOverride[currentPageIndex]
      : currentPage?.ocr_text || '';

  const handleCopyOcr = () => {
    if (!currentPageOcr) return;
    navigator.clipboard.writeText(currentPageOcr);
    setCopiedText(true);
    setTimeout(() => setCopiedText(false), 2000);
  };

  const handleInsertPageToNote = () => {
    if (!activeNote || !currentPageOcr) return;
    const insertion = `\n\n### Page ${currentPageIndex + 1}: ${originalFilename}\n${currentPageOcr.trim()}\n`;
    updateActiveNote({ content: (activeNote.content || '') + insertion });
    setInsertedToNote(true);
    setTimeout(() => setInsertedToNote(false), 2000);
  };



  const handleExtractAllPages = async () => {
    const docIdentifier =
      docDetails?.document.id ||
      docDetails?.document.filename ||
      activeDocumentViewer?.filename ||
      '';
    if (!docIdentifier || isExtractingAllPages) return;

    setIsExtractingAllPages(true);
    try {
      const res = await documentApi.triggerDocumentOcr(docIdentifier, customPrompt.trim() || undefined);
      const overrides: Record<number, string> = {};
      res.pages.forEach((p, idx) => {
        overrides[idx] = p.ocr_text;
      });
      setPageOcrOverride(overrides);
      setCustomPrompt('');
      setShowPromptInput(false);
    } catch (err: any) {
      console.error('Failed to extract text for all pages:', err);
    } finally {
      setIsExtractingAllPages(false);
    }
  };

  const handleReRunPageOcr = async () => {
    if (!currentPage || isReRunningOcr) return;
    setIsReRunningOcr(true);
    try {
      const res = await documentApi.reprocessPageOcr(
        currentPage.id || currentPage.filename,
        customPrompt.trim() || undefined
      );
      setPageOcrOverride((prev) => ({
        ...prev,
        [currentPageIndex]: res.ocr_text,
      }));
      setCustomPrompt('');
      setShowPromptInput(false);
    } catch (err: any) {
      console.error('Failed to re-scan page OCR:', err);
    } finally {
      setIsReRunningOcr(false);
    }
  };

  return (
    <Dialog.Root open={isOpen} onOpenChange={(open) => !open && setActiveDocumentViewer(null)}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-background/90 backdrop-blur-md z-50 animate-in fade-in" />
        <Dialog.Content className="fixed inset-4 md:inset-8 bg-card border border-border rounded-2xl shadow-2xl z-50 flex flex-col overflow-hidden focus:outline-none animate-in zoom-in-95 duration-150">
          {/* Header */}
          <div className="flex items-center justify-between px-6 py-3.5 border-b border-border bg-surface/50 backdrop-blur-sm shrink-0">
            <div className="flex items-center gap-3 min-w-0">
              <div className="p-2 rounded-lg bg-red-500/10 text-red-500 border border-red-500/20">
                <FileText className="w-5 h-5" />
              </div>
              <div className="min-w-0">
                <Dialog.Title className="text-sm font-bold text-foreground truncate max-w-md">
                  {originalFilename}
                </Dialog.Title>
                <Dialog.Description className="text-xs text-muted-foreground flex items-center gap-2">
                  <span>
                    {totalPages > 0
                      ? `Page ${currentPageIndex + 1} of ${totalPages}`
                      : 'Loading document...'}
                  </span>
                  {docDetails?.document.file_size && (
                    <span>• {(docDetails.document.file_size / (1024 * 1024)).toFixed(2)} MB</span>
                  )}
                </Dialog.Description>
              </div>
            </div>

            {/* Actions */}
            <div className="flex items-center gap-2">
              <button
                onClick={handleReRunPageOcr}
                disabled={isExtractingAllPages || isReRunningOcr}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 text-xs font-semibold transition-all cursor-pointer shadow-xs disabled:opacity-50"
                title={`Extract text from Page ${currentPageIndex + 1} with local Ollama GLM-OCR`}
              >
                {isReRunningOcr ? (
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <Sparkles className="w-3.5 h-3.5" />
                )}
                <span>
                  {isReRunningOcr
                    ? `Extracting Page ${currentPageIndex + 1}...`
                    : `Extract Page ${currentPageIndex + 1} (GLM-OCR)`}
                </span>
              </button>

              {totalPages > 1 && (
                <button
                  onClick={handleExtractAllPages}
                  disabled={isExtractingAllPages || isReRunningOcr}
                  className="hidden sm:flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-surface-hover hover:bg-surface border border-border text-xs font-semibold text-foreground transition-all cursor-pointer disabled:opacity-50"
                  title="Extract text across all pages"
                >
                  {isExtractingAllPages && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                  <span>{isExtractingAllPages ? 'Extracting All...' : `Extract All (${totalPages} Pages)`}</span>
                </button>
              )}

              <a
                href={downloadUrl}
                download={originalFilename}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-surface-hover hover:bg-surface border border-border text-xs font-semibold text-foreground transition-all"
                title="Download Original PDF"
              >
                <Download className="w-3.5 h-3.5 text-primary" />
                <span className="hidden sm:inline">Download PDF</span>
              </a>

              <button
                onClick={() => setActiveDocumentViewer(null)}
                className="p-1.5 rounded-lg text-muted-foreground hover:text-foreground hover:bg-surface-hover transition-colors cursor-pointer"
                title="Close"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

          </div>


          {/* Main Content Area: Left Page Viewer + Right OCR Drawer */}
          <div className="flex-1 flex overflow-hidden">
            {/* Left: Interactive Page Canvas */}
            <div className="flex-1 flex flex-col bg-background/50 relative overflow-hidden">
              {isLoadingDoc ? (
                <div className="flex-1 flex flex-col items-center justify-center gap-3 text-muted-foreground">
                  <Loader2 className="w-8 h-8 animate-spin text-primary" />
                  <p className="text-sm font-medium">Loading document pages...</p>
                </div>
              ) : currentPage ? (
                <div className="flex-1 overflow-auto flex items-center justify-center p-4">
                  <div
                    style={{ transform: `scale(${zoomLevel})`, transition: 'transform 0.15s ease-out' }}
                    className="origin-center max-h-full flex items-center justify-center"
                  >
                    <img
                      src={currentPage.url}
                      alt={`Page ${currentPageIndex + 1}`}
                      className="max-h-[calc(100vh-220px)] w-auto object-contain rounded-lg shadow-xl border border-border/80 bg-white"
                    />
                  </div>
                </div>
              ) : (
                <div className="flex-1 flex items-center justify-center text-muted-foreground text-sm">
                  No preview available for this document.
                </div>
              )}

              {/* Bottom Floating Control Bar */}
              {totalPages > 0 && (
                <div className="p-3 border-t border-border bg-surface/80 backdrop-blur-md flex items-center justify-between gap-4 shrink-0">
                  {/* Page Switcher */}
                  <div className="flex items-center gap-1.5">
                    <button
                      onClick={() => setCurrentPageIndex((p) => Math.max(0, p - 1))}
                      disabled={currentPageIndex === 0}
                      className="p-1.5 rounded-lg border border-border bg-surface-hover hover:bg-surface disabled:opacity-40 disabled:pointer-events-none transition-colors"
                      title="Previous Page (Left Arrow)"
                    >
                      <ChevronLeft className="w-4 h-4" />
                    </button>
                    <span className="text-xs font-semibold px-2">
                      Page {currentPageIndex + 1} of {totalPages}
                    </span>
                    <button
                      onClick={() => setCurrentPageIndex((p) => Math.min(totalPages - 1, p + 1))}
                      disabled={currentPageIndex >= totalPages - 1}
                      className="p-1.5 rounded-lg border border-border bg-surface-hover hover:bg-surface disabled:opacity-40 disabled:pointer-events-none transition-colors"
                      title="Next Page (Right Arrow)"
                    >
                      <ChevronRight className="w-4 h-4" />
                    </button>
                  </div>

                  {/* Thumbnail Strip */}
                  <div className="hidden md:flex items-center gap-2 overflow-x-auto max-w-md px-2 py-1">
                    {pages.map((p, idx) => (
                      <button
                        key={p.id || idx}
                        onClick={() => setCurrentPageIndex(idx)}
                        className={`relative shrink-0 w-10 h-14 rounded border transition-all overflow-hidden bg-white ${
                          idx === currentPageIndex
                            ? 'border-primary ring-2 ring-primary/30 shadow-md'
                            : 'border-border opacity-60 hover:opacity-100'
                        }`}
                        title={`Jump to Page ${idx + 1}`}
                      >
                        <img src={p.url} alt={`Thumb ${idx + 1}`} className="w-full h-full object-cover" />
                        <span className="absolute bottom-0 inset-x-0 bg-black/70 text-[9px] text-white text-center font-mono py-0.5">
                          {idx + 1}
                        </span>
                      </button>
                    ))}
                  </div>

                  {/* Zoom Controls */}
                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => setZoomLevel((z) => Math.max(0.6, z - 0.2))}
                      className="p-1.5 rounded-lg border border-border bg-surface-hover hover:bg-surface text-muted-foreground hover:text-foreground transition-colors"
                      title="Zoom Out"
                    >
                      <ZoomOut className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => setZoomLevel(1)}
                      className="px-2 py-1 rounded-lg border border-border bg-surface-hover hover:bg-surface text-[11px] font-mono text-muted-foreground hover:text-foreground transition-colors"
                      title="Reset Zoom"
                    >
                      {Math.round(zoomLevel * 100)}%
                    </button>
                    <button
                      onClick={() => setZoomLevel((z) => Math.min(2.5, z + 0.2))}
                      className="p-1.5 rounded-lg border border-border bg-surface-hover hover:bg-surface text-muted-foreground hover:text-foreground transition-colors"
                      title="Zoom In"
                    >
                      <ZoomIn className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              )}
            </div>

            {/* Right: GLM-OCR Intelligence Drawer */}
            <div className="w-80 md:w-96 border-l border-border bg-card flex flex-col shrink-0">
              {/* Drawer Header */}
              <div className="px-4 py-3 border-b border-border flex items-center justify-between bg-surface/40">
                <div className="flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-primary" />
                  <span className="text-xs font-bold uppercase tracking-wider text-foreground">
                    GLM-OCR Intelligence
                  </span>
                </div>
                <button
                  onClick={() => setShowPromptInput(!showPromptInput)}
                  className="text-[11px] text-primary hover:underline font-semibold flex items-center gap-1"
                >
                  <RotateCcw className="w-3 h-3" />
                  Re-scan
                </button>
              </div>

              {/* Custom Prompt Bar */}
              {showPromptInput && (
                <div className="p-3 border-b border-border bg-surface/30 flex flex-col gap-2 animate-in slide-in-from-top-2">
                  <div className="text-[11px] font-semibold text-muted-foreground">
                    Custom Prompt for Page {currentPageIndex + 1}:
                  </div>
                  <div className="flex items-center gap-1.5">
                    <input
                      type="text"
                      placeholder="e.g. Extract tables as Markdown, equations as LaTeX..."
                      value={customPrompt}
                      onChange={(e) => setCustomPrompt(e.target.value)}
                      onKeyDown={(e) => e.key === 'Enter' && handleReRunPageOcr()}
                      className="flex-1 px-2.5 py-1.5 text-xs bg-surface-hover border border-border rounded-lg outline-none focus:ring-1 focus:ring-primary"
                    />
                    <button
                      onClick={handleReRunPageOcr}
                      disabled={isReRunningOcr}
                      className="p-1.5 rounded-lg bg-primary text-primary-foreground hover:opacity-90 disabled:opacity-50 transition-opacity"
                    >
                      {isReRunningOcr ? (
                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      ) : (
                        <Send className="w-3.5 h-3.5" />
                      )}
                    </button>
                  </div>
                </div>
              )}

              {/* Extracted Text Content */}
              <div className="flex-1 p-4 overflow-y-auto font-mono text-xs text-foreground/90 whitespace-pre-wrap leading-relaxed select-text bg-surface/20">
                {isExtractingAllPages ? (
                  <div className="h-full flex flex-col items-center justify-center gap-3 text-muted-foreground">
                    <Loader2 className="w-6 h-6 animate-spin text-primary" />
                    <p className="text-xs">Extracting text across all pages with GLM-OCR...</p>
                  </div>
                ) : isReRunningOcr ? (
                  <div className="h-full flex flex-col items-center justify-center gap-3 text-muted-foreground">
                    <Loader2 className="w-6 h-6 animate-spin text-primary" />
                    <p className="text-xs">Processing Page {currentPageIndex + 1} with GLM-OCR...</p>
                  </div>
                ) : currentPageOcr ? (
                  currentPageOcr
                ) : (
                  <div className="h-full flex flex-col items-center justify-center text-center p-4 gap-3 text-muted-foreground">
                    <Sparkles className="w-8 h-8 text-primary opacity-80" />
                    <div>
                      <p className="text-xs font-semibold text-foreground">No OCR text extracted yet</p>
                      <p className="text-[11px] text-muted-foreground mt-0.5">Extract text with local Ollama GLM-OCR model</p>
                    </div>
                    <div className="flex flex-col gap-2 w-full max-w-xs mt-1">
                      <button
                        onClick={handleReRunPageOcr}
                        disabled={isExtractingAllPages || isReRunningOcr}
                        className="flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 text-xs font-semibold cursor-pointer transition-all shadow-xs disabled:opacity-50"
                      >
                        <Sparkles className="w-3.5 h-3.5" />
                        <span>Extract Page {currentPageIndex + 1} (GLM-OCR)</span>
                      </button>
                      {totalPages > 1 && (
                        <button
                          onClick={handleExtractAllPages}
                          disabled={isExtractingAllPages || isReRunningOcr}
                          className="flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-lg border border-border bg-surface-hover hover:bg-surface text-xs font-medium text-foreground cursor-pointer transition-colors"
                        >
                          <span>Extract All {totalPages} Pages</span>
                        </button>
                      )}
                    </div>
                  </div>
                )}
              </div>

              {/* Drawer Footer Actions */}
              <div className="p-3 border-t border-border bg-surface/40 flex items-center justify-between gap-2">
                <button
                  onClick={handleCopyOcr}
                  disabled={!currentPageOcr}
                  className="flex-1 flex items-center justify-center gap-1.5 py-2 px-3 rounded-lg border border-border bg-surface-hover hover:bg-surface text-xs font-semibold text-foreground disabled:opacity-40 transition-colors"
                >
                  {copiedText ? (
                    <>
                      <Check className="w-3.5 h-3.5 text-emerald-500" />
                      <span>Copied!</span>
                    </>
                  ) : (
                    <>
                      <Copy className="w-3.5 h-3.5 text-muted-foreground" />
                      <span>Copy Page Text</span>
                    </>
                  )}
                </button>

                <button
                  onClick={handleInsertPageToNote}
                  disabled={!activeNote || !currentPageOcr}
                  className="flex-1 flex items-center justify-center gap-1.5 py-2 px-3 rounded-lg bg-primary text-primary-foreground hover:opacity-90 text-xs font-semibold disabled:opacity-40 transition-opacity"
                >
                  {insertedToNote ? (
                    <>
                      <Check className="w-3.5 h-3.5" />
                      <span>Appended!</span>
                    </>
                  ) : (
                    <>
                      <FileText className="w-3.5 h-3.5" />
                      <span>Append Page {currentPageIndex + 1}</span>
                    </>
                  )}
                </button>
              </div>

            </div>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
};
