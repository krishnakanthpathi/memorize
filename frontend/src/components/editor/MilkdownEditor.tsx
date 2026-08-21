import React, { useRef } from 'react';
import { defaultValueCtx, Editor, rootCtx, editorViewOptionsCtx } from '@milkdown/core';
import { Milkdown, MilkdownProvider, useEditor } from '@milkdown/react';
import { commonmark } from '@milkdown/preset-commonmark';
import { gfm } from '@milkdown/preset-gfm';
import { listener, listenerCtx } from '@milkdown/plugin-listener';
import { history } from '@milkdown/plugin-history';
import { clipboard } from '@milkdown/plugin-clipboard';
import { prism, prismConfig } from '@milkdown/plugin-prism';
import { math, katexOptionsCtx } from '@milkdown/plugin-math';
import { refractor } from 'refractor/all';
import 'katex/dist/katex.min.css';
import { normalizeMarkdownMath } from '@/lib/renderMath';
import { useNotesStore } from '@/store/useNotesStore';


interface MilkdownEditorProps {
  noteId: string;
  initialContent: string;
  readOnly?: boolean;
  onChange: (markdown: string) => void;
}

const EditorInner: React.FC<MilkdownEditorProps> = ({
  initialContent,
  readOnly = false,
  onChange,
}) => {
  const onChangeRef = useRef(onChange);
  onChangeRef.current = onChange;

  const { get } = useEditor((root) => {
    const cleanContent = normalizeMarkdownMath(initialContent || '');
    return Editor.make()
      .config((ctx) => {
        ctx.set(rootCtx, root);
        ctx.set(defaultValueCtx, cleanContent);
        if (readOnly) {
          ctx.set(editorViewOptionsCtx, { editable: () => false });
        }
        ctx.set(prismConfig.key, {
          configureRefractor: () => refractor,
        });
        ctx.set(katexOptionsCtx.key, {
          throwOnError: false,
          errorColor: '#ef4444',
          strict: false,
          trust: true,
        });
        const listenerPlugin = ctx.get(listenerCtx);
        listenerPlugin.markdownUpdated((_, markdown) => {
          if (!readOnly) {
            onChangeRef.current(markdown);
          }
        });
      })
      .use(commonmark)
      .use(gfm)
      .use(prism)
      .use(math)
      .use(history)
      .use(clipboard)
      .use(listener);
  });

  const handleImageClick = (e: React.MouseEvent) => {
    const target = e.target as HTMLElement;
    if (target && target.tagName === 'IMG') {
      const img = target as HTMLImageElement;
      const src = img.getAttribute('src');
      if (src) {
        useNotesStore.getState().setActiveLightboxImage({
          url: src,
          filename: img.getAttribute('alt') || 'image.png',
        });
      }
    }
  };

  return (
    <div
      onClick={handleImageClick}
      className="milkdown-wrapper w-full h-full min-h-[400px]"
    >
      <Milkdown />
    </div>
  );
};


export const MilkdownEditor: React.FC<MilkdownEditorProps> = ({
  noteId,
  initialContent,
  readOnly = false,
  onChange,
}) => {
  return (
    <MilkdownProvider key={noteId}>
      <EditorInner
        noteId={noteId}
        initialContent={initialContent}
        readOnly={readOnly}
        onChange={onChange}
      />
    </MilkdownProvider>
  );
};
