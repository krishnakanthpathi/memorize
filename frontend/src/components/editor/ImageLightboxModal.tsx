import React, { useEffect, useState } from 'react';
import {
  X,
  Copy,
  Check,
  RotateCcw,
  Sparkles,
  Download,
  ExternalLink,
  ZoomIn,
  ZoomOut,
  Maximize2,
  FileText,
  Loader2,
  Info,
} from 'lucide-react';
import { useNotesStore } from '@/store/useNotesStore';
import { api } from '@/services/api';
import { cn } from '@/lib/utils';

const getMediaIdentifier = (img?: { url?: string; filename?: string; mediaId?: string } | null): string => {
  if (!img) return '';
  if (img.mediaId) return img.mediaId;
  if (img.url) {
    const match = img.url.match(/\/api\/media\/([^\/?#]+)/);
    if (match && match[1]) return decodeURIComponent(match[1]);
    const parts = img.url.split('?')[0].split('/');
    const last = parts[parts.length - 1];
    if (last && !last.startsWith('data:')) return decodeURIComponent(last);
  }
  return img.filename || '';
};

export const ImageLightboxModal: React.FC = () => {
  const {
    activeLightboxImage,
    setActiveLightboxImage,
    notes,
    activeNoteId,
    updateActiveNote,
    startTask,
    completeTask,
    failTask,
  } = useNotesStore();
  const activeNote = notes.find((n) => n.id === activeNoteId);

  const [ocrText, setOcrText] = useState<string>('');
  const [isOcrRunning, setIsOcrRunning] = useState<boolean>(false);
  const [isCopied, setIsCopied] = useState<boolean>(false);
  const [insertedToNote, setInsertedToNote] = useState<boolean>(false);
  const [zoom, setZoom] = useState<number>(1);
  const [activeTab, setActiveTab] = useState<'preview' | 'ocr'>('preview');
  const [mediaDetails, setMediaDetails] = useState<any>(null);


  useEffect(() => {
    if (!activeLightboxImage) return;
    setOcrText(activeLightboxImage.ocrText || '');
    setMediaDetails(null);
    setZoom(1);

    const identifier = getMediaIdentifier(activeLightboxImage);
    if (identifier) {
      api
        .getMediaItem(identifier)
        .then((res) => {
          if (res && res.media) {
            setMediaDetails(res.media);
            if (res.media.ocr_text && !activeLightboxImage.ocrText) {
              setOcrText(res.media.ocr_text);
            }
          }
        })
        .catch((err) => {
          console.warn('Could not fetch media item details:', err);
        });
    }

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setActiveLightboxImage(null);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [activeLightboxImage, setActiveLightboxImage]);

  if (!activeLightboxImage) return null;

  const handleCopyOcr = () => {
    if (!ocrText) return;
    navigator.clipboard.writeText(ocrText);
    setIsCopied(true);
    setTimeout(() => setIsCopied(false), 2000);
  };

  const handleRerunOcr = async () => {
    const identifier = getMediaIdentifier(activeLightboxImage) || mediaDetails?.id;
    if (!identifier) return;

    const fileNameStr = activeLightboxImage.filename || 'image';
    const taskId = startTask('GLM-OCR Vision Extraction', `Re-scanning "${fileNameStr}" with local Ollama GLM-OCR model...`);
    setIsOcrRunning(true);
    try {
      const res = await api.triggerMediaOcr(identifier);
      if (res && res.ocr_text) {
        setOcrText(res.ocr_text);
        setMediaDetails((prev: any) => ({
          ...prev,
          ocr_text: res.ocr_text,
          ocr_status: 'completed',
        }));
        completeTask(
          taskId,
          `Extracted ${res.ocr_text.length.toLocaleString()} characters from "${fileNameStr}"`,
          true,
          'GLM-OCR Complete'
        );
      } else {
        completeTask(taskId, `Processed "${fileNameStr}" with GLM-OCR`, true, 'GLM-OCR Complete');
      }
    } catch (err: any) {
      console.error('Failed to rerun OCR:', err);
      failTask(taskId, err?.message || 'GLM-OCR re-run failed');
    } finally {
      setIsOcrRunning(false);
    }
  };


  const formatFileSize = (bytes?: number) => {
    if (!bytes) return 'Original';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/85 backdrop-blur-md animate-in fade-in duration-200">
      {/* Modal Container */}
      <div className="relative flex flex-col w-[94vw] h-[90vh] max-w-6xl rounded-2xl bg-zinc-900 border border-zinc-800 shadow-2xl overflow-hidden">
        {/* Header Bar */}
        <div className="flex items-center justify-between px-5 py-3 border-b border-zinc-800 bg-zinc-900/90 select-none">
          <div className="flex items-center space-x-3 truncate">
            <div className="p-1.5 rounded-lg bg-zinc-800 text-zinc-100 border border-zinc-700">
              <Maximize2 className="w-4 h-4" />
            </div>
            <div className="truncate">
              <h3 className="text-sm font-semibold text-zinc-100 truncate">
                {activeLightboxImage.filename || 'Image Inspection'}
              </h3>
              <p className="text-xs text-zinc-400">
                Original Uncompressed • {formatFileSize(mediaDetails?.file_size)} • {mediaDetails?.mime_type || 'image'}
              </p>
            </div>
          </div>

          {/* Actions & Close */}
          <div className="flex items-center space-x-2">
            <div className="flex items-center bg-zinc-800/80 rounded-lg p-0.5 border border-zinc-700/50">
              <button
                onClick={() => setZoom((z) => Math.max(0.5, z - 0.25))}
                className="p-1.5 text-zinc-400 hover:text-zinc-200 rounded hover:bg-zinc-700 transition"
                title="Zoom Out"
              >
                <ZoomOut className="w-3.5 h-3.5" />
              </button>
              <span className="px-2 text-xs font-mono text-zinc-300 min-w-[3rem] text-center">
                {Math.round(zoom * 100)}%
              </span>
              <button
                onClick={() => setZoom((z) => Math.min(3, z + 0.25))}
                className="p-1.5 text-zinc-400 hover:text-zinc-200 rounded hover:bg-zinc-700 transition"
                title="Zoom In"
              >
                <ZoomIn className="w-3.5 h-3.5" />
              </button>
              <button
                onClick={() => setZoom(1)}
                className="p-1.5 text-zinc-400 hover:text-zinc-200 rounded hover:bg-zinc-700 transition"
                title="Reset Zoom"
              >
                <RotateCcw className="w-3.5 h-3.5" />
              </button>
            </div>

            <a
              href={activeLightboxImage.url}
              download={activeLightboxImage.filename}
              className="p-2 text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800 rounded-lg transition"
              title="Download Original File"
            >
              <Download className="w-4 h-4" />
            </a>

            <button
              onClick={() => setActiveLightboxImage(null)}
              className="p-2 text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800 rounded-lg transition ml-2"
              title="Close (Esc)"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Content Body: Split View (Image on Left, OCR on Right) */}
        <div className="flex-1 flex overflow-hidden">
          {/* Left Canvas: Uncompressed Image Viewer */}
          <div className="flex-1 relative flex items-center justify-center p-6 bg-zinc-950/80 overflow-auto select-none">
            <div
              className="transition-transform duration-150 ease-out flex items-center justify-center"
              style={{ transform: `scale(${zoom})` }}
            >
              <img
                src={activeLightboxImage.url}
                alt={activeLightboxImage.filename}
                className="max-h-[72vh] max-w-full rounded-lg shadow-xl object-contain border border-zinc-800/80 pointer-events-auto"
              />
            </div>
          </div>

          {/* Right Drawer: Local Ollama GLM-OCR Text & Intelligence */}
          <div className="w-96 border-l border-zinc-800 bg-zinc-900/60 flex flex-col">
            <div className="flex items-center justify-between px-4 py-3 border-b border-zinc-800 bg-zinc-900/80">
              <div className="flex items-center space-x-2">
                <Sparkles className="w-4 h-4 text-zinc-100" />
                <span className="text-xs font-semibold uppercase tracking-wider text-zinc-300">
                  Local Ollama GLM-OCR
                </span>
              </div>
              <button
                onClick={handleRerunOcr}
                disabled={isOcrRunning}
                className="flex items-center space-x-1.5 px-2.5 py-1 text-xs font-medium bg-zinc-800 text-zinc-100 hover:bg-zinc-700 border border-zinc-700 rounded-md transition disabled:opacity-50 cursor-pointer"
                title="Re-run local Ollama GLM-OCR model"
              >
                {isOcrRunning ? (
                  <>
                    <Loader2 className="w-3 h-3 animate-spin" />
                    <span>Extracting...</span>
                  </>
                ) : (
                  <>
                    <RotateCcw className="w-3 h-3" />
                    <span>Re-run OCR</span>
                  </>
                )}
              </button>
            </div>

            {/* OCR Text Area */}
            <div className="flex-1 p-4 overflow-y-auto font-sans text-xs text-zinc-300 leading-relaxed whitespace-pre-wrap selection:bg-zinc-700">
              {ocrText ? (
                <div className="space-y-3">
                  <div className="p-3 bg-zinc-950/60 rounded-lg border border-zinc-800/80 font-mono text-[11px] leading-relaxed text-zinc-200">
                    {ocrText}
                  </div>
                </div>
              ) : isOcrRunning ? (
                <div className="flex flex-col items-center justify-center h-full text-center space-y-3 text-zinc-400">
                  <Loader2 className="w-6 h-6 animate-spin text-zinc-100" />
                  <p className="text-xs">Processing visual tokens with local Ollama GLM-OCR...</p>
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center h-full text-center p-4 space-y-3 text-zinc-400">
                  <Sparkles className="w-8 h-8 text-zinc-300 opacity-80" />
                  <div>
                    <p className="text-xs font-semibold text-zinc-200">No OCR text extracted yet</p>
                    <p className="text-[11px] text-zinc-400 mt-0.5">Extract text with local Ollama GLM-OCR model</p>
                  </div>
                  <button
                    onClick={handleRerunOcr}
                    disabled={isOcrRunning}
                    className="flex items-center space-x-1.5 px-3 py-2 text-xs font-semibold bg-zinc-100 text-zinc-900 hover:bg-white rounded-lg transition disabled:opacity-50 cursor-pointer shadow-sm"
                  >
                    <Sparkles className="w-3.5 h-3.5" />
                    <span>Extract Text (GLM-OCR)</span>
                  </button>
                </div>
              )}
            </div>

            {/* Bottom Actions */}
            {ocrText && (
              <div className="p-3 border-t border-zinc-800 bg-zinc-900/90 flex items-center justify-between gap-2">
                <button
                  onClick={handleCopyOcr}
                  className="flex-1 flex items-center justify-center space-x-1.5 px-3 py-1.5 text-xs font-medium bg-zinc-800 hover:bg-zinc-700 text-zinc-200 rounded-lg border border-zinc-700 transition cursor-pointer"
                >
                  {isCopied ? (
                    <>
                      <Check className="w-3.5 h-3.5 text-zinc-100" />
                      <span className="text-zinc-100">Copied</span>
                    </>
                  ) : (
                    <>
                      <Copy className="w-3.5 h-3.5" />
                      <span>Copy Text</span>
                    </>
                  )}
                </button>

                <button
                  onClick={() => {
                    if (!activeNote || !ocrText) return;
                    const block = `\n\n## Extracted Image Content (${activeLightboxImage.filename || 'Image'})\n${ocrText.trim()}\n`;
                    updateActiveNote({ content: (activeNote.content || '') + block });
                    setInsertedToNote(true);
                    setTimeout(() => setInsertedToNote(false), 2000);
                  }}
                  disabled={!activeNote}
                  className="flex-1 flex items-center justify-center space-x-1.5 px-3 py-1.5 text-xs font-medium bg-zinc-100 hover:bg-white text-zinc-900 rounded-lg transition cursor-pointer font-semibold"
                >
                  {insertedToNote ? (
                    <>
                      <Check className="w-3.5 h-3.5" />
                      <span>Appended!</span>
                    </>
                  ) : (
                    <>
                      <FileText className="w-3.5 h-3.5" />
                      <span>Append to Note</span>
                    </>
                  )}
                </button>
              </div>
            )}

          </div>
        </div>
      </div>
    </div>

  );
};
