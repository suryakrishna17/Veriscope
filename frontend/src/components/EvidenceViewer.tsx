import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { BBox, DocumentInfo } from "../api/types";
import { DOC_LABEL } from "../lib/format";
import { errorText } from "../lib/hooks";
import { Spinner, TrustBadge } from "./Badges";
import { IconFileText } from "./Icons";

export interface Highlight {
  documentId: string;
  page: number;
  boxes: BBox[];
  label: string;
  tone: "field" | "high" | "medium" | "low" | "info";
}

interface Props {
  documents: DocumentInfo[];
  activeDocId: string | null;
  page: number;
  highlight: Highlight | null;
  onNavigate: (docId: string, page: number) => void;
}

const cache = new Map<string, string>();

function usePageImage(docId: string | null, page: number) {
  const [url, setUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!docId) return;
    const key = `${docId}:${page}`;
    setError(null);
    if (cache.has(key)) {
      setUrl(cache.get(key)!);
      return;
    }
    setUrl(null);
    let live = true;
    api.pageImage(docId, page)
      .then((blob) => {
        const u = URL.createObjectURL(blob);
        cache.set(key, u);
        if (live) setUrl(u);
      })
      .catch((e) => live && setError(errorText(e)));
    return () => {
      live = false;
    };
  }, [docId, page]);

  return { url, error };
}

export function EvidenceViewer({ documents, activeDocId, page, highlight, onNavigate }: Props) {
  const doc = documents.find((d) => d.id === activeDocId) ?? documents[0] ?? null;
  const pageCount = Math.max(1, doc?.page_count ?? 1);
  const { url, error } = usePageImage(
    doc?.processing_status === "failed" && !doc.page_count ? null : doc?.id ?? null,
    page
  );
  const [zoom, setZoom] = useState(1);
  const boxes = highlight && doc && highlight.documentId === doc.id && highlight.page === page ? highlight.boxes : [];
  const pageInfo = doc?.pages.find((p) => p.page_number === page);

  if (!doc) return <div className="viewer viewer-empty">No documents uploaded yet.</div>;

  return (
    <section className="viewer" aria-label="Document evidence viewer">
      <div className="doc-tabs" role="tablist" aria-label="Document selection">
        {documents.map((d) => (
          <button
            key={d.id}
            role="tab"
            aria-selected={d.id === doc.id}
            className="doc-tab"
            onClick={() => onNavigate(d.id, 1)}
          >
            <span className="doc-tab-name" style={{ display: "flex", alignItems: "center", gap: "0.35rem" }}>
              <IconFileText width="14" height="14" />
              {DOC_LABEL[d.doc_type]}
            </span>
            <span className="doc-tab-file">{d.original_name}</span>
          </button>
        ))}
      </div>

      <div className="viewer-meta">
        <TrustBadge label={doc.trust_label} simulated={doc.issuer_check?.simulated} />

        {pageInfo?.text_source === "ocr" && (
          <span className="pill pill-warn" title="Text on this page was extracted from an image via OCR">
            OCR scan · {Math.round(pageInfo.mean_confidence ?? 0)}% confidence
          </span>
        )}

        <span className="hash" title={`SHA-256 Digest: ${doc.sha256}`}>
          sha256: {doc.sha256.slice(0, 10)}…
        </span>

        <span className="viewer-tools">
          <button
            className="icon-btn"
            onClick={() => setZoom((z) => Math.max(0.6, +(z - 0.2).toFixed(1)))}
            aria-label="Zoom out"
            title="Zoom out"
          >
            −
          </button>
          <span className="zoom">{Math.round(zoom * 100)}%</span>
          <button
            className="icon-btn"
            onClick={() => setZoom((z) => Math.min(2.4, +(z + 0.2).toFixed(1)))}
            aria-label="Zoom in"
            title="Zoom in"
          >
            +
          </button>
          <button
            className="btn btn-small btn-ghost"
            style={{ fontSize: "0.72rem", padding: "0.15rem 0.4rem" }}
            onClick={() => setZoom(1)}
            title="Reset zoom to 100%"
          >
            Reset
          </button>
        </span>
      </div>

      {doc.processing_status === "failed" && (
        <p className="inline-error" style={{ margin: "0.5rem 1rem" }}>{doc.processing_error}</p>
      )}

      <div className="page-scroll">
        <div className="page" style={{ width: `${zoom * 100}%` }}>
          {error && <p className="inline-error">{error}</p>}
          {!url && !error && (
            <div className="page-loading">
              <Spinner label="Rendering document page" />
            </div>
          )}
          {url && <img src={url} alt={`${DOC_LABEL[doc.doc_type]}, page ${page}`} draggable={false} />}
          {url &&
            boxes.map((b, i) => (
              <span
                key={`${highlight?.label}-${i}`}
                className={`hl hl-${highlight?.tone}`}
                style={{
                  left: `${b[0] * 100}%`,
                  top: `${b[1] * 100}%`,
                  width: `${(b[2] - b[0]) * 100}%`,
                  height: `${(b[3] - b[1]) * 100}%`,
                }}
                aria-hidden
              />
            ))}
        </div>
      </div>

      <div className="viewer-foot">
        {highlight && highlight.documentId === doc.id ? (
          <span className="hl-caption">Source: {highlight.label}</span>
        ) : (
          <span className="muted">Click any extracted field or finding to highlight its source location.</span>
        )}

        <span className="pager">
          <button
            className="icon-btn"
            disabled={page <= 1}
            onClick={() => onNavigate(doc.id, page - 1)}
            aria-label="Previous page"
          >
            ‹
          </button>
          <span>Page {page} of {pageCount}</span>
          <button
            className="icon-btn"
            disabled={page >= pageCount}
            onClick={() => onNavigate(doc.id, page + 1)}
            aria-label="Next page"
          >
            ›
          </button>
        </span>
      </div>
    </section>
  );
}
