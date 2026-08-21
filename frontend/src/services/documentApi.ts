const API_BASE = '/api';

export interface DocumentPage {
  page_number: number;
  media_id: string;
  filename: string;
  image_url: string;
  file_size?: number;
  ocr_status: 'completed' | 'failed' | 'skipped' | 'pending';
  ocr_text: string;
}

export interface DocumentMetadata {
  id: string;
  filename: string;
  original_filename: string;
  url: string;
  download_url: string;
  thumbnail_url: string;
  page_count: number;
  file_size: number;
  ocr_status: string;
  ocr_text: string;
}

export interface DocumentUploadResponse {
  status: string;
  document: DocumentMetadata;
  pages: DocumentPage[];
  markdown_insertion: string;
}

export interface DocumentDetailsResponse {
  status: string;
  document: DocumentMetadata;
  total_pages: number;
  pages: {
    id: string;
    filename: string;
    url: string;
    ocr_text: string;
    ocr_status: string;
  }[];
}

export const documentApi = {
  async uploadPdf(
    file: File | Blob,
    filename?: string,
    memoryId?: string,
    runOcr: boolean = true,
    customPrompt?: string,
    maxPages: number = 50,
    signal?: AbortSignal
  ): Promise<DocumentUploadResponse> {
    const formData = new FormData();
    const finalName = filename || (file instanceof File ? file.name : 'document.pdf');
    formData.append('file', file, finalName);
    formData.append('filename', finalName);
    if (memoryId) formData.append('memory_id', memoryId);
    formData.append('run_ocr', String(runOcr));
    if (customPrompt) formData.append('custom_prompt', customPrompt);
    formData.append('max_pages', String(maxPages));

    const res = await fetch(`${API_BASE}/documents/upload-pdf`, {
      method: 'POST',
      body: formData,
      signal,
    });


    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `PDF upload failed: ${res.statusText}`);
    }

    return res.json();
  },

  async getDocumentDetails(identifier: string): Promise<DocumentDetailsResponse> {
    const res = await fetch(`${API_BASE}/documents/item/${encodeURIComponent(identifier)}`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Fetch document failed: ${res.statusText}`);
    }
    return res.json();
  },

  async reprocessPageOcr(
    pageIdentifier: string,
    customPrompt?: string
  ): Promise<{ status: string; media_id: string; filename: string; ocr_status: string; ocr_text: string }> {
    const res = await fetch(`${API_BASE}/documents/re-ocr-page`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        page_identifier: pageIdentifier,
        custom_prompt: customPrompt || null,
      }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Page OCR re-scan failed: ${res.statusText}`);
    }

    return res.json();
  },

  async triggerDocumentOcr(
    docIdentifier: string,
    customPrompt?: string
  ): Promise<{
    status: string;
    document: DocumentMetadata;
    total_pages: number;
    ocr_text: string;
    pages: { id: string; filename: string; url: string; ocr_text: string; ocr_status: string }[];
  }> {
    const res = await fetch(`${API_BASE}/documents/trigger-ocr`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        doc_identifier: docIdentifier,
        custom_prompt: customPrompt || null,
      }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Document OCR extraction failed: ${res.statusText}`);
    }

    return res.json();
  },


  async getOrphans(): Promise<{ status: string; total_orphans: number; total_bytes: number; orphans: any[] }> {
    const res = await fetch(`${API_BASE}/media/orphans`);
    if (!res.ok) throw new Error(`Fetch orphans failed: ${res.statusText}`);
    return res.json();
  },

  async cleanupOrphans(): Promise<{ status: string; deleted_count: number; freed_bytes: number; orphans_removed: string[] }> {
    const res = await fetch(`${API_BASE}/media/cleanup-orphans`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error(`Orphan cleanup failed: ${res.statusText}`);
    return res.json();
  },
};
